# Pano

A dummy-simple API in front of garage for storing and accessing panoramas in MeshDB.

<p align="center">
  <img height="300px" src="https://github.com/user-attachments/assets/692fabb1-4b7c-4392-9731-604ebdf95af1" alt="Pano Logo">
</p>

<a href="https://codecov.io/github/WillNilges/pano" > 
 <img src="https://codecov.io/github/WillNilges/pano/graph/badge.svg?token=M51PLA57H7"/> 
 </a>

# Running

```
gunicorn main:app -b 0.0.0.0:8081
```

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

We use garage to store images as objects. The schema for the path that identifies
a particular object is very simple:

`/<bucket name>/<install_number>/<uuid>`

# Migrations

To upgrade your database with the latest changes, run the following:

```
alembic upgrade head
```

To create new migrations when the data model is changed, run a revision command
like so:

```
alembic revision --autogenerate -m "initial revision"
```

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

## Garage Setup

Garage has a slightly more involved setup than garage (whom we migrated off of due to garage becoming hostile to open source)

https://garagehq.deuxfleurs.fr/documentation/quick-start/

1. Stand up Garage with this command

```
docker compose -f dev/docker-compose.yml up -d garage
```

2. Get your node ID with this command

_Note that your container name might be different. Fetch it with `docker ps`

```
docker exec -it pano-dev-garage-1 /garage status
```

3. Finally, apply a layout

```
garage layout assign -z dc1 -c 1G <node_id>
docker exec -it pano-dev-garage-1 /garage layout apply --version 1
```

## Adding Env variables

if you need to add an env var,

1. Add it to the Environment on Github as either a secret or a value

2. Add it to the `deploy-to-k8s.yaml` file under the appropriate deployment (pano or garage)

3. Add it to the appropriate `configmap.yaml` or `secrets.yaml` file.
