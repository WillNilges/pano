FROM python:3.13-bookworm

WORKDIR /opt/pano

COPY pyproject.toml .
RUN mkdir src
RUN pip install .

COPY ./src .

ENTRYPOINT exec gunicorn  -w 4 --graceful-timeout 2 'main:app'
