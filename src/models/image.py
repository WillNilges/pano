import dataclasses
import enum
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath

from sqlalchemy import DateTime, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from wand.image import Image as WandImage

from models.base import Base
from settings import MINIO_BUCKET, MINIO_SECURE, MINIO_URL


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
        self.signature = self.get_image_signature(path)

        # Save the original filename.
        basename = PurePosixPath(path).name
        if basename:
            self.original_filename = basename
        else:
            raise ValueError("Could not get filename")

        super().__init__()

    def get_image_signature(self, path: str) -> str:
        try:
            sig = WandImage(filename=path).signature
            if sig:
                # Not sure why, but my linter complains unless I hard cast this to str.
                return str(sig)
            raise ValueError("Signature for image was None")
        except Exception as e:
            logging.exception("Failed to get signature.")
            raise e

    def object_path(self):
        return f"{self.install_number}/{self.id}"
