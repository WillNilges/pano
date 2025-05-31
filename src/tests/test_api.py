#import unittest
#
#from pano import Pano
#
#
#class TestAPI(unittest.TestCase):
#    def setUp(self):
#        self.pano = Pano()
#    
#    def test_upload_and_retrieve():
#        pass
        
import unittest
from unittest.mock import patch
import uuid
from flask_login import FlaskLoginClient
from models.user import User
from pano import Pano
import pytest
from flask import Flask
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

#    def get_install(self):
#        pass

    def test_upload_and_retrieve(self):
        chom = uuid.uuid4() 
        self.meshdb.get_install.return_value = chom
        post_data = {
            "installNumber": 420
        }
        rv = self.client.post("/api/v1/upload", data=post_data)
        assert rv.status_code == 201

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

#def test_get_images_by_install_id_not_found(client):
#    rv = client.get("/api/v1/install/404")
#    assert rv.status_code == 404
#
#def test_get_images_by_node_id_not_found(client):
#    rv = client.get("/api/v1/nn/404")
#    assert rv.status_code == 404
