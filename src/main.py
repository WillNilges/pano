from flask import Flask
from minio.error import S3Error
from dotenv import load_dotenv
import logging
from pano import Pano
from storage import Storage
#from storage_git import StorageGit
from storage_minio import StorageMinio

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")

def main() -> None:
    load_dotenv()

    pano = Pano()

    panos = pano.meshdb.get_building_panos("015c006f-edb8-49a1-bf3e-8728c867b1ca")
    print(panos)
    
    flask_app = Flask(__name__)

    @flask_app.route("/submit", methods=["POST"])
    def respond():
        pano.handle_upload(10071, "")

    flask_app.run(host="127.0.0.1", port=8089, debug=False)



def sync(source_storage: Storage, destination_storage: Storage) -> None:
    pass
    
if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
