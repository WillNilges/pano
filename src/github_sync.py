import settings
import logging
import os


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")

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

    for file in os.listdir(f"{repo_path}/data/panoramas"):
        logging.info(f"Processing {file}")
        pass

if __name__ == "__main__":
    github_sync()
    logging.info("Complete. Goodbye!")
