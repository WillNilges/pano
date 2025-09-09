import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from sqlalchemy import CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from util.exif import get_exif_data
from wand.image import Image as WandImage
from models.base import Base


log = logging.getLogger("image")

@dataclass
class Image(Base):
    __tablename__ = "image"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    install_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    node_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    # The hash of the image generated from ImageMagick
    signature: Mapped[str] = mapped_column()
    # The name of the file when it was uploaded
    original_filename: Mapped[str] = mapped_column()
    public: Mapped[bool] = mapped_column()

    __table_args__ = (
        CheckConstraint(
            "(install_id IS NOT NULL AND node_id IS NULL) OR "
            "(node_id IS NOT NULL AND install_id IS NULL)",
            name="check_install_id_and_node_id_are_mutually_exclusive",
        ),
    )

    def __init__(
        self,
        path: str,
        install_id: uuid.UUID | None = None,
        node_id: uuid.UUID | None = None,
        public: bool = False,
    ):
        self.id = uuid.uuid4()
        self.public = public

        try:
            exif_timestamp_str = get_exif_data(path)["DateTime"]
            timestamp = datetime.strptime(exif_timestamp_str, "%Y:%m:%d %H:%M:%S")
            self.timestamp = timestamp
        except Exception:
            now = datetime.now()
            log.warning(f"Could not extract timestamp from EXIF data. Setting to {now}")
            self.timestamp = now

        # The constraint should save us here but why not add redundancy
        if install_id and node_id:
            raise ValueError("Cannot pass both install_id and node_id!")

        if install_id:
            self.install_id = install_id
        if node_id:
            self.node_id = node_id

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
        return f"{self.id}"
