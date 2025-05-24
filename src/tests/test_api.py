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
        
import uuid
import pytest
from flask import Flask
from src.main import app

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

def test_get_image_by_image_id_not_found(monkeypatch, client):
    # Patch pano.db.get_image to raise NotFoundException or return None
    #from src.main import pano
    #from pymeshdb.exceptions import NotFoundException

    #def fake_get_image(image_id):
    #    raise NotFoundException("Not found")
    #monkeypatch.setattr(pano.db, "get_image", fake_get_image)

    test_id = uuid.uuid4()
    rv = client.get(f"/api/v1/image/{test_id}")
    # Your endpoint does not handle NotFoundException, so this will error (500).
    # If you want to return 404, update your endpoint to catch NotFoundException.
    assert rv.status_code == 404

# More tests can be added for other endpoints, e.g., /api/v1/upload, /api/v1/update, etc.
