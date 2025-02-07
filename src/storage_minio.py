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
    def __init__(self, bucket: str = MINIO_BUCKET) -> None:
        log.info("Configuring Minio Storage...")
        # Get env vars like this so that we crash if they're missing
        minio_url = MINIO_URL
        minio_access_key = os.environ["MINIO_ACCESS_KEY"]
        minio_secret_key = os.environ["MINIO_SECRET_KEY"]
        self.bucket = bucket
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
