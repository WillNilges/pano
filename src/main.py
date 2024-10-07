from flask import Flask, request
from flask_cors import CORS
from minio.error import S3Error
import logging

import pymeshdb
from pano import Pano
from settings import UPLOAD_DIRECTORY, WORKING_DIRECTORY
from storage import Storage

import os
import shutil
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")


def main() -> None:
    pano = Pano()

    flask_app = Flask(__name__)
    CORS(flask_app)  # This will enable CORS for all routes
    flask_app.config["UPLOAD_FOLDER"] = UPLOAD_DIRECTORY
    flask_app.config["MAX_CONTENT_LENGTH"] = 16 * 1000 * 1000
    flask_app.config["SECRET_KEY"] = "chomskz"

    def allowed_file(filename):
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )

    # XXX (wdn): I think this is going to be dead code
    # Returns existing panoramas for a given install number
    # @flask_app.route("/api/v1/get-existing", methods=["GET"])
    # def existing():
    #    install_number = request.get_json()["install_number"]
    #    return pano.minio.list_all_images(install_number=install_number)

    @flask_app.route("/api/v1/upload", methods=["POST"])
    def upload():
        if "installNumber" not in request.values:
            logging.error("Bad Request! Missing Install # from header.")

        bypass_dupe_protection = (
            "trustMeBro" in request.values and request.values["trustMeBro"] == "true"
        )
        # check if the post request has the file part
        if "dropzoneImages[]" not in request.files:
            logging.error("Bad Request! Found no files.")
            return "Found no files. Maybe the request is malformed?", 400

        try:
            install_number = int(request.values["installNumber"])
        except ValueError:
            logging.exception("Bad Request! Install # wasn't an integer.")
            return "Install # wasn't an integer", 400

        dropzone_files = request.files.getlist("dropzoneImages[]")

        # pano.validate_filenames(dropzone_files)

        # We're gonna check each file for dupes. If we find a dupe, we keep track
        # of it and bail back to the client, changing nothing except for temp storage
        # until we get a confirmation.
        possible_duplicates = {}

        for file in dropzone_files:
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if not file.filename:
                logging.error("No filename?")
                return "No filename?", 400
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

                    # If duplicates were found from that upload, then don't do anything else and keep chekcing for more.
                    if d:
                        possible_duplicates.update(d)
                        continue
                except ValueError as e:
                    logging.exception(
                        "Bad Request! Could not find a building associated with that Install #"
                    )
                    return e, 400
                except pymeshdb.exceptions.BadRequestException:
                    logging.exception("Problem communicating with MeshDB.")
                    return "There was a problem communicating with MeshDB.", 500

        # Clean up working directory
        shutil.rmtree(WORKING_DIRECTORY)
        os.makedirs(WORKING_DIRECTORY)

        if possible_duplicates:
            return possible_duplicates, 409

        return "", 201

    @flask_app.route("/", methods=["GET", "POST"])
    def home():
        if request.method == "POST":
            # check if the post request has the file part
            if "file" not in request.files:
                flash("No file part")
                return redirect(request.url)
            file = request.files["file"]
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if not file.filename:
                flash("No selected file")
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(flask_app.config["UPLOAD_FOLDER"], filename))
                return """
                <!doctype html>
                <title>Thanks!</title>
                <body>
                <h1>Thanks!</h1>
                </body>
                """
        return """
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file>
          <input type=submit value=Upload>
        </form>
        """

    flask_app.run(host="127.0.0.1", port=8089, debug=False)


def sync(source_storage: Storage, destination_storage: Storage) -> None:
    pass


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
