import os
import logging
import jwt
from flask import jsonify, request


def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            logging.exception("Token is missing")
            return jsonify({'error': 'token is missing'}), 403
        try:
            jwt.decode(token, os.environ.get("PANO_SECRET_KEY"), algorithms="HS256")
        except Exception as error:
            logging.exception("Token is invalid")
            return jsonify({'error': 'token is invalid/expired'}), 403
        return f(*args, **kwargs)
    return decorated
