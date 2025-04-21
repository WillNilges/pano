import unittest

from storage_minio import StorageMinio
from tests.test_pano import SAMPLE_IMAGE_PATH

class TestStorageMinio(unittest.TestCase):
    bucket_name = "test-bucket"

    def setUp(self):
        self.storage = StorageMinio(self.bucket_name)

        found = self.storage.client.bucket_exists(self.bucket_name)
        if not found:
            self.storage.client.make_bucket(self.bucket_name)
            print("Created bucket", self.bucket_name)
        else:
            print("Bucket", self.bucket_name, "already exists")

    def tearDown(self) -> None:
        self.storage.client.remove_bucket(self.bucket_name)

    def test_upload_objects(self):
        self.storage.upload_objects({"1/pano.png": SAMPLE_IMAGE_PATH})
        self.assertEqual(["1/pano.png"], self.storage.list_all_objects(1))
        self.storage.client.remove_object(self.bucket_name, "1/pano.png")
