import logging
import os

import pymeshdb
from pymeshdb.api.buildings_api import BuildingsApi
from pymeshdb.api.installs_api import InstallsApi 
from pymeshdb.api_client import ApiClient
from pymeshdb.configuration import Configuration
from pymeshdb.models.building import Building
from pymeshdb.models.install import Install

log = logging.getLogger("pano.meshdb_client")


class MeshdbClient:
    def __init__(self):
        self.config = Configuration(
            host=os.environ["MESHDB_ENDPOINT"],
            access_token=os.environ["MESHDB_TOKEN"],
            api_key={"tokenAuth": os.environ["MESHDB_TOKEN"]},
            api_key_prefix={"tokenAuth": "Token"},
        )
        self.c = ApiClient(self.config)
        self.b = BuildingsApi(self.c)
        self.i = InstallsApi(self.c)

    def get_install(self, install_number: int) -> Install | None:
        installs = self.i.api_v1_installs_lookup_list(install_number=install_number)
        if not installs.results:
            return None
        return installs[0]

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
