# Pano

A dummy-simple API in front of MinIO for storing and accessing panoramas in MeshDB.

<p align="center">
  <img height="300px" src="https://github.com/user-attachments/assets/692fabb1-4b7c-4392-9731-604ebdf95af1" alt="Oxford the Grabbit">
</p>


# Schema

Pano keeps track of Images in Postgres. An Image has a uuid, a timestamp,
an install_number, an order, and a category.

- UUID: Simple unique identifier
- Timestamp: When the image was uploaded
- Install Number: The Install # this image is associated with
- Order: What order clients should display this image in when querying
for a specific install's images 
- Category: An indicator of the image contents. A panorama with potential LOS,
a photo of the equipment installed on the roof, or a notable detail about the
building.

## Notes about Schema

When querying for a Node with multiple installs, the Images from the lower install
number are returned first

We should find some way to mark if a Node is visible in an Image. Maybe add a column for it
Node Table, seen from: {uuid, uuid, uuid...}

# S3

We use MinIO to store images as objects. The schema for the path that identifies
a particular object is very simple:

`/<bucket name>/<install_number>/<uuid>`

# Run

Set up Database

```
docker exec -it meshdb-postgres-1 psql -U meshdb -d postgres
# CREATE USER pano SUPERUSER ENCRYPTED PASSWORD 'localdev';
# CREATE DATABASE pano;
```

Use a venv

`pip install -e '.[dev]'`

`flask --app app run` or `gunicorn -w 4 'main:app'`

## Token

Get a token by using jwt with your client name 

`python -c 'from dotenv import load_dotenv; import jwt; import os; load_dotenv(); print(jwt.encode({"client": "my_client"}, os.environ.get("PANO_SECRET_KEY"), algorithm="HS256"))'`

## Troubleshooting

The API Token needs Read Only, and the ability to `Change Building`

If you're getting 403's, check that you ran `create_groups` in your MeshDB Dev enviornment.
