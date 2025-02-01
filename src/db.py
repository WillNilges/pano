from datetime import datetime
import logging
import os
import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.base import Base
from models.image import Image, ImageCategory


class PanoDB:
    def __init__(self) -> None:
        self.engine = create_engine(os.environ['PG_CONN'], echo=True)
        Base.metadata.create_all(self.engine)

    def create_image(self, install_number: int, category: ImageCategory) -> Image:
        # TODO: Figure out order
        # DO I want to order per category or overall? Probably both?

        #install_images = self.get_images(install_number)

        image_uuid = uuid.uuid4()

        with Session(self.engine, expire_on_commit=False) as session:
            # Get last ordered image
            next_order = 0
            statement = select(Image).filter_by(install_number=install_number).order_by(Image.order.desc())
            row = session.execute(statement).first()
            if row:
                next_order = row[0].order + 1

            i = Image(
                id=image_uuid,
                timestamp=datetime.now(),
                install_number=install_number,
                order=next_order,
                category=category,
            )
            session.add_all([i])
            session.commit()
            return i

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
