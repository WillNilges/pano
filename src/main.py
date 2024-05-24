from minio.error import S3Error
from dotenv import load_dotenv
import logging

from storage_minio import StorageMinio

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")

def main():
    load_dotenv()

    # The file to upload, change this path if needed
    source_file = "/tmp/test-file.txt"

    # The destination bucket and filename on the MinIO server
    destination_file = "my-test-file-2.txt"

    storage = StorageMinio()
    storage.upload_images({destination_file: source_file})


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
