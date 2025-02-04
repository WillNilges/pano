
import unittest

from sqlalchemy.orm import Session

from db import PanoDB
from models.image import Image, ImageCategory
from storage_minio import StorageMinio
from tests.test_pano import SAMPLE_IMAGE_PATH


class TestImage(unittest.TestCase):
    def setUp(self) -> None:
        self.db = PanoDB("sqlite:///:memory:")
        self.session = Session(self.db.engine)

    def test_get_object_path(self):
        i = Image(self.session, SAMPLE_IMAGE_PATH, 1, ImageCategory.panorama)

        self.assertEqual(f"1/{i.id}", i.get_object_path())
