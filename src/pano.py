import logging
from pathlib import PurePosixPath
import re

from sqlalchemy.orm import Session

from db import PanoDB
from meshdb_client import MeshdbClient
from models.image import Image, ImageCategory
from settings import MINIO_BUCKET, MINIO_URL
from storage_minio import StorageMinio
from wand.image import WandImage


# I need to find a way to improve the abstraction of the database
class Pano:
    def __init__(self) -> None:
        self.meshdb = MeshdbClient()
        self.minio = StorageMinio()
        self.db = PanoDB()

    # Mocking some kind of upload portal with an array of strings
    def handle_upload(
        self, install_number: int, file_path: str, bypass_dupe_protection: bool = False
    ) -> dict[str, str] | None:
        # Firstly, check the images for possible duplicates.
        if not bypass_dupe_protection:
            possible_duplicates = self.check_for_duplicates(install_number, [file_path])
            if possible_duplicates:
                return possible_duplicates

        building = self.meshdb.get_primary_building_for_install(install_number)
        # TODO: Distinguish between the server erroring, and getting passed a bad install #
        if not building:
            raise ValueError("Could not find a building associated with that Install #")

        # Create a DB object
        image_object = Image(
            install_number=install_number, category=ImageCategory.panorama
        )

        # Upload object to S3
        self.minio.upload_images({image_object.s3_object_path(): file_path})

        # If successful, save image to db
        image_object = self.db.save_image(image_object)

        # Save link to object in MeshDB
        url = image_object.url()
        logging.info(url)
        self.meshdb.save_panorama_on_building(building.id, url)

    # Uses ImageMagick to check the hash of the files uploaded against photos
    # that already exist under an install. If a photo matches, the path is returned
    # in the list.

    # This is probably going to be really expensive, so best to limit its use.
    # XXX (wdn): Perhaps we should somehow cache the signatures of our files?
    def check_for_duplicates(
        self, install_number: int, uploaded_files: list[str]
    ) -> dict[str, str]:
        # First, download any images that might exist for this install number
        existing_files = self.minio.download_images(
            self.minio.list_all_images(install_number)
        )
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

                image = self.db.get_image(existing_file_signatures[img.signature])
                if not image:
                    raise FileNotFoundError(
                        f"Could not locate image in the database. {basename}"
                    )

                image_path = image.s3_object_path()

                # Get a link to the S3 object to share with the client
                url = self.minio.client.presigned_get_object(
                    self.minio.bucket, image_path
                )

                possible_duplicates[basename] = url

                logging.warning(
                    f"Got possible duplicate. Uploaded file {basename} looks like existing file {existing_file_signatures[img.signature]} (Signature matches: {sig})"
                )

        return possible_duplicates
