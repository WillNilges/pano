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


# TODO (wdn): I need to find a way to improve the abstraction of the database
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

    def get_images(self, install_number: int) -> list[dict]:
        images = self.db.get_images(install_number=install_number)
        serialized_images = []
        for img in images:
            i = dataclasses.asdict(img)
            i["url"] = img.url()
            serialized_images.append(i)

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
                session=session,
                path=file_path,
                install_number=install_number,
                category=ImageCategory.panorama,
            )

            # Check the images for possible duplicates.
            if not bypass_dupe_protection:
                possible_duplicates = self.storage.check_for_duplicates(
                    install_number, image_object.signature
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

            try:
                # Save link to object in MeshDB (best effort)
                url = image_object.url()
                logging.info(url)
                self.meshdb.save_panorama_on_building(building.id, url)
            except Exception as e:
                logging.exception("Could not save panorama to MeshDB.")
                raise e

    def check_for_duplicates(
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


        ###

        # Download any images that might exist for this install number
        existing_files = self.storage.download_objects(self.storage.list_all_objects(install_number))
        # If there are no existing files, we're done.
        if not existing_files:
            return {}

        

        # Else, we'll have to grab the signatures and compare them. Create a dictionary
        # of key: filename
        existing_file_signatures = {
            # Sanitze the paths to avoid betraying internals
            WandImage(filename=f).signature: PurePosixPath(f).name
            for f in existing_files
        }

        # Check if any of the images we received have a matching signature to an
        # existing image
        possible_duplicates = {}
        for f in uploaded_files:
            img = WandImage(filename=f)
            sig = img.signature
            if sig in existing_file_signatures:
                # Sanitze the paths to avoid betraying internals. This should
                # always be a UUID
                basename = PurePosixPath(f).name

                image_path = self.get_object_path(
                    install_number, uuid.UUID(existing_file_signatures[img.signature])
                )

                # Get a link to the S3 object to share with the client
                url = self.client.presigned_get_object(self.bucket, image_path)

                possible_duplicates[basename] = url

                logging.warning(
                    f"Got possible duplicate. Uploaded file {basename} looks like existing file {existing_file_signatures[img.signature]} (Signature matches: {sig})"
                )

        return possible_duplicates
