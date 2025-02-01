from datetime import datetime
import uuid
import enum
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

# Or should I have tags?
class ImageCategory(enum.Enum):
    panoramas = 1
    equipment = 2
    details = 3
    misc = 4


class Image(Base):
    __tablename__ = "image"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    install_number: Mapped[int] = mapped_column()
    order: Mapped[int] = mapped_column()
    category: Mapped[ImageCategory] = mapped_column()

    def s3_path(self):
        return f"{self.install_number}/{self.id}"
