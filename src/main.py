import dataclasses
import logging
import os
import shutil
import uuid
from datetime import timedelta
import html

import argparse

import pymeshdb
from pymeshdb.exceptions import NotFoundException
from authlib.integrations.flask_client import OAuth
from flask import Flask, Request, Response, jsonify, redirect, request, url_for
from flask_cors import CORS
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.utils import secure_filename

from pano import Pano
from settings import UPLOAD_DIRECTORY, WORKING_DIRECTORY
from models.user import User

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

NETWORK_NUMBER_MAX = 8000

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")

pano = Pano()

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
app.config["UPLOAD_FOLDER"] = UPLOAD_DIRECTORY
app.config["MAX_CONTENT_LENGTH"] = 100 * 1000 * 1000
app.config["SECRET_KEY"] = "chomskz"

allowed_origins = {
    "origins": [
        "http://127.0.0.1:3000",
        "https://pano.nycmesh.net",
        "https://devpano.nycmesh.net",
        "https://api.devpano.nycmesh.net",
    ]
}

CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": allowed_origins, r"/userinfo": allowed_origins},
)

# Authlib
oauth = OAuth(app)

# Register google outh
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"  # provide us with common metadata configurations
google = oauth.register(
    name="google",
    server_metadata_url=CONF_URL,
    # Collect client_id and client secret from google auth api
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    client_kwargs={"scope": "openid email profile"},
)

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class IdResolutionError(Exception):
    pass


class IdNotFoundError(IdResolutionError):
    pass


@app.route("/api/v1/image/<image_id>")
def get_image_by_image_id(image_id: str):
    image_uuid = None
    try:
        image_uuid = uuid.UUID(image_id)
    except ValueError:
        error = f"get_image_by_image_id failed: {html.escape(image_id)} is not a valid UUID."
        log.exception(error)
        return {"detail": error}, 400

    if not image_uuid:
        log.error("Could not GET image. image_id not provided")
        return {"detail": "image_id not provided."}, 400

    image = pano.db.get_image(image_uuid)
    if not image:
        error = f"Image {image_id} not found."
        log.error(error)
        return {"detail": error}, 404
    i = dataclasses.asdict(image)
    i["url"] = pano.storage.get_presigned_url(image)
    return i, 200


@app.route("/api/v1/install/<install_number>")
def get_images_by_install_number(install_number: str):
    install_number_int = None
    get_related = False
    try:
        install_number_int = int(install_number)
        get_related = bool(request.values.get("get_related"))
    except ValueError:
        error = f"{html.escape(str(install_number))} is not an integer."
        logging.exception(error)
        return {"detail": error}, 400

    if not install_number_int:
        return {"detail": "install_number not provided."}, 400

    try:
        images, additional_images = pano.get_images_by_install_number(
            install_number_int, get_related
        )
    except NotFoundException:
        error = f"Could not find {html.escape(str(install_number))}. Consult MeshDB to make sure the object exists."
        logging.exception(error)
        return {"detail": error}, 404

    j = {"images": images, "additional_images": additional_images}
    return j, 200


@app.route("/api/v1/nn/<network_number>")
def get_images_by_network_number(network_number: str):
    nn = None
    get_related = False
    try:
        nn = int(network_number)
        get_related = bool(request.values.get("get_related"))
    except ValueError:
        error = f"{html.escape(str(network_number))} is not an integer."
        logging.exception(error)
        return {"detail": error}, 400

    if not nn:
        return {"detail": "network_number not provided."}, 400

    if nn > NETWORK_NUMBER_MAX:
        return {"detail": "Please enter a NN <= 8000"}, 403

    try:
        images, additional_images = pano.get_images_by_network_number(nn, get_related)
    except NotFoundException:
        error = f"Could not find {network_number}. Consult MeshDB to make sure the object exists."
        logging.exception(error)
        return {"detail": error}, 404

    j = {"images": images, "additional_images": additional_images}
    return j, 200


@app.route("/api/v1/image/<image_id>", methods=["DELETE"])
@login_required
def delete_image(image_id: str):
    raise NotImplemented


# Upadte a particular image
@app.route("/api/v1/image/<image_id>", methods=["PUT"])
@login_required
def update_image(image_id: str):
    image_uuid = None
    try:
        image_uuid = uuid.UUID(image_id)
    except ValueError:
        error = f"get_image_by_image_id failed: {html.escape(image_id)} is not a valid UUID."
        log.exception(error)
        return {"detail": error}, 403

    if not image_uuid:
        log.error("Could not PUT image. image_id not provided")
        return {"detail": "image_id not provided."}, 403

    # TODO: (wdn) Use NN or Install #
    new_install_number = request.values.get("new_install_number")

    # check if the post request has the file part
    if "dropzoneImages[]" not in request.files:
        logging.error("Bad Request! Found no files.")
        return {"detail": "Found no files. Maybe the request is malformed?"}, 400

    dropzone_files = request.files.getlist("dropzoneImages[]")
    if len(dropzone_files) != 1:
        return {"detail": "Too many files! This endpoint only expects one"}, 400

    # There should only be one file
    file = dropzone_files[0]

    if not file:
        return {"detail": "Empty file"}, 400

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if not file.filename:
        logging.error("No filename?")
        return {"detail": "File has no filename"}, 400

    if not allowed_file(file.filename):
        return {"detail": "Invalid filename"}, 400

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

    image = pano.update_image(
        image_uuid,
        int(new_install_number) if new_install_number else None,
        file_path,
    )
    return jsonify(image), 200


