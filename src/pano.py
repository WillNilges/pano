import dataclasses
import logging
import os
from pathlib import PurePosixPath
import re
from typing import Optional
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db import PanoDB
from meshdb_client import MeshdbClient
from models.base import Base
from models.image import Image, ImageCategory
from storage import Storage
from storage_minio import StorageMinio


class Pano:
    def __init__(
        self,
        meshdb: MeshdbClient = MeshdbClient(),
        storage: Storage = StorageMinio(),
        db: PanoDB = PanoDB(),
    ) -> None:
        self.meshdb: MeshdbClient = meshdb
        self.storage: Storage = storage
        self.db: PanoDB = db

    def get_all_images(
        self, category: ImageCategory | None = None
    ) -> dict[int, list[dict]]:
        serialized_images = {}
        for image in self.db.get_images():
            if not serialized_images.get(image.install_number):
                serialized_images[image.install_number] = []

            i = dataclasses.asdict(image)
            i["url"] = image.get_object_url()
            serialized_images[image.install_number].append(i)
        return serialized_images

    def get_images(
        self, install_number: int, category: ImageCategory | None = None
    ) -> list[dict]:
        images = self.db.get_images(install_number=install_number, category=category)
        serialized_images = []
        for image in images:
            i = dataclasses.asdict(image)
            i["url"] = image.get_object_url()
            serialized_images.append(i)

        return serialized_images

    # TODO: How to update order?
    def update_image(
        self,
        id: uuid.UUID,
        new_install_number: Optional[int],
        new_category: Optional[ImageCategory],
        file_path: Optional[str],
    ):
        """
        Allows us to update details about an image, or change the image itself.
        Requires a uuid to identify the image.
        Optional new_install_number
        Optional new_category
        Pass a new file path to update the image itself.
        """

        image = self.db.get_image(id)

        if not image:
            raise ValueError(f"[db] Could not find image with id {id}")

        # Sanity check that the image exists. This should never fail
        if not self.storage.object_exists(image.get_object_path()):
            raise ValueError(f"[storage] Could not find image object with id {id}")

        # Update details if necessary
        if new_install_number:
            image.install_number = new_install_number

        if new_category:
            image.category = new_category

        if file_path:
            image.original_filename = PurePosixPath(file_path).name 
            image.signature = image.get_image_signature(file_path)

            try:
                self.storage.upload_objects({image.get_object_path(): file_path})
            except Exception as e:
                logging.exception("Failed to upload object to S3.")
                raise e

        # If all of that worked, save the image.
        self.db.save_image(image)

        return image.dict_with_url()

    def handle_upload(
        self, install_number: int, file_path: str, bypass_dupe_protection: bool = False
    ) -> dict[str, str] | None:
        building = self.meshdb.get_primary_building_for_install(install_number)
        # TODO: Distinguish between the server erroring, and getting passed a
        # bad install #
        if not building:
            raise ValueError("Could not find a building associated with that Install #")

        # Create a DB object
        image_object = Image(
            path=file_path,
            install_number=install_number,
            category=ImageCategory.uncategorized,
        )

        # Check the images for possible duplicates.
        if not bypass_dupe_protection:
            possible_duplicates = self.detect_duplicates(install_number, image_object)
            if possible_duplicates:
                return possible_duplicates

        # Upload object to S3
        try:
            self.storage.upload_objects({image_object.get_object_path(): file_path})
        except Exception as e:
            logging.exception("Failed to upload object to S3.")
            raise e

        self.db.save_image(image_object)

    def detect_duplicates(
        self, install_number: int, uploaded_image: Image
    ) -> dict[str, str]:
        """
        Uses ImageMagick to check the hash of the files uploaded against photos
        that already exist under an install. If a photo matches, the path is returned
        in the list.
        """

        possible_duplicates = {}

        # Get any images we already uploaded for this install
        images = self.db.get_images(install_number)
        for i in images:
            if uploaded_image.signature in i.signature:
                possible_duplicates[i.original_filename] = i.get_object_url()
                logging.warning(
                    f"Got possible duplicate. Uploaded file '{uploaded_image.original_filename}' looks like existing file '{i.original_filename}' (Signature matches: {i.signature})"
                )

        return possible_duplicates
