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
        # Firstly, check the images for possible duplicates.
        if not bypass_dupe_protection:
            possible_duplicates = self.storage.check_for_duplicates(
                install_number, [file_path]
            )
            if possible_duplicates:
                return possible_duplicates

        building = self.meshdb.get_primary_building_for_install(install_number)
        # TODO: Distinguish between the server erroring, and getting passed a bad install #
        if not building:
            raise ValueError("Could not find a building associated with that Install #")

        with Session(self.db.engine, expire_on_commit=False) as session:
            # Create a DB object
            image_object = Image(
                session=session,
                install_number=install_number,
                category=ImageCategory.panorama,
            )

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
