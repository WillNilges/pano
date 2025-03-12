# virtualenv

You should use a virtualenv, through your preferred version management tool,
for example pyenv or uv.

## uv (optional)

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

# Install this package as editable

## uv

```
uv pip install --editable .
```

## virtualenv (no uv)

```
source .venv/bin/activate
pip install --editable .
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