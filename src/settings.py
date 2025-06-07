import os

from dotenv import load_dotenv

load_dotenv()
WORKING_DIRECTORY = "/tmp/pano"
UPLOAD_DIRECTORY = f"{WORKING_DIRECTORY}/upload"

PG_CONN = os.getenv("PG_CONN")

GARAGE_SECURE = False if os.environ["GARAGE_SECURE"] == "False" else True
GARAGE_URL = os.environ["GARAGE_URL"]
GARAGE_PUBLIC_URL = os.environ["GARAGE_URL"]
GARAGE_BUCKET = os.environ["GARAGE_BUCKET"]
