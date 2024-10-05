import logging
from pathlib import PurePosixPath
import uuid
from meshdb_client import MeshdbClient
from settings import MINIO_URL
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
        suffix = PurePosixPath(file_path).suffix 
        letter = self.minio.get_next_object_letter(install_number)
        object_name = f"{install_number}{letter}{suffix}"
        self.minio.upload_images({object_name: file_path})

        # Save link to object in MeshDB
        # TODO: Perhaps it would be better to completely re-build the panorama
        # list for that particular building each time we save? Edge case on that:
        # we don't want to blow away panoramas from other installs.
        url = f"http://{MINIO_URL}/{object_name}"
        logging.info(url)
        self.meshdb.save_panorama_on_building(building.id, url)

    # TODO: Could we have a route to check the file names and see if there are
    # dupes?

    # Maybe we enforce a naming scheme with a regex.
    # If you give me a file with the correct format, I'll take it at face
    # value and let you know if there's a pre-existing file. Else, I'll give it
    # the next letter in the sequence.
