import dataclasses
from datetime import datetime
import logging
import uuid
from typing import Any, Optional

from db import PanoDB
from meshdb_client import MeshdbClient
from models.image import Image
from models.panorama import Panorama
from pymeshdb.models.install import Install
from pymeshdb.models.node import Node
from storage_minio import StorageMinio
from werkzeug.exceptions import NotFound


class Pano:
    def __init__(
        self,
        meshdb: MeshdbClient = MeshdbClient(),
        storage: StorageMinio = StorageMinio(),
        db: PanoDB = PanoDB(),
    ) -> None:
        self.meshdb: MeshdbClient = meshdb
        self.storage: StorageMinio = storage
        self.db: PanoDB = db

    def get_all_images(self) -> dict[int, list[dict]]:
        serialized_images = {}
        for image in self.db.get_all_images():
            if not serialized_images.get(image.install_id):
                serialized_images[image.install_id] = []

            i = dataclasses.asdict(image)
            i["url"] = self.storage.get_presigned_url(image)
            serialized_images[image.install_id].append(i)
        return serialized_images

    def get_images_by_install_number(
        self,
        install_number: int,
        get_related: bool = False,
    ) -> tuple[list[dict], dict[str, list[dict]]]:
        install_id = None

        install = self.meshdb.get_install(install_number)
        if not install:
            raise NotFound(
                "Could not resolve new install number. Is this a valid install?"
            )

        install_id = uuid.UUID(install.id)

        images = self.db.get_images_by_install_id(install_id)
        serialized_images = []
        for image in images:
            serialized_images.append(self.serialize_image(image))

        related_images = {}
        if get_related:
            related_images = self.get_related_images_from_install(install)

        return serialized_images, related_images

    def get_related_images_from_install(
        self, install: Install
    ) -> dict[str, list[dict]]:
        # Get images from node if it exists
        additional_images_by_network_number = {}
        if install.node:
            node_images = self.db.get_images_by_node_id(uuid.UUID(install.node.id))
            additional_images = []
            for image in node_images:
                additional_images.append(self.serialize_image(image))
            additional_images_by_network_number[
                install.node.network_number
            ] = additional_images
        return additional_images_by_network_number

    def get_images_by_network_number(
        self,
        network_number: int,
        get_related: bool = False,
    ) -> tuple[list[dict], dict[str, list[dict]]]:
        node_id = None

        node = self.meshdb.get_node(network_number)
        if not node:
            raise NotFound(
                "Could not resolve network number. Is this a valid network number?"
            )

        node_id = uuid.UUID(node.id)

        images = self.db.get_images_by_node_id(node_id)
        serialized_images = []
        for image in images:
            serialized_images.append(self.serialize_image(image))

        related_images = {}
        if get_related:
            related_images = self.get_related_images_from_node(node)

        return serialized_images, related_images

    def get_related_images_from_node(self, node: Node) -> dict[str, list[dict]]:
        # Get images from related installs
        additional_images_by_install_number = {}
        for install in node.installs:
            if install.id:
                install_images = self.db.get_images_by_install_id(uuid.UUID(install.id))
                additional_images = []
                for image in install_images:
                    additional_images.append(self.serialize_image(image))
                additional_images_by_install_number[
                    install.install_number
                ] = additional_images
        return additional_images_by_install_number

    def serialize_image(self, image: Image) -> dict[str, Any]:
        i = dataclasses.asdict(image)
        i["url"] = self.storage.get_presigned_url(image)
        return i

    # TODO: How to update order?
    def update_image(
        self,
        id: uuid.UUID,
        new_install_number: Optional[int],
        file_path: Optional[str],
    ):
        """
        Allows us to update details about an image, or change the image itself.
        Requires a uuid to identify the image.
        Optional new_install_number
        Optional new_category
        Pass a new file path to update the image itself.
        """

        image = self.db.get_image(id)

        if not image:
            raise ValueError(f"[db] Could not find image with id {id}")

        # Sanity check that the image exists. This should never fail
        if not self.storage.object_exists(image.object_path()):
            raise ValueError(f"[storage] Could not find image object with id {id}")

        # Update details if necessary
        if new_install_number:
            new_install = self.meshdb.get_install(new_install_number)
            if not new_install:
                raise NotFound(
                    "Could not resolve new install number. Is this a valid install?"
                )
            image.install_id = uuid.UUID(new_install.id)

        if file_path:
            image.signature = image.get_image_signature(file_path)

            try:
                self.storage.upload_objects({image.object_path(): file_path})
            except Exception as e:
                logging.exception("Failed to upload object to S3.")
                raise e

        # Update the timestamp of the image
        image.timestamp = datetime.now()

        # If all of that worked, save the image.
        self.db.save_image(image)

        image_dict = dataclasses.asdict(image)
        image_dict["url"] = self.storage.get_presigned_url(image)

        return image_dict

    def handle_upload(
        self,
        file_path: str,
        install_id: uuid.UUID | None = None,
        node_id: uuid.UUID | None = None,
        bypass_dupe_protection: bool = False,
    ) -> dict[str, str]:
        # Create a DB object
        image_object = Panorama(path=file_path, install_id=install_id, node_id=node_id)

        # Check the images for possible duplicates.
        if not bypass_dupe_protection:
            possible_duplicates = self.detect_duplicates(image_object)
            if possible_duplicates:
                return possible_duplicates

        # Upload object to S3
        try:
            self.storage.upload_objects({image_object.object_path(): file_path})
        except Exception as e:
            logging.exception("Failed to upload object to S3.")
            raise e

        self.db.save_image(image_object)

        # Empty Dict = No Dupes; We're good.
        return {}

    def detect_duplicates(self, uploaded_image: Image) -> dict[str, str]:
        """
        Uses ImageMagick to check the hash of the files uploaded against photos
        that already exist under an install. If a photo matches, the path is returned
        in the list.
        """

        possible_duplicates = {}

        # Get any images we already uploaded for this install
        images = self.db.get_image_by_signature(uploaded_image.signature)
        for i in images:
            if uploaded_image.signature in i.signature:
                possible_duplicates[
                    i.original_filename
                ] = self.storage.get_presigned_url(i)
                logging.warning(
                    f"Got possible duplicate. Uploaded file '{uploaded_image.original_filename}' looks like existing file '{i.original_filename}' (Signature matches: {i.signature})"
                )

        return possible_duplicates
