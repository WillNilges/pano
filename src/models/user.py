from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[str] = mapped_column(primary_key=True)
    is_active: Mapped[bool] = mapped_column()
    name: Mapped[str] = mapped_column()
    email_address: Mapped[str] = mapped_column()

    def get_id(self):
        return self.id
