import uuid
from pymeshdb.models.building import Building


SAMPLE_BUILDING = Building(
    id="one",
    installs=[],
    bin=0,
    street_address="888 Fake Street",
    city="New York",
    state="New York",
    zip_code="10001",
    address_truth_sources=[],
    latitude=0,
    longitude=0,
)

SAMPLE_IMAGE_PATH = "./src/tests/sample_images/pano.png"
SAMPLE_IMAGE_PATH_2 = "./src/tests/sample_images/logo.jpg"

UUID_1 = uuid.uuid4()
UUID_2 = uuid.uuid4()
