import os
import logging
import jwt
from flask import jsonify, request


def check_token(token: str | None):
    if not token:
        logging.exception("Token is missing")
        return jsonify({"error": "token is missing"}), 403
    try:
        secret_key = os.environ.get("PANO_SECRET_KEY")
        if not secret_key:
            raise EnvironmentError("Did not find PANO_SECRET_KEY. Check .env")
        jwt.decode(token, secret_key, algorithms="HS256")
    except Exception as error:
        logging.exception("Token is invalid")
        return jsonify({"error": "token is invalid/expired"}), 403

    return None


def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get("token")
        token_check_result = check_token(token)
        if token_check_result:
            return token_check_result

        return f(*args, **kwargs)

    return decorated
