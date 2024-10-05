import uuid
from meshdb_client import MeshdbClient
from storage_minio import StorageMinio


class Pano:
    def __init__(self) -> None:
        self.meshdb = MeshdbClient()
        self.minio = StorageMinio()

    # Mocking some kind of upload portal with an array of strings
    # TODO: What about NNs? What about normal install photos?
    def handle_upload(self, install_number: int, file_path: str) -> None:
        building = self.meshdb.get_primary_building_for_install(install_number)
        # TODO: Distinguish between the server shitting and getting passed a bad install #
        if not building:
            raise ValueError("Could not find a building associated with that Install #")

        # Upload object to S3
        object_name = f"{install_number}/{uuid.uuid4}"
        self.minio.upload_images({object_name: file_path})

        # Save link to object in MeshDB
        self.meshdb.save_panorama_on_building(building.id, object_name)
        print("Mock 200 OK")
