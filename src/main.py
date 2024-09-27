from minio.error import S3Error
from dotenv import load_dotenv
import logging
from meshdb_client import MeshdbClient
from pano import Pano
from storage import Storage
#from storage_git import StorageGit
from storage_minio import StorageMinio

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")

WORKING_DIRECTORY = "/var/pano"

def main() -> None:
    load_dotenv()

    pano = Pano()

    panos = pano.meshdb.get_building_panos("015c006f-edb8-49a1-bf3e-8728c867b1ca")
    print(panos)

    #meshdb = MeshdbClient()
    ##installs = meshdb.get_all_installs()
    ##log.info(installs)
    #panos = meshdb.get_building_panos("015c006f-edb8-49a1-bf3e-8728c867b1ca")
    #print(panos)

    #return

    ## Initialize the Minio Bucket
    #storage = StorageMinio()
    ##storage.upload_images({destination_file: source_file})

    ## Clone and/or sync repo
    #github = StorageGit()
    #github.clone_repo()
    #github.sync_repo()

    ## Sync GitHub to MinIO
    #sync(github, storage)

def sync(source_storage: Storage, destination_storage: Storage) -> None:
    pass
    
if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
