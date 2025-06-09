import re
import uuid
from pano import Pano
import settings
import logging
import os


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")

pano = Pano()

def github_sync():
    """
    Clones/pulls the repo to a known location (some mounted volume, most likely)
    and compares the files found in data/panoramas with the file titles in the DB,
    then goes through basically upload() for each file it does not have.
    """

    repo_path = os.environ.get("NODE_DB_REPO_PATH")
    if not repo_path:
        log.error("Please specify NODE_DB_REPO_PATH in the environment.")
        return

    for file_name in os.listdir(f"{repo_path}/data/panoramas"):
        logging.info(f"Processing {file_name}")
        existing_image = pano.db.get_image(original_filename=file_name)
        if existing_image:
            continue

        logging.info("Will upload.")
        network_number = None
        install_number = None

        # Get the number.
        pattern = r'\d+'

        # Search for the first match
        match = re.search(pattern, file_name)

        # Check if a match was found and print it
        if not match:
            logging.warning(f"Could not parse number from {file_name}. Filename might be invalid.")
            continue

        first_match = match.group()

        # FIXME (wdn): Code duplication :(
        if "nn" in file_name:
            network_number = int(first_match) 
            logging.info(f"Network Number = {network_number}")
            node = pano.meshdb.get_node(network_number)
            if not node:
                logging.warning(f"Failed to resolve NN {network_number} to node_id.")
                continue
            node_id = uuid.UUID(node.id)
            logging.info(f"Successfully resolved NN {network_number} to node_id {node_id}")
        else:
            install_number = int(first_match)
            logging.info(f"Install Number = {install_number}")
            install = pano.meshdb.get_install(install_number)
            if not install:
                logging.warning(f"Failed to resolve install# {install_number} to install_id.")
                continue
            install_id = uuid.UUID(install.id)
            logging.info(f"Successfully resolved install# {install_number} to install_id {install_id}")

        #pano.handle_upload(
        #            f"{repo_path}/data/panoramas/{file}", install_id, node_id, False 
        #        )

if __name__ == "__main__":
    github_sync()
    logging.info("Complete. Goodbye!")
