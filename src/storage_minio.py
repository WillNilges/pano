import logging
import os
from pathlib import PurePosixPath
from minio import Minio

from settings import MINIO_BUCKET, MINIO_URL, WORKING_DIRECTORY
from storage import Storage

log = logging.getLogger("pano.storage_minio")


class StorageMinio(Storage):
    def __init__(self) -> None:
        log.info("Configuring Minio Storage...")
        # Get env vars like this so that we crash if they're missing
        minio_url = MINIO_URL
        minio_access_key = os.environ["MINIO_ACCESS_KEY"]
        minio_secret_key = os.environ["MINIO_SECRET_KEY"]
        self.bucket = MINIO_BUCKET
        minio_secure = False if os.environ["MINIO_SECURE"] == "False" else True

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

    def upload_images(self, images: dict[str, str]) -> None:
        for path, file in images.items():
            self.client.fput_object(
                self.bucket,
                path,
                file,
            )
            log.info(f"Uploaded {file} to {path} in {self.bucket}")

    def download_images(self, objects: list[str]) -> list[str]:
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

    def list_all_images(self, install_number: int) -> list[str]:
        objects = []

        prefix = f"{install_number}/"

        for o in self.client.list_objects(self.bucket, prefix=prefix):
            objects.append(o.object_name)

        return objects
