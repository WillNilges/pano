import dataclasses
import logging
import uuid
from typing import Optional

from db import PanoDB
from meshdb_client import MeshdbClient
from models.image import Image
from storage_minio import StorageMinio
from werkzeug.exceptions import NotFound


class Pano:
    def __init__(
        self,
        meshdb: MeshdbClient = MeshdbClient(),
        storage: StorageMinio = StorageMinio(),
        db: PanoDB = PanoDB(),
    ) -> None:
        self.meshdb: MeshdbClient = meshdb
        self.storage: StorageMinio = storage
        self.db: PanoDB = db

    def get_all_images(
        self
    ) -> dict[int, list[dict]]:
        serialized_images = {}
        for image in self.db.get_images():
            if not serialized_images.get(image.install_id):
                serialized_images[image.install_id] = []

            i = dataclasses.asdict(image)
            i["url"] = self.storage.get_presigned_url(image)
            serialized_images[image.install_id].append(i)
        return serialized_images

    def get_images(
        self, install_number: int
    ) -> list[dict]:
        install = self.meshdb.get_install(install_number)
        if not install:
            raise NotFound("Could not resolve new install number. Is this a valid install?")

        images = self.db.get_images(install_id=uuid.UUID(install.id))
        serialized_images = []
        for image in images:
            i = dataclasses.asdict(image)
            i["url"] = self.storage.get_presigned_url(image)
            serialized_images.append(i)

        return serialized_images

    # TODO: How to update order?
    def update_image(
        self,
        id: uuid.UUID,
        new_install_number: Optional[int],
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
        if not self.storage.object_exists(image.object_path()):
            raise ValueError(f"[storage] Could not find image object with id {id}")

        # Update details if necessary
        if new_install_number:
            new_install = self.meshdb.get_install(new_install_number)
            if not new_install:
                raise NotFound("Could not resolve new install number. Is this a valid install?")
            image.install_id = uuid.UUID(new_install.id)

        if file_path:
            image.signature = image.get_image_signature(file_path)

            try:
                self.storage.upload_objects({image.object_path(): file_path})
            except Exception as e:
                logging.exception("Failed to upload object to S3.")
                raise e

        # If all of that worked, save the image.
        self.db.save_image(image)

        image_dict = dataclasses.asdict(image)
        image_dict["url"] = self.storage.get_presigned_url(image)

        return image_dict

    def handle_upload(
        self, install_id: uuid.UUID, file_path: str, bypass_dupe_protection: bool = False
    ) -> dict[str, str]:
        # Create a DB object
        image_object = Image(
            path=file_path,
            install_number=install_id,
        )

        # Check the images for possible duplicates.
        if not bypass_dupe_protection:
            possible_duplicates = self.detect_duplicates(install_id, image_object)
            if possible_duplicates:
                return possible_duplicates

        # Upload object to S3
        try:
            self.storage.upload_objects({image_object.object_path(): file_path})
        except Exception as e:
            logging.exception("Failed to upload object to S3.")
            raise e

        self.db.save_image(image_object)

        # Empty Dict = No Dupes; We're good.
        return {}

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
                possible_duplicates[
                    i.original_filename
                ] = self.storage.get_presigned_url(i)
                logging.warning(
                    f"Got possible duplicate. Uploaded file '{uploaded_image.original_filename}' looks like existing file '{i.original_filename}' (Signature matches: {i.signature})"
                )

        return possible_duplicates
