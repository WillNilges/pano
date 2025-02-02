import logging
import os
from pathlib import PurePosixPath
import uuid
from minio import Minio

from settings import MINIO_BUCKET, MINIO_SECURE, MINIO_URL, WORKING_DIRECTORY
from storage import Storage
from wand.image import Image as WandImage

log = logging.getLogger("pano.storage_minio")


class StorageMinio(Storage):
    def __init__(self) -> None:
        log.info("Configuring Minio Storage...")
        # Get env vars like this so that we crash if they're missing
        minio_url = MINIO_URL
        minio_access_key = os.environ["MINIO_ACCESS_KEY"]
        minio_secret_key = os.environ["MINIO_SECRET_KEY"]
        self.bucket = MINIO_BUCKET
        minio_secure = MINIO_SECURE

        # Create a client with the MinIO server playground, its access key
        # and secret key.
        self.client = Minio(
            minio_url,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure,
        )

        # Make the bucket if it doesn't exist.
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            log.info(f"Created bucket {self.bucket}")
        else:
            log.info(f"Bucket {self.bucket} already exists")

    def upload_objects(self, objects: dict[str, str]) -> None:
        for path, file in objects.items():
            self.client.fput_object(
                self.bucket,
                path,
                file,
            )
            log.info(f"Uploaded {file} to {path} in {self.bucket}")

    def download_objects(self, objects: list[str]) -> list[str]:
        images = []
        try:
            for object_name in objects:
                title = object_name.split("/")[-1]
                path = f"{WORKING_DIRECTORY}/minio/{title}"
                self.client.fget_object(self.bucket, object_name, path)
                images.append(path)
        except Exception:  # TODO: Better error handling?
            logging.exception("Could not download some images")
            return []

        return images

    def list_all_objects(self, install_number: int) -> list[str]:
        objects = []

        prefix = f"{install_number}/"

        for o in self.client.list_objects(self.bucket, prefix=prefix):
            objects.append(o.object_name)

        return objects

    @staticmethod
    def get_object_path(install_number: int, id: uuid.UUID) -> str:
        return f"{install_number}/{id}"

    # Uses ImageMagick to check the hash of the files uploaded against photos
    # that already exist under an install. If a photo matches, the path is returned
    # in the list.

    # This is probably going to be really expensive, so best to limit its use.
    # XXX (wdn): Perhaps we should somehow cache the signatures of our files?
    def check_for_duplicates(
        self, install_number: int, uploaded_files: list[str]
    ) -> dict[str, str]:
        # First, download any images that might exist for this install number
        existing_files = self.download_objects(
            self.list_all_objects(install_number)
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

                image_path = self.get_object_path(install_number, uuid.UUID(existing_file_signatures[img.signature]))

                # Get a link to the S3 object to share with the client
                url = self.client.presigned_get_object(
                    self.bucket, image_path
                )

                possible_duplicates[basename] = url

                logging.warning(
                    f"Got possible duplicate. Uploaded file {basename} looks like existing file {existing_file_signatures[img.signature]} (Signature matches: {sig})"
                )

        return possible_duplicates
