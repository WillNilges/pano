import os

from dotenv import load_dotenv

load_dotenv()
WORKING_DIRECTORY = "/tmp/pano"
UPLOAD_DIRECTORY = f"{WORKING_DIRECTORY}/upload"

PG_CONN = os.getenv("PG_CONN")

MINIO_SECURE = False if os.environ["MINIO_SECURE"] == "False" else True
MINIO_URL = os.environ["MINIO_URL"]
MINIO_PUBLIC_URL = os.environ["MINIO_URL"]
MINIO_BUCKET = os.environ["MINIO_BUCKET"]
