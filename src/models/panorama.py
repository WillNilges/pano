import uuid
from models.image import Image
from sqlalchemy.orm import Mapped, mapped_column


class Panorama(Image):
    order: Mapped[int] = mapped_column()

    def __init__(
        self,
        path: str,
        install_number: uuid.UUID | None = None,
        network_number: uuid.UUID | None = None,
    ):
        self.order = 0
        super().__init__(path, install_number, network_number)
