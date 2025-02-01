# Pano

A dummy-simple API in front of MinIO for storing and accessing panoramas in MeshDB.

# Run

Set up Database

```
docker exec -it meshdb-postgres-1 psql -U meshdb -d postgres
# CREATE USER pano SUPERUSER ENCRYPTED PASSWORD 'localdev';
# CREATE DATABASE pano;
```

Use a venv

```
pip install -e '.[dev]'
```

`python src/main.py`

## Troubleshooting

The API Token needs Read Only, and the ability to `Change Building`

If you're getting 403's, check that you ran `create_groups` in your MeshDB Dev enviornment.
