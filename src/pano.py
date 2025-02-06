import dataclasses
import logging
import os
from pathlib import PurePosixPath
import re
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

    def get_images(self, install_number: int) -> list[dict]:
        images = self.db.get_images(install_number=install_number)
        serialized_images = []
        for image in images:
            i = dataclasses.asdict(image)
            i["url"] = image.get_object_url()
            serialized_images.append(i)

        print(serialized_images)

        return serialized_images

    # Mocking some kind of upload portal with an array of strings
    def handle_upload(
        self, install_number: int, file_path: str, bypass_dupe_protection: bool = False
    ) -> dict[str, str] | None:
        building = self.meshdb.get_primary_building_for_install(install_number)
        # TODO: Distinguish between the server erroring, and getting passed a
        # bad install #
        if not building:
            raise ValueError("Could not find a building associated with that Install #")

        with Session(self.db.engine, expire_on_commit=False) as session:
            # Create a DB object
            image_object = Image(
                path=file_path,
                install_number=install_number,
                category=ImageCategory.uncategorized,
            )

            # Check the images for possible duplicates.
            if not bypass_dupe_protection:
                possible_duplicates = self.detect_duplicates(
                    install_number, image_object
                )
                if possible_duplicates:
                    return possible_duplicates

            # Upload object to S3
            try:
                self.storage.upload_objects({image_object.get_object_path(): file_path})
            except Exception as e:
                logging.exception("Failed to upload object to S3.")
                raise e

            # If successful, save image object to DB
            session.add(image_object)
            session.commit()

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
