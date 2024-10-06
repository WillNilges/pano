import os
from dotenv import load_dotenv


load_dotenv()
WORKING_DIRECTORY = "/tmp/pano"

MINIO_URL = os.environ["MINIO_URL"]
MINIO_BUCKET = os.environ["MINIO_BUCKET"]
