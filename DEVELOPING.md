# uv (optional)

uv is an all-in-one Python environment manager.
Our current configuration permits, but does not require, the use of uv.
To use uv, prefix Python-related commands with:

```
uv run
```

For example:

```
uv run python
```

# PYTHONPATH

As a short-term workaround, set `PYTHONPATH` manually:

```
export PYTHONPATH=./src/
```

# Run the web server

```
flask --app main.app run
```

or

```
gunicorn -w 4 'main:app'
```

# Service dependencies via Docker Compose

Pano depends on service dependencies Postgres and MinIO.
For your convenience, we provide a Docker Compose configuration that contains all service dependencies.

## Start all service dependencies

```
docker compose --file ./dev/docker-compose.yml up --detach
```

## Stop all service dependencies

```
docker compose --file ./dev/docker-compose.yml down
```

# Automated tests

## Run unit tests

```
pytest tests/unit/
```