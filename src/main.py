import uuid
from flask import Flask, jsonify, request
from flask_cors import CORS
from minio.error import S3Error
import logging

import pymeshdb
from models.image import ImageCategory
from pano import Pano, PossibleDuplicate
from settings import UPLOAD_DIRECTORY, WORKING_DIRECTORY
from storage import Storage

import os
import shutil
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

from jwt_token_auth import check_token, token_required

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")


pano = Pano()

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
app.config["UPLOAD_FOLDER"] = UPLOAD_DIRECTORY
app.config["MAX_CONTENT_LENGTH"] = 16 * 1000 * 1000
app.config["SECRET_KEY"] = "chomskz"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_and_save_file_locally(file) -> str:
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if not file.filename:
        raise ValueError("File has no filename")

    if not file:
        raise FileNotFoundError("Received no file")

    if not allowed_file(file.filename):
        raise ValueError("File type not allowed.")

    # Sanitize input
    filename = secure_filename(file.filename)
    # Ensure that the upload directory exists
    try:
        os.makedirs(UPLOAD_DIRECTORY)
    except:
        pass
    # Save the file to local storage
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    file.save(file_path)
    return file_path

# Lists all images from all install numbers of a category
@app.route("/api/v1/<category>")
def get_all_images(category):
    j = jsonify(pano.get_all_images(ImageCategory[category]))
    return j, 200


# Any other route requires auth.
@app.route("/api/v1/install/<install_number>")
@app.route("/api/v1/install/<install_number>/<category>")
def get_images_for_install_number(install_number: int, category: str | None = None):
    # Check the token if trying to access anything except panoramas
    if category != "panorama":
        token_check_result = check_token(request.headers.get("token"))
        if token_check_result:
            return token_check_result

    try:
        j = jsonify(
            pano.get_images(
                install_number=int(install_number),
                category=ImageCategory[category] if category else None,
            )
        )
        return j, 200
    except ValueError:
        error = f"Install number {install_number} is not an integer."
        logging.exception(error)
        return {"detail": error}, 400


@app.route("/api/v1/update", methods=["POST"])
def update():
    # FIXME (wdn): This token checking business is not going to fly in the long
    # run
    token_check_result = check_token(request.headers.get("token"))
    if token_check_result:
        return token_check_result

    id = request.values.get("id")
    new_install_number = request.values.get("new_install_number")
    new_category = request.values.get("new_category")

    # Check if he wants us to change the file.
    dropzone_files = request.files.getlist("dropzoneImages[]")
    path = None
    if dropzone_files:
        file = dropzone_files[0]
        path = validate_and_save_file_locally(file)

    image = pano.update_image(
        uuid.UUID(id),
        int(new_install_number) if new_install_number else None,
        ImageCategory[new_category.lower()] if new_category else None,
        path,
    )
    return jsonify(image), 200


@app.route("/api/v1/upload", methods=["POST"])
def upload():
    token_check_result = check_token(request.headers.get("token"))
    if token_check_result:
        return token_check_result

    logging.info("Received upload request.")
    if "installNumber" not in request.values:
        logging.error("Bad Request! Missing Install # from header.")
        return {"detail": "Missing Install # from header"}, 400

    bypass_dupe_protection = (
        "trustMeBro" in request.values and request.values["trustMeBro"] == "true"
    )
    # check if the post request has the file part
    if "dropzoneImages[]" not in request.files:
        logging.error("Bad Request! Found no files.")
        return {"detail": "Found no files. Maybe the request is malformed?"}, 400

    try:
        install_number = int(request.values["installNumber"])
    except ValueError:
        logging.error("Bad Request! Install # wasn't an integer.")
        return {"detail": "Install # wasn't an integer"}, 400

    if not pano.meshdb.get_primary_building_for_install(install_number):
        e = {
            "detail": "Could not find building for this install number. Is this a valid number?"
        }
        logging.error(e)
        return e, 400

    dropzone_files = request.files.getlist("dropzoneImages[]")

    # We're gonna check each file for dupes. If we find a dupe, we keep track
    # of it and bail back to the client, changing nothing except for temp storage
    # until we get a confirmation.
    possible_duplicates: list[PossibleDuplicate] = []

    for file in dropzone_files:
        file_path = validate_and_save_file_locally(file)

        # Try to upload it to S3 and save it in MeshDB
        try:
            d = pano.handle_upload(
                install_number, file_path, bypass_dupe_protection
            )

            # If duplicates were found from that upload, then don't do
            # anything else and keep chekcing for more.
            if d:
                possible_duplicates.extend(d)
                continue
        except ValueError as e:
            logging.exception(
                "Something went wrong processing this panorama upload"
            )
            return {
                "detail": "Something went wrong processing this panorama upload"
            }, 400
        except pymeshdb.exceptions.BadRequestException:
            logging.exception("Problem communicating with MeshDB.")
            return {"detail": "There was a problem communicating with MeshDB."}, 500

    # Clean up working directory
    shutil.rmtree(WORKING_DIRECTORY)
    os.makedirs(WORKING_DIRECTORY)

    if possible_duplicates:
        return jsonify({"possible_duplicates": possible_duplicates}), 409

    return "", 201


@app.route("/", methods=["GET", "POST"])
def home():
    return "whats up dog"
