from dataclasses import dataclass
from datetime import datetime
import uuid
import enum
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
from settings import MINIO_BUCKET, MINIO_URL

# Or should I have tags?
class ImageCategory(enum.Enum):
    panorama = 1
    equipment = 2
    detail = 3
    misc = 4

    def __html__(self):
        return self._name_

@dataclass
class Image(Base):
    __tablename__ = "image"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4())
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    install_number: Mapped[int] = mapped_column()
    order: Mapped[int] = mapped_column()
    category: Mapped[ImageCategory] = mapped_column()

    def __init__(self, install_number: int, category: ImageCategory):
        self.install_number = install_number
        self.category = category
        self.order = -1

        super().__init__()

    def s3_object_path(self):
        return f"{self.install_number}/{self.id}"

    def url(self):
        return  f"{MINIO_URL}/{MINIO_BUCKET}/{self.s3_object_path()}"

    #def __repr__(self) -> str:
    #    return f"Image(id={self.id}, timestamp={self.timestamp}, install_number={self.install_number}, order={self.order}, category={self.category})"
