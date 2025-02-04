from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import PurePosixPath
import uuid
import enum
from sqlalchemy import DateTime, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from models.base import Base
from settings import MINIO_BUCKET, MINIO_SECURE, MINIO_URL
from storage_minio import StorageMinio

from wand.image import Image as WandImage


# Or should I have tags?
class ImageCategory(enum.Enum):
    panorama = "PANORAMA"
    equipment = "EQUIPMENT"
    detail = "DETAIL"
    miscellaneous = "MISCELLANEOUS"
    uncategorized = "UNCATEGORIZED"

    def __html__(self):
        return self._name_


@dataclass
class Image(Base):
    __tablename__ = "image"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    install_number: Mapped[int] = mapped_column()
    category: Mapped[ImageCategory] = mapped_column()
    order: Mapped[int] = mapped_column()
    # The hash of the image generated from ImageMagick
    signature: Mapped[str] = mapped_column()
    # The name of the file when it was uploaded
    original_filename: Mapped[str] = mapped_column()

    def __init__(
        self,
        path: str,
        install_number: int,
        category: ImageCategory,
    ):
        self.id = uuid.uuid4()
        self.timestamp = datetime.now()
        self.install_number = install_number
        self.category = category

        # By default, the images have no order. Set to -1 to represent that.
        self.order = -1

        # Store a signature for the image
        sig = WandImage(filename=path).signature
        if sig:
            try:
                # Not sure why, but my linter complains unless I hard cast this to str.
                self.signature = str(sig)
            except ValueError as e:
                logging.exception("Could not get signature for image")
                raise e

        # Save the original filename.
        basename = PurePosixPath(path).name
        if basename:
            self.original_filename = basename
        else:
            raise ValueError("Could not get filename")

        super().__init__()

    def get_object_path(self):
        return StorageMinio.get_object_path(self.install_number, self.id)

    def get_object_url(self):
        return f"{'https://' if MINIO_SECURE else 'http://'}{MINIO_URL}/{MINIO_BUCKET}/{self.get_object_path()}"

    # def __repr__(self) -> str:
    #    return f"Image(id={self.id}, timestamp={self.timestamp}, install_number={self.install_number}, order={self.order}, category={self.category})"
