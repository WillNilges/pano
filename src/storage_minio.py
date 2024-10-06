import logging
import os
from pathlib import PurePosixPath
from minio import Minio

from settings import MINIO_BUCKET, MINIO_URL
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

    def download_images(self, images: list[str]) -> list[str]:
        images = []
        try:
            for file in images:
                title = file.split("/")[-1]
                path = f"{WORKING_DIRECTORY}/minio/{title}"
                self.client.fget_object(self.bucket, file, path)
                images.append(path)
        except Exception:  # TODO: Better error handling?
            logging.exception("Could not download some images")
            return []

        return images

    def list_all_images(self, install_number: int | None = None) -> list[str]:
        objects = []

        prefix = str(install_number) if install_number else None

        for o in self.client.list_objects(self.bucket, prefix=prefix):
            objects.append(o)

        return objects

    def get_next_lexicograph(self, install_number: int) -> str:
        objects = self.client.list_objects(self.bucket, prefix=str(install_number))

        # If there are no objects for this install number yet, then return an empty
        # string (is this valid? What if I just prepend the install number)
        if not objects:
            return ""

        # We can figure out what letter we want by checking the # of objects
        # 0 objects: no letter
        # 1 object: a
        # 2 objects: b
        # 3 objexts: c
        # and so on

        # Count the number of objects
        number_of_objects = 0
        for _ in objects:
            number_of_objects += 1

        return self.int_to_lexicograph(number_of_objects)

    # Given a number, returns a lexicographical representation of that number
    # Example:
    # 0  -> 
    # 1  -> a
    # 26 -> z
    # 27 -> aa
    # Thanks chatgpt
    @staticmethod
    def int_to_lexicograph(n):
        result = []
        while n > 0:
            n -= 1  # Adjust because Excel columns are 1-indexed
            result.append(chr(n % 26 + ord('a')))
            n //= 26
        return ''.join(reversed(result))
