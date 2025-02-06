FROM python:3.13-bookworm

WORKDIR /opt/pano

COPY pyproject.toml .
RUN mkdir src
RUN pip install .

RUN useradd -ms /bin/bash celery # Celery does not recommend running as root

COPY ./scripts ./scripts

COPY ./src .

ENTRYPOINT exec gunicorn 'meshdb.wsgi' --graceful-timeout 2 --bind=0.0.0.0:8081
