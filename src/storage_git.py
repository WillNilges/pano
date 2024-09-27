import logging
import os
from git import InvalidGitRepositoryError, Repo
import pymeshdb
from meshdb_client import MeshdbClient

from storage import Storage

log = logging.getLogger("pano.storage_git")

# Raised if we get total nonsense as a panorama title
class BadPanoramaTitle(Exception):
    pass

# Confusingly, I don't know if I want to make this implement the storage interface yet. This might be fucked.
class StorageGit(Storage):
    def __init__(self):
        self.repo_url = os.environ["PANO_GIT_REPO"]
        # This needs to be stored in a volume or something. We definitely don't
        # want to re-clone this massive git repo every time.
        self.local_dir = os.environ["PANO_GIT_LOCAL_DIR"]

    def clone_repo(self):
        if not os.path.isdir(self.local_dir):
            log.warn(f"Did not find repo at {self.local_dir}. Will clone...")
            self.repo = Repo.clone_from(self.repo_url, self.local_dir)

    def sync_repo(self):
        log.info("Pulling latest changes")
        try:
            origin = self.repo.remotes.origin
            origin.pull()
            log.info("Successfully pulled the latest changes.")
        except InvalidGitRepositoryError:
            log.exception(f"The directory at {self.local_dir} is not a valid Git repository.")
        except Exception:
            log.exception("An error occurred.")

    def upload_images(self, images: dict[str, str]) -> None:
        raise NotImplementedError("Oh god please don't make me upload images to GitHub.")

    def get_all_images(self) -> list[str]:
        images = []
        for image in os.listdir():
            images.append(f"{self.local_dir}/{image}") 

        return images

    def get_inventory(self) -> dict[int, list[str]]:
        meshdb = MeshdbClient()
        #nns = meshdb.map_installs_to_nns()
        inventory = {}

        for image in os.listdir():
            pass


    # This is awful. Maybe there are easy ways to generalize some cases like stripping
    # spaces, but for now I would rather explicitly handle these cases until I have
    # better tests.
    @staticmethod
    def _parse_pano_title(title: str) -> tuple[str, str]:
        if len(title) <= 0:
            raise BadPanoramaTitle("Got title of length 0")

        # Get that file extension outta here
        stem = Path(title).stem

        # Handle dumb edge case
        if len(stem) > 4 and stem[0:4] == "IMG_":
            return (stem[4:], "")

        # Some of the files have spaces but are otherwise fine
        if stem[0] == " ":
            stem = stem[1:]

        # Handle any other dumb edge cases by bailing
        if not stem[0].isdigit():
            raise BadPanoramaTitle(f"First character not a digit: {title}")

        number = ""
        label = ""
        for i in range(0, len(stem)):
            if stem[i].isdigit():
                number += stem[i]
            elif i == 0:
                # There are some files in here that have a space or something in the
                # first letter, so we handle that edge case by ignoring it.
                continue
            else:
                label = stem[i:]
                break
        return (number, label)


