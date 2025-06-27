# import unittest
#
# from pano import Pano
#
#
# class TestAPI(unittest.TestCase):
#    def setUp(self):
#        self.pano = Pano()
#
#    def test_upload_and_retrieve():
#        pass

import unittest
from unittest.mock import patch
import uuid
from flask_login import FlaskLoginClient
from models.image import Image
from models.panorama import Panorama
from models.user import User
from pano import Pano
import pytest
from flask import Flask
from .test_pano import NN_UUID_1
from . import SAMPLE_IMAGE_PATH, UUID_1
from src.main import app


class TestAPI(unittest.TestCase):
    @patch("meshdb_client.MeshdbClient")
    def setUp(self, meshdb):
        app.config["TESTING"] = True
        app.config["LOGIN_DISABLED"] = True
        self.meshdb = meshdb
        self.pano = Pano(meshdb=meshdb)
        with app.test_client() as client:
            self.client = client
        self.pano.handle_upload(SAMPLE_IMAGE_PATH, UUID_1)

    @patch("main.pano.db.get_image")
    @patch("main.Pano.get_images_by_install_number")
    def test_get_image_by_image_id(self, mock_pano, mock_db):
        image_object = Panorama(path=SAMPLE_IMAGE_PATH, install_id=UUID_1, node_id=None)
        serialized_image_object = self.pano.serialize_image(image_object)
        mock_pano.return_value = ([serialized_image_object], {})
        mock_db.return_value = image_object

        response = self.client.get("/api/v1/install/1")
        image_id = response.json["images"][0]["id"]
        self.assertEqual(uuid.UUID(image_id), image_object.id)

        response = self.client.get(f"/api/v1/image/{image_object.id}")
        self.maxDiff = None
        self.assertEqual(uuid.UUID(response.json["id"]), image_object.id)

    @patch("main.pano.db.get_image")
    @patch("main.Pano.get_images_by_network_number")
    def test_get_image_by_node_id(self, mock_pano, mock_db):
        image_object = Panorama(path=SAMPLE_IMAGE_PATH, node_id=NN_UUID_1)
        serialized_image_object = self.pano.serialize_image(image_object)
        mock_pano.return_value = ([serialized_image_object], {})
        mock_db.return_value = image_object

        response = self.client.get("/api/v1/nn/1")
        image_id = response.json["images"][0]["id"]
        self.assertEqual(uuid.UUID(image_id), image_object.id)

        response = self.client.get(f"/api/v1/image/{image_object.id}")
        self.maxDiff = None
        self.assertEqual(uuid.UUID(response.json["id"]), image_object.id)

    def test_get_image_by_image_id_bad_requests(self):
        invalid_id = "chom"
        response = self.client.get(f"/api/v1/image/{invalid_id}")
        assert response.status_code == 400
        assert response.json

        assert (
            response.json["detail"]
            == f"get_image_by_image_id failed: {invalid_id} is not a valid UUID."
        )

        response = self.client.get(f"/api/v1/image/")
        assert response.status_code == 404
        assert not response.json

    def test_get_image_by_install_number_bad_requests(self):
        invalid_id = "chom"
        response = self.client.get(f"/api/v1/install/{invalid_id}")
        assert response.status_code == 400
        assert response.json
        assert response.json["detail"] == f"{invalid_id} is not an integer."

        response = self.client.get(f"/api/v1/install/")
        assert response.status_code == 404
        assert not response.json

    def test_get_image_by_network_number_bad_requests(self):
        invalid_id = "chom"
        response = self.client.get(f"/api/v1/nn/{invalid_id}")
        assert response.status_code == 400
        assert response.json
        assert response.json["detail"] == f"{invalid_id} is not an integer."

        response = self.client.get(f"/api/v1/nn/")
        assert response.status_code == 404
        assert not response.json


#    def get_install(self):
#        pass

#    def test_upload_and_retrieve(self):
#        chom = uuid.uuid4()
#        self.meshdb.get_install.return_value = chom
#        post_data = {
#            "installNumber": 420
#        }
#        rv = self.client.post("/api/v1/upload", data=post_data)
#        assert rv.status_code == 201


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_unauthenticated(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"click here to login" in rv.data


def test_userinfo_unauthenticated(client):
    rv = client.get("/userinfo")
    assert rv.status_code == 401
    assert b"Please log in" in rv.data


def test_get_image_by_image_id_not_found(client):
    test_id = uuid.uuid4()
    rv = client.get(f"/api/v1/image/{test_id}")
    assert rv.status_code == 404


# def test_get_images_by_install_id_not_found(client):
#    rv = client.get("/api/v1/install/404")
#    assert rv.status_code == 404
#
# def test_get_images_by_node_id_not_found(client):
#    rv = client.get("/api/v1/nn/404")
#    assert rv.status_code == 404
