import logging
import os

from pymeshdb.api.buildings_api import BuildingsApi
from pymeshdb.api.installs_api import InstallsApi
from pymeshdb.api.nodes_api import NodesApi
from pymeshdb.api_client import ApiClient
from pymeshdb.configuration import Configuration
from pymeshdb.exceptions import NotFoundException
from pymeshdb.models.building import Building
from pymeshdb.models.install import Install
from pymeshdb.models.node import Node

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("pano.meshdb_client")


class MeshdbClient:
    def __init__(self):
        self.host = os.environ["MESHDB_ENDPOINT"]
        self.token = os.environ["MESHDB_TOKEN"]
        self.config = Configuration(
            host=self.host,
            access_token=self.token,
            api_key={"tokenAuth": self.token},
            api_key_prefix={"tokenAuth": "Token"},
        )
        self.c = ApiClient(self.config)
        self.b = BuildingsApi(self.c)
        self.i = InstallsApi(self.c)
        self.n = NodesApi(self.c)
        log.info("Initialized ")

    def get_install(self, install_number: int) -> Install | None:
        try:
            return self.i.api_v1_installs_retrieve2(install_number=install_number)
        except NotFoundException as e:
            logging.exception(e)
            return None

    def get_node(self, network_number: int) -> Node | None:
        try:
            return self.n.api_v1_nodes_retrieve2(network_number=network_number)
        except NotFoundException as e:
            logging.exception(e)
            return None

    def get_primary_building_for_install(self, install_number: int) -> Building | None:
        buildings = self.b.api_v1_buildings_lookup_list(install_number=install_number)
        if not buildings.results:
            return None
        first_building = buildings.results[0]
        return first_building

    def get_building_panos(self, id: str) -> list[str]:
        building_panos = []
        building = self.b.api_v1_buildings_retrieve(id=id)
        building_panos = building.panoramas
        return building_panos

    def save_panorama_on_building(self, id: str, panorama_link: str) -> None:
        building = self.b.api_v1_buildings_retrieve(id=id)
        building.panoramas.append(panorama_link)
        self.b.api_v1_buildings_update(id=id, building=building)
