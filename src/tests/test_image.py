import unittest
import uuid

from sqlalchemy.orm import Session

from db import PanoDB
from models.image import Image
from storage_minio import StorageMinio
from .sample_data import SAMPLE_IMAGE_PATH


class TestImage(unittest.TestCase):
    def setUp(self) -> None:
        self.db = PanoDB("sqlite:///:memory:")

    def test_get_object_path(self):
        i = Image(SAMPLE_IMAGE_PATH, uuid.uuid4())

        self.assertEqual(f"{i.id}", i.object_path())
