import unittest
import uuid
from pathlib import PurePosixPath
from unittest.mock import MagicMock, patch

from pymeshdb.models.building import Building
from pymeshdb.models.install import Install
from sqlalchemy.orm import Session

from db import PanoDB
from models.base import Base
from pano import Pano
from settings import GARAGE_URL

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
SAMPLE_IMAGE_PATH_2 = "./src/tests/sample_images/logo.jpg"

UUID_1 = uuid.UUID("8d2d5a8a-2941-433d-abc6-259b1b02e290")
UUID_2 = uuid.UUID("b67bd7ba-a362-4d9c-931f-4ad2e9b33aed")


class TestPano(unittest.TestCase):
    @patch("meshdb_client.MeshdbClient")
    @patch("minio.Minio")
    def setUp(self, minio, meshdb):
        self.db = PanoDB("sqlite:///:memory:")
        self.minio = minio
        self.meshdb = meshdb

        mock_install = MagicMock()
        mock_install.id = str(UUID_1)
        mock_install.node = None
        self.meshdb.get_install.return_value = mock_install

        self.session = Session(self.db.engine)
        self.pano = Pano(meshdb=self.meshdb, storage=self.minio, db=self.db)

    def tearDown(self):
        Base.metadata.drop_all(self.db.engine)

    def test_handle_upload(self):
        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING]

        r = self.pano.handle_upload(SAMPLE_IMAGE_PATH, UUID_1)
        self.assertEqual({}, r)

        self.assertEqual(1, len(self.pano.get_images_by_install_number(1)))

    @patch("models.image.uuid")
    def test_handle_duplicate_upload(self, mock_uuid):
        self.meshdb.get_primary_building_for_install.side_effect = [
            SAMPLE_BUILDING,
            SAMPLE_BUILDING,
        ]

        mock_uuid_value = uuid.UUID("e67603a5-2509-4683-add5-8ffdbbd56f1d")
        mock_uuid.uuid4.return_value = mock_uuid_value

        self.minio.get_presigned_url.return_value = (
            f"http://{GARAGE_URL}/panoramas/{mock_uuid_value}"
        )

        r = self.pano.handle_upload(SAMPLE_IMAGE_PATH, UUID_1)
        self.assertEqual({}, r)

        r = self.pano.handle_upload(SAMPLE_IMAGE_PATH, UUID_1)

        all_images = self.pano.get_images_by_install_number(1)

        self.assertEqual(
            {
                PurePosixPath(
                    SAMPLE_IMAGE_PATH
                ).name: f"http://{GARAGE_URL}/panoramas/1/{all_images[0]['id']}"
            },
            r,
        )
        self.assertEqual(1, len(all_images))

    def test_handle_upload_with_bypass_dupe(self):
        self.meshdb.get_primary_building_for_install.side_effect = [
            SAMPLE_BUILDING,
            SAMPLE_BUILDING,
        ]

        r = self.pano.handle_upload(
            SAMPLE_IMAGE_PATH, UUID_1, bypass_dupe_protection=True
        )
        self.assertEqual({}, r)
        r = self.pano.handle_upload(
            SAMPLE_IMAGE_PATH, UUID_1, bypass_dupe_protection=True
        )
        self.assertEqual({}, r)

        # Make sure there are two records in the DB
        self.assertEqual(2, len(self.pano.get_images_by_install_number(1)))

    def test_failed_to_upload_to_s3(self):
        self.minio.upload_objects.side_effect = Exception()

        self.meshdb.get_primary_building_for_install.side_effect = [SAMPLE_BUILDING]

        with self.assertRaises(Exception):
            r = self.pano.handle_upload(SAMPLE_IMAGE_PATH, UUID_1)

        # Make sure there are no images in the DB
        self.assertEqual(0, len(self.pano.get_images_by_install_number(1)))

    def test_get_images(self):
        self.meshdb.get_primary_building_for_install.side_effect = [
            SAMPLE_BUILDING,
            SAMPLE_BUILDING,
        ]

        r = self.pano.handle_upload(SAMPLE_IMAGE_PATH, UUID_1)
        self.assertEqual({}, r)

        r = self.pano.handle_upload(SAMPLE_IMAGE_PATH_2, UUID_1)
        self.assertEqual({}, r)

        all_images = self.pano.get_images_by_install_number(1)

        self.assertEqual(2, len(all_images))

        self.assertEqual(UUID_1, all_images[0]["install_id"])
        self.assertEqual(None, all_images[0]["node_id"])
        self.assertEqual("pano.png", all_images[0]["original_filename"])

        self.assertEqual(UUID_1, all_images[1]["install_id"])
        self.assertEqual(None, all_images[1]["node_id"])
        self.assertEqual("logo.jpg", all_images[1]["original_filename"])
