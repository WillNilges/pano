from pathlib import PurePosixPath
import unittest
from unittest.mock import MagicMock, patch

from pymeshdb.models.building import Building
from sqlalchemy.orm import Session

from db import PanoDB
from models.base import Base
from models.image import ImageCategory
from pano import Pano
from settings import MINIO_URL

SAMPLE_BUILDING = Building(
    id="one",
    installs=[],
    bin=0,
    street_address="888 Fake Street",
    city="New York",
    state="New York",
    zip_code="10001",
    address_truth_sources=[],
    latitude=0,
    longitude=0,
)

SAMPLE_IMAGE_PATH = "./src/tests/sample_images/pano.png"


class TestPanoDB(unittest.TestCase):
    @patch("meshdb_client.MeshdbClient")
    @patch("minio.Minio")
    def setUp(self, minio, meshdb):
        self.db = PanoDB("sqlite:///:memory:")
        self.minio = minio
        self.meshdb = meshdb

        self.session = Session(self.db.engine)
        self.pano = Pano(meshdb=self.meshdb, storage=self.minio, db=self.db)

    def tearDown(self):
        Base.metadata.drop_all(self.db.engine)

    def test_handle_upload(self):
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING]

        r = self.pano.handle_upload(1, SAMPLE_IMAGE_PATH)
        self.assertIsNone(r)

        self.assertEqual(1, len(self.pano.get_images(1)))

    def test_handle_duplicate_upload(self):
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING, SAMPLE_BUILDING]

        r = self.pano.handle_upload(1, SAMPLE_IMAGE_PATH)
        self.assertIsNone(r)

        r = self.pano.handle_upload(1, SAMPLE_IMAGE_PATH)

        all_images = self.pano.get_images(1)

        self.assertEqual({PurePosixPath(SAMPLE_IMAGE_PATH).name: f"http://{MINIO_URL}/panoramas/1/{all_images[0]["id"]}"}, r)
        self.assertEqual(1, len(all_images))

    def test_handle_upload_with_bypass_dupe(self):
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING, SAMPLE_BUILDING]

        r = self.pano.handle_upload(
            1, SAMPLE_IMAGE_PATH, bypass_dupe_protection=True
        )
        self.assertIsNone(r)
        r = self.pano.handle_upload(
            1, SAMPLE_IMAGE_PATH, bypass_dupe_protection=True
        )
        self.assertIsNone(r)

        # Make sure there are two records in the DB
        self.assertEqual(2, len(self.pano.get_images(1)))

    def test_failed_to_upload_to_s3(self):
        self.minio.upload_objects.side_effect = Exception()
        
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING]

        with self.assertRaises(Exception):
            r = self.pano.handle_upload(
                1,  SAMPLE_IMAGE_PATH
            )

        # Make sure there are no images in the DB
        self.assertEqual(0, len(self.pano.get_images(1)))

    def test_get_images(self):
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING]

        r = self.pano.handle_upload(1, SAMPLE_IMAGE_PATH)
        self.assertIsNone(r)

        self.assertEqual(1, len(self.pano.get_images(1)))

        all_images = self.pano.get_images(1)
        for i in all_images:
            self.assertEqual(1, i["install_number"])
            self.assertEqual(ImageCategory.panorama, i["category"])
            self.assertEqual(0, i["order"])
            self.assertEqual("pano.png", i["original_filename"])
