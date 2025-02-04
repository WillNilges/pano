import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db import PanoDB
from models.base import Base
from models.image import Image, ImageCategory
from tests.test_pano import SAMPLE_IMAGE_PATH


class TestPanoDB(unittest.TestCase):
    def setUp(self):
        self.db = PanoDB("sqlite:///:memory:")

        self.session = Session(self.db.engine)
        self.image = Image(
            session=self.session, path=SAMPLE_IMAGE_PATH, install_number=1, category=ImageCategory.panorama
        )
        self.session.add(self.image)
        self.session.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.db.engine)

    def test_query_panel(self):
        expected = [self.image]
        result = self.session.query(Image).all()
        self.assertEqual(result, expected)
