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

    # FIXME(wdn): This almost certainly isn't correct, but if id exists and is_active is true, then... shrug?
    # If an attacker can get a user into the application somehow, then gg. That's definitely not good.
    # Counterpoint: https://stackoverflow.com/questions/19532372/whats-the-point-of-the-is-authenticated-method-used-in-flask-login
    def is_authenticated(self):
        if not self.id or not self.is_active:
            return False
        return True

    def is_anonymous(self):
        return False
