import os

from dotenv import load_dotenv

load_dotenv()
WORKING_DIRECTORY = "/tmp/pano"
UPLOAD_DIRECTORY = f"{WORKING_DIRECTORY}/upload"

PG_CONN = os.getenv("PG_CONN")

garage_SECURE = False if os.environ["garage_SECURE"] == "False" else True
garage_URL = os.environ["garage_URL"]
garage_PUBLIC_URL = os.environ["garage_URL"]
garage_BUCKET = os.environ["garage_BUCKET"]
