from flask import Flask, request
from flask_cors import CORS
from minio.error import S3Error
from dotenv import load_dotenv
import logging
from pano import Pano
from storage import Storage

import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "/tmp/pano/upload"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano")


def main() -> None:
    load_dotenv()

    pano = Pano()

    flask_app = Flask(__name__)
    CORS(flask_app)  # This will enable CORS for all routes
    flask_app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    flask_app.config["MAX_CONTENT_LENGTH"] = 16 * 1000 * 1000
    flask_app.config["SECRET_KEY"] = "chomskz"

    def allowed_file(filename):
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )

    @flask_app.route("/upload", methods=["POST"])
    def upload():
        print(request.files)
        # check if the post request has the file part
        if "files[]" not in request.files:
            print("no file part!")
            return "No file part!", 400

        print(request.files)
        file = request.files["files[]"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if not file.filename:
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(flask_app.config["UPLOAD_FOLDER"], filename))
            return "Success"

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
