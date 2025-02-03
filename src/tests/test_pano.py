import unittest
from unittest.mock import MagicMock, patch

from pymeshdb.models.building import Building
from sqlalchemy.orm import Session

from db import PanoDB
from models.base import Base
from models.image import Image, ImageCategory
from pano import Pano

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

        self.minio.check_for_duplicates.side_effect = [
            None,
        ]

        r = self.pano.handle_upload(1, "./src/tests/sample_images/pano.png")
        self.assertIsNone(r)

    # @patch("storage.Storage.check_for_duplicates")
    def test_handle_duplicate_upload(self):
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING, SAMPLE_BUILDING]

        self.minio.check_for_duplicates.side_effect = [
            None,
            {"some-uuid": "http://some-url.com"},
        ]

        r = self.pano.handle_upload(1, "./src/tests/sample_images/pano.png")
        self.assertIsNone(r)
        r = self.pano.handle_upload(1, "./src/tests/sample_images/pano.png")
        self.assertEqual({"some-uuid": "http://some-url.com"}, r)

    def test_handle_upload_with_bypass_dupe(self):
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING, SAMPLE_BUILDING]

        self.minio.check_for_duplicates.side_effect = [
            None,
            {"some-uuid": "http://some-url.com"},
        ]

        r = self.pano.handle_upload(
            1, "./src/tests/sample_images/pano.png", bypass_dupe_protection=True
        )
        self.assertIsNone(r)
        r = self.pano.handle_upload(
            1, "./src/tests/sample_images/pano.png", bypass_dupe_protection=True
        )
        self.assertIsNone(r)

        # Make sure there are two records in the DB
        self.assertEqual(2, len(self.pano.get_images(1)))

    def test_failed_to_upload_to_s3(self):
        self.minio.upload_objects.side_effect = Exception()
        
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING]

        self.minio.check_for_duplicates.side_effect = [
            None,
        ]

        with self.assertRaises(Exception):
            r = self.pano.handle_upload(
                1, "./src/tests/sample_images/pano.png" 
            )

        # Make sure there are no images in the DB
        self.assertEqual(0, len(self.pano.get_images(1)))
