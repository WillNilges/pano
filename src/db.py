import logging
import os
import uuid

from settings import PG_CONN
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.base import Base
from models.image import Image
from models.user import User


class PanoDB:
    def __init__(self, connection_string=PG_CONN) -> None:
        self.engine = create_engine(connection_string, echo=False)
        Base.metadata.create_all(self.engine)

    def delete_image(self, id: uuid.UUID):
        with Session(self.engine) as session:
            result = session.query(Image).filter(Image.id == id).first()
            session.delete(result)
            session.commit()

    def get_image(self, id: uuid.UUID | None=None, original_filename: str | None=None) -> Image | None:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Image).filter_by(id=id) if id else select(Image).filter_by(original_filename=original_filename)
            row = session.execute(statement).first()
            if row:
                return row[0]
            #logging.warning(f"Could not find image. id={id}, original_filename={original_filename}")
            return None

    def get_images_by_install_id(
        self,
        install_id: uuid.UUID,
    ) -> list[Image]:
        images = []
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Image).filter_by(install_id=install_id)
            rows = session.execute(statement).fetchall()
            for r in rows:
                images.append(r[0])
        return images

    def get_images_by_node_id(
        self,
        node_id: uuid.UUID,
    ) -> list[Image]:
        images = []
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Image).filter_by(node_id=node_id)
            rows = session.execute(statement).fetchall()
            for r in rows:
                images.append(r[0])
        return images

    def get_image_by_signature(
        self,
        signature: str,
    ) -> list[Image]:
        images = []
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Image).filter_by(signature=signature)
            rows = session.execute(statement).fetchall()
            if len(rows) > 1:
                logging.warning("get_image_by_signature returned more than 1 image. There are probably duplicate images.")
            for r in rows:
                images.append(r[0])
        return images

    def save_image(self, image: Image):
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(image)
            session.commit()

    # Hmmmm this boilerplate/duplication could be fixed by Django.
    def get_user(self, id: str) -> User | None:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(User).filter_by(id=id)
            row = session.execute(statement).first()
            if row:
                return row[0]
            logging.warning(f"Could not find User with id {id}")
            return None

    def save_user(self, user: User):
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(user)
            session.commit()
