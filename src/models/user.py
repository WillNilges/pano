from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[str] = mapped_column(primary_key=True)
    is_active: Mapped[bool] = mapped_column()
    name: Mapped[str] = mapped_column()
    email_address: Mapped[str] = mapped_column()

    # --- django-login required methods ---
    def get_id(self):
        return self.id

    def is_active(self):
        return self.is_active

    def is_authenticated(self):
        if not self.id or not self.is_active:
            return False
        return True

    def is_anonymous(self):
        return False
