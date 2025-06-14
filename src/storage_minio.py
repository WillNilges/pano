import logging
import os
import uuid
from pathlib import PurePosixPath

from minio import Minio
from wand.image import Image as WandImage

from models.image import Image
from settings import GARAGE_BUCKET, GARAGE_SECURE, GARAGE_URL, WORKING_DIRECTORY
from storage import Storage

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano.storage_minio")


class StorageMinio(Storage):
    def __init__(self, bucket: str = GARAGE_BUCKET) -> None:
        log.info("Configuring Minio Storage...")
        # Get env vars like this so that we crash if they're missing
        garage_url = GARAGE_URL
        garage_api_key = os.environ["GARAGE_API_KEY"]
        garage_secret = os.environ["GARAGE_SECRET"]
        log.info("Loaded credentials.")

        self.bucket = bucket
        minio_secure = GARAGE_SECURE
        log.info(f"URL: {garage_url}, bucket: {bucket}, secure: {minio_secure}")

        self.client = Minio(
            garage_url,
            access_key=garage_api_key,
            secret_key=garage_secret,
            secure=minio_secure,
            region="garage",
        )

        # Sanity check
        log.info(f"I see these buckets: {self.client.list_buckets()}")

        # Make the bucket if it doesn't exist.
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            log.info(f"Created bucket {self.bucket}")
        else:
            log.info(f"Bucket {self.bucket} already exists")

        log.info("Ready.")

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
