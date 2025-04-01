import uuid
from models.image import Image
from sqlalchemy.orm import Mapped, mapped_column


class Panorama(Image):
    order: Mapped[int] = mapped_column()

    def __init__(
        self,
        path: str,
        install_id: uuid.UUID | None = None,
        node_id: uuid.UUID | None = None,
    ):
        self.order = 0
        super().__init__(path, install_id, node_id)
