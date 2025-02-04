import logging
import os
import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.base import Base
from models.image import Image


class PanoDB:
    def __init__(self, connection_string=os.environ["PG_CONN"]) -> None:
        self.engine = create_engine(connection_string, echo=False)
        Base.metadata.create_all(self.engine)

    def delete_image(self, id: uuid.UUID):
        with Session(self.engine) as session:
            result = session.query(Image).filter(Image.id == id).first()
            session.delete(result)
            session.commit()

    def get_image(self, id: uuid.UUID) -> Image | None:
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Image).filter_by(id=id)
            row = session.execute(statement).first()
            if row:
                return row[0]
            logging.warning(f"Could not find image with id {id}")
            return None

    def get_images(self, install_number: int | None=None) -> list[Image]:
        images = []
        with Session(self.engine, expire_on_commit=False) as session:
            if install_number:
                statement = select(Image).filter_by(install_number=int(install_number))
            else:
                statement = select(Image)
            rows = session.execute(statement).fetchall()
            if rows:
                # FIXME: This is probably the wrong way to get this data
                for r in rows:
                    images.append(r[0])
        return images
