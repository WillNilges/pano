import uuid
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from minio.error import S3Error
import logging

import pymeshdb
from models.image import ImageCategory
from pano import Pano
from settings import UPLOAD_DIRECTORY, WORKING_DIRECTORY
from src.models.user import User
from storage import Storage

import os
import shutil
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

from jwt_token_auth import check_token, token_required

from authlib.integrations.flask_client import OAuth


from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

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


@login_required
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
    image = pano.update_image(
        uuid.UUID(id),
        int(new_install_number) if new_install_number else None,
        ImageCategory[new_category.lower()] if new_category else None,
        None,  # TODO (wdn): Allow users to update the image itself
    )
    return jsonify(image), 200


@login_required
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
            try:
                os.makedirs(UPLOAD_DIRECTORY)
            except:
                pass
            # Save the file to local storage
            file_path = os.path.join(UPLOAD_DIRECTORY, filename)
            file.save(file_path)

            # Try to upload it to S3 and save it in MeshDB
            try:
                d = pano.handle_upload(
                    install_number, file_path, bypass_dupe_protection
                )

                # If duplicates were found from that upload, then don't do
                # anything else and keep chekcing for more.
                if d:
                    possible_duplicates.update(d)
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
        return possible_duplicates, 409

    return "", 201


@app.route("/", methods=["GET", "POST"])
def home():
    if not current_user.is_authenticated:
        return "whats up dog (<a href='/login/google'>click here to login</a>)"

    return (
        "<p>Hello, {}! You're logged in! Email: {}</p>"
        '<a class="button" href="/logout">Logout</a>'.format(
            current_user.name, current_user.email_address
        )
    )


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
    if not login_user(user):
        return "Error ocurred while logging in", 400

    # Send user back to homepage
    return redirect("/")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")
