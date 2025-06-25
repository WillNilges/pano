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
#
# import unittest
# import uuid
# from flask_login import FlaskLoginClient
# from models.user import User
# import pytest
# from flask import Flask
# from src.main import app
#
# def test_request_with_logged_in_user():
#    user = User.query.get(1)
#    with app.test_client(user=user) as client:
#        # This request has user 1 already logged in!
#        client.get("/")
#
# class TestAPIAuthenticated(unittest.TestCase):
#    def setUp(self):
#        app.test_client_class = FlaskLoginClient
#        app.config["TESTING"] = True
#        user = User()
#        with app.test_client(user=user) as client:
#            self.client = client
#
#    def test_upload_and_retrieve(self):
#        rv = self.client.post("/api/v1/upload")
#        assert rv.status_code == 201
#
#
