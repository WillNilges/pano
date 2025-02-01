from datetime import datetime
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.base import Base
from models.image import Image, ImageCategory


class PanoDB:
    def __init__(self) -> None:
        self.engine = create_engine(os.environ['PG_CONN'], echo=True)
        Base.metadata.create_all(self.engine)

    def create_image(self, install_number: int, category: ImageCategory) -> uuid.UUID:
        # TODO: Figure out order
        # DO I want to order per category or overall? Probably both?

        #install_images = self.get_images(install_number)

        image_uuid = uuid.uuid4()

        with Session(self.engine) as session:
            i = Image(
                id=image_uuid,
                timestamp=datetime.now(),
                install_number=install_number,
                order=0, # TODO: Figure out order lol. I think a new Model might be warranted
                category=category,
            )
            session.add_all([i])
            session.commit()

        return image_uuid

    def delete_image(self, id: uuid.UUID): 
        with Session(self.engine) as session:
            i = 

    def get_images(self, install_number):
        with Session(self.engine) as session: 
            """
            q = session.query(Image, Image.id, user_alias)

            # this expression:
            chom = q.column_descriptions
            """

            result = session.query(Image).filter(Image.install_number == install_number).all()
            return result
