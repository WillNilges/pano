import logging
import os
import uuid
from pathlib import PurePosixPath

from minio import Minio
from wand.image import Image as WandImage

from models.image import Image
from settings import MINIO_BUCKET, MINIO_SECURE, MINIO_URL, WORKING_DIRECTORY
from storage import Storage

log = logging.getLogger("pano.storage_minio")


class StorageMinio(Storage):
    def __init__(self, bucket: str = MINIO_BUCKET) -> None:
        log.info("Configuring Minio Storage...")
        # Get env vars like this so that we crash if they're missing
        minio_url = MINIO_URL
        minio_access_key = os.environ["GARAGE_API_KEY"]
        minio_secret_key = os.environ["GARAGE_SECRET"]
        self.bucket = bucket
        minio_secure = MINIO_SECURE

        log.info(f"URL: {minio_url}, bucket: {bucket}, secure: {minio_secure}")

        self.client = Minio(
            minio_url,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure,
            region="garage"
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

    def object_exists(self, object: str) -> bool:
        result = self.client.stat_object(self.bucket, object)
        if result:
            return True
        return False

    def get_presigned_url(self, image: Image) -> str:
        return self.client.presigned_get_object(self.bucket, f"{image.id}")
