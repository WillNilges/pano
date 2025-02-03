
from unittest.mock import patch


class TestStorageMinio(unittest.TestCase):
    def setUp(self):
        pass

    @patch("storage_minio.StorageMinio.download_objects")
    def test_check_for_duplicates(self):
        pass
        

    # TODO: Figure out how to test upload and download
