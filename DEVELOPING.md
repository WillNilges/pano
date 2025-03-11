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
