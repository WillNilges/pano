# uv (optional)

uv is an all-in-one Python environment manager.
Our current configuration permits, but does not require, the use of uv.

If you're not using uv, replace `uv run` with however you use your virtualenv, and the rest should stay the same.

## Run a Python shell in the project

```
uv run python
```

# Service dependencies via Docker Compose

Pano depends on service dependencies Postgres and MinIO.
For your convenience, we provide a Docker Compose configuration that contains all service dependencies.

## Start all service dependencies

```
docker compose --file ./dev/docker-compose.yml up --detach
```

## Stopping all service dependencies

```
docker compose --file ./dev/docker-compose.yml down
```

# Automated tests

## Running unit tests

```
uv run pytest tests/unit/
```