from meshdb_client import MeshdbClient
from storage_minio import StorageMinio


class Pano():
    def __init__(self) -> None:
        self.meshdb = MeshdbClient()
        self.minio = StorageMinio()

    # Mocking some kind of upload portal with an array of strings
    # TODO: What about NNs? What about normal install photos?
    def handle_upload(self, install_number: int, mock_file: str) -> None:
        # TODO: Check if there are existing panoramas and increment the letter
        building = self.meshdb.get_primary_building_for_install(install_number) 
        
        # Decide what to name this file 
        file_name = self.get_next_filename(install_number, building.panoramas)


        minio_link = "mock"
        self.minio.upload_images({str(install_number): mock_file})
        self.meshdb.save_panorama_on_building(building.id, minio_link)
        print("Mock 200 OK")

    def get_next_filename(self, install_number: int, existing_panoramas: list[str]) -> str:
        if not existing_panoramas:
            # TODO: What if it's not just JPEGs?
            return f"{install_number}.jpg"

        last_title = sorted(existing_panoramas)[-1].split("/")[-1]

        # If all we've got is one panorama, then we should start lettering them.
        if last_title == f"{install_number}.jpg":
            return f"{install_number}a.jpg"

        last_letter = last_title.strip(".jpg").strip(f"{install_number}")

        # This means that there's gotta already be one panorama.
        if not last_letter:
            raise ValueError("Where's the letter? There should be a letter.")


