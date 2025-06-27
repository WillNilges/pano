import argparse
import re
import uuid
from pano import Pano
import settings
import logging
import os

import git
from git import Repo
from git.exc import GitCommandError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")

pano = Pano()


class CloneProgress(git.remote.RemoteProgress):
    def update(self, *args, **kwargs):
        # This method is called during the cloning process
        if "info" in kwargs:
            print(kwargs["info"].strip())


def manage_repo(repo_path, repo_url):
    # Check if the repository exists at the specified path
    if os.path.exists(repo_path):
        try:
            # Attempt to open the existing repository
            repo = Repo(repo_path)
            print(f"Repository found at {repo_path}. Pulling latest changes...")
            # Pull the latest changes
            repo.remotes.origin.pull()
            print("Repository updated successfully.")
        except GitCommandError as e:
            print(f"Error while pulling the repository: {e}")
    else:
        try:
            # Clone the repository since it does not exist
            print(f"Cloning repository from {repo_url} to {repo_path}...")
            Repo.clone_from(repo_url, repo_path)  # , progress=CloneProgress())
            print("Repository cloned successfully.")
        except GitCommandError as e:
            print(f"Error while cloning the repository: {e}")


def github_sync():
    parser = argparse.ArgumentParser(
        prog="Pano Node-DB Importer",
        description="""
        Clones/pulls the repo to a known location (some mounted volume, most likely)
        and compares the files found in data/panoramas with the file titles in the DB,
        then goes through basically upload() for each file it does not have.
        """,
        epilog="Chom E :)",
    )

    parser.add_argument("-w", "--write", action="store_true")

    args = parser.parse_args()

    repo_path = os.environ.get("NODE_DB_PATH")
    if not repo_path:
        log.error("Please specify NODE_DB_PATH in the environment.")
        return

    repository_url = "https://github.com/nycmeshnet/node-db.git"  # Change this to your repository URL

    manage_repo(repo_path, repository_url)

    # Find files that already exist
    node_db_panoramas = set(os.listdir(f"{repo_path}/data/panoramas"))
    pano_panoramas = {item.original_filename for item in pano.db.get_all_images()}

    new_panoramas = node_db_panoramas.difference(pano_panoramas)

    log.info(f"node-db has {len(new_panoramas)} images we don't have.")

    for file_name in new_panoramas:
        log.info(f"Processing {file_name}")
        # existing_image = pano.db.get_image(original_filename=file_name)
        # if existing_image:
        #    continue

        install_id = None
        node_id = None

        # Get the number.
        pattern = r"\d+"

        # Search for the first match
        match = re.search(pattern, file_name)

        # Check if a match was found and print it
        if not match:
            log.warning(
                f"Could not parse number from {file_name}. Filename might be invalid."
            )
            continue

        first_match = match.group()

        # FIXME (wdn): Code duplication :(
        if "nn" in file_name:
            network_number = int(first_match)
            log.info(f"Network Number = {network_number}")
            node = pano.meshdb.get_node(network_number)
            if not node:
                log.warning(f"Failed to resolve NN {network_number} to node_id.")
                continue
            node_id = uuid.UUID(node.id)
            log.info(f"Successfully resolved NN {network_number} to node_id {node_id}")
        else:
            install_number = int(first_match)
            log.info(f"Install Number = {install_number}")
            install = pano.meshdb.get_install(install_number)
            if not install:
                log.warning(
                    f"Failed to resolve install# {install_number} to install_id."
                )
                continue
            install_id = uuid.UUID(install.id)
            log.info(
                f"Successfully resolved install# {install_number} to install_id {install_id}"
            )

        if args.write:
            try:
                pano.handle_upload(
                    f"{repo_path}/data/panoramas/{file_name}",
                    install_id,
                    node_id,
                    False,
                )
                log.info("Write successful.")
            except Exception:
                log.exception("Could not save panorama.")


if __name__ == "__main__":
    github_sync()
    log.info("Complete. Goodbye!")
