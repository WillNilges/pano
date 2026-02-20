from dataclasses import dataclass
import enum
import uuid
from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class TransitionType(enum.Enum):
    zoom = "ZOOM"
    pan = "PAN"

    def __html__(self):
        return self._name_


@dataclass
class Quad:
    upper_left: tuple[float, float]
    upper_right: tuple[float, float]
    lower_left: tuple[float, float]
    lower_right: tuple[float, float]


class Transition(Base):
    __tablename__ = "transition"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    src: Mapped[uuid.UUID] = mapped_column()
    dst: Mapped[uuid.UUID] = mapped_column()
    transition_type: Mapped[TransitionType] = mapped_column()
    quad: Mapped[Quad] = mapped_column()
