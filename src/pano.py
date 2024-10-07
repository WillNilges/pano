import logging
from pathlib import PurePosixPath
import re
import uuid
from meshdb_client import MeshdbClient
from settings import MINIO_URL
from storage_minio import StorageMinio
from wand.image import Image


class Pano:
    def __init__(self) -> None:
        self.meshdb = MeshdbClient()
        self.minio = StorageMinio()

    # Mocking some kind of upload portal with an array of strings
    # TODO: What about NNs? What about normal install photos?
    def handle_upload(
        self, install_number: int, file_path: str, bypass_dupe_protection: bool = False
    ) -> dict[str, str] | None:
        # Firstly, check the images for possible duplicates.
        if not bypass_dupe_protection:
            possible_duplicates = self.check_for_duplicates(install_number, [file_path])
            if possible_duplicates:
                return possible_duplicates

        building = self.meshdb.get_primary_building_for_install(install_number)
        # TODO: Distinguish between the server shitting and getting passed a bad install #
        if not building:
            raise ValueError("Could not find a building associated with that Install #")

        # Upload object to S3
        suffix = PurePosixPath(file_path).suffix
        letter = self.minio.get_next_lexicograph(install_number)
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

    # Check that a filename already has the correct format.
    # TODO (willnilges) If it does, and does not collide with existing images,
    # then we'll take it at face value and not change it.
    def validate_filenames(self, files) -> bool:
        p = re.compile("^(\\d)+([a-z])*.([a-z])*")
        for f in files:
            filename = f.filename
            match = p.match(filename)
            if match.span() != (0, len(filename)):
                return False
        return True

    # Uses ImageMagick to check the hash of the files uploaded against photos
    # that already exist under an install. If a photo matches, the path is returned
    # in the list.

    # This is probably going to be really expensive, so best to limit its use.
    # XXX (wdn): Perhaps we should somehow cache the signatures of our files?
    def check_for_duplicates(
        self, install_number: int, uploaded_files: list[str]
    ) -> dict[str, str]:
        # First, download any images that might exist for this install number
        existing_files = self.minio.download_images(self.minio.list_all_images(install_number))

        # If there are no existing files, we're done.
        if not existing_files:
            return {}

        # Else, we'll have to grab the signatures and compare them. Create a dictionary
        # of key: filename
        existing_file_signatures = {
            # Sanitze the paths to avoid betraying internals 
            Image(filename=f).signature: PurePosixPath(f).name for f in existing_files
        }

        # Check if any of the images we received have a matching signature to an
        # existing image
        possible_duplicates = {}
        for f in uploaded_files:
            img = Image(filename=f)
            sig = img.signature
            if sig in existing_file_signatures:
                # Sanitze the paths to avoid betraying internals 
                basename = PurePosixPath(f).name

                # Get a link to the S3 object to share with the client
                url = self.minio.client.presigned_get_object(self.minio.bucket, existing_file_signatures[img.signature])

                possible_duplicates[basename] = url 

                logging.warning(f"Got possible duplicate. {possible_duplicates[basename]} looks like {existing_file_signatures[img.signature]} (Signature matches: {sig})")

        return possible_duplicates
