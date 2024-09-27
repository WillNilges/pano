from meshdb_client import MeshdbClient
from storage_minio import StorageMinio


class Pano():
    def __init__(self) -> None:
        self.meshdb = MeshdbClient()
        self.minio = StorageMinio()

    # Mocking some kind of upload portal with an array of strings
    def handle_upload(self, install_number: int, mock_file: str) -> None:
        # TODO: Check if there are existing panoramas and increment the letter
        building = self.meshdb.get_primary_building_for_install(install_number) 
        minio_link = "mock"
        self.minio.upload_images([install_number, mock_file])
        self.meshdb.save_panorama_on_building(building.id, minio_link)
        print("Mock 200 OK")