# Process image upload request.
@app.route("/api/v1/upload", methods=["POST"])
@login_required
def upload():
    logging.info("Received upload request.")

    # We can be passed install number or network number, but not both.
    try:
        install_id, node_id = resolve_install_id_or_node_id(request)
    except IdNotFoundError as e:
        logging.exception(e)
        return {"detail": str(e)}, 404
    except IdResolutionError as e:
        logging.exception(e)
        return {"detail": str(e)}, 400

    bypass_dupe_protection = (
        "trustMeBro" in request.values and request.values["trustMeBro"] == "true"
    )
    # check if the post request has the file part
    if "dropzoneImages[]" not in request.files:
        logging.error("Bad Request! Found no files.")
        return {"detail": "Found no files. Maybe the request is malformed?"}, 400

    dropzone_files = request.files.getlist("dropzoneImages[]")

    # We're gonna check each file for dupes. If we find a dupe, we keep track
    # of it and bail back to the client, changing nothing except for temp storage
    # until we get a confirmation.
    possible_duplicates = {}

    for file in dropzone_files:
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if not file.filename:
            logging.error("No filename?")
            return {"detail": "File has no filename"}, 400
        if file and allowed_file(file.filename):
            # Sanitize input
            filename = secure_filename(file.filename)

            # Ensure that the upload directory exists
            if not os.path.exists(UPLOAD_DIRECTORY):
                try:
                    os.makedirs(UPLOAD_DIRECTORY)
                except:
                    log.error(f"Could not create {UPLOAD_DIRECTORY}")
                    return {
                        "detail": "There was a problem processing your upload."
                    }, 500

            # Save the file to local storage
            file_path = os.path.join(UPLOAD_DIRECTORY, filename)
            file.save(file_path)

            # Try to upload it to S3 and save it in MeshDB
            try:
                d = pano.handle_upload(
                    file_path, install_id, node_id, bypass_dupe_protection
                )

                # If duplicates were found from that upload, then don't do
                # anything else and keep checking for more.
                if d:
                    possible_duplicates.update(d)
                    continue
            except ValueError as e:
                logging.exception("Error processing this panorama upload")
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
        return possible_duplicates, 409

    return "", 201


# Given a Request, resolves either an install_id or a node_id. Raises an exception
# if both are resolved. Can also raise ValueErrors if unexpected values are found
# Return value is in the form [install_id, node_id]
def resolve_install_id_or_node_id(
    request: Request,
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    install_number = None
    network_number = None

    try:
        i = request.values.get("installNumber")
        if i:
            install_number = int(i)
    except ValueError:
        raise IdResolutionError("Bad Request! Install # wasn't an integer.")

    try:
        n = request.values.get("networkNumber")
        if n:
            network_number = int(n)
    except ValueError:
        raise IdResolutionError("Bad Request! Network Number wasn't an integer.")

    # Can't have both
    if install_number and network_number:
        raise IdResolutionError("Cannot pass both an NN and an Install #")

    # Can't have neither
    if not install_number and not network_number:
        raise IdResolutionError("Must pass either NN or Install #")

    if install_number:
        install = pano.meshdb.get_install(install_number)
        if not install:
            raise IdResolutionError(
                "Could not resolve install number. Is this a valid install?"
            )

        return uuid.UUID(install.id), None

    if network_number:
        node = pano.meshdb.get_node(network_number)
        if not node:
            raise IdResolutionError(
                "Could not resolve node. Is this a valid network number?"
            )
        return None, uuid.UUID(node.id)

    raise IdResolutionError("Something unexpected happened.")


@app.route("/", methods=["GET"])
def home():
    if not current_user.is_authenticated:
        return "whats up dog (<a href='/login/google'>click here to login</a>)"

    pano_frontend_redirect_url = os.getenv("PANO_FRONTEND_REDIRECT_URL")
    if pano_frontend_redirect_url:
        return redirect(pano_frontend_redirect_url, 302)

    return (
        "<p>Hello, {}! You're logged in! Email: {}</p>"
        '<a class="button" href="/logout">Logout</a>'.format(
            current_user.name, current_user.email_address
        )
    )


@app.route("/userinfo", methods=["GET"])
def userinfo():
    if not current_user.is_authenticated:
        return {"detail": "Please log in"}, 401

    return {"name": current_user.name, "email": current_user.email_address}, 200


@login_manager.user_loader
def load_user(user_id):
    return pano.db.get_user(user_id)


# Routes for login
@app.route("/login/google")
def googleLogin():
    redirect_uri = url_for("authorize", _external=True)
    google = oauth.create_client("google")
    return google.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    token = oauth.google.authorize_access_token()
    user = token["userinfo"]
    if not user.get("email_verified"):
        logging.warning("User has not verified email.")
        return "Please verify your email before using Pano.", 400

    # "sub" is unique id
    unique_id = user.get("sub")
    user_name = user.get("name")
    user_email = user.get("email")

    # This should be handled by Google, but might as well add a check.
    if not "@nycmesh.net" in user_email:
        return "You must have an NYCMesh email to use this service", 400

    # Create a user in your db with the information provided
    # by Google
    user = User(id=unique_id, is_active=True, name=user_name, email_address=user_email)

    # Doesn't exist? Add it to the database.
    if not pano.db.get_user(unique_id):
        pano.db.save_user(user)
        logging.info(f"Saved user: {user_email}")

    # Begin user session by logging the user in
    if not login_user(user, remember=True, duration=timedelta(days=2)):
        return "Error ocurred while logging in", 400

    # Send user back to homepage
    return redirect("/")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")
