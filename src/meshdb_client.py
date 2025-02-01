import logging
import os

import pymeshdb
from pymeshdb.models.install import Install
from pymeshdb.models.building import Building

log = logging.getLogger("pano.meshdb_client")


class MeshdbClient:
    def __init__(self):
        self.config = pymeshdb.Configuration(
            host=os.environ["MESHDB_ENDPOINT"],
            access_token=os.environ["MESHDB_TOKEN"],
            api_key={"tokenAuth": os.environ["MESHDB_TOKEN"]},
            api_key_prefix={"tokenAuth": "Token"},
        )

    def get_primary_building_for_install(self, install_number: int) -> Building | None:
        with pymeshdb.ApiClient(self.config) as api_client:
            building_api = pymeshdb.BuildingsApi(api_client)
            buildings = building_api.api_v1_buildings_lookup_list(
                install_number=install_number
            )
            if not buildings.results:
                return None
            first_building = buildings.results[0]
            return first_building

    def get_building_panos(self, id: str) -> list[str]:
        building_panos = []
        with pymeshdb.ApiClient(self.config) as api_client:
            api = pymeshdb.BuildingsApi(api_client)
            building = api.api_v1_buildings_retrieve(id=id)
            building_panos = building.panoramas
        return building_panos

    def save_panorama_on_building(self, id: str, panorama_link: str) -> None:
        with pymeshdb.ApiClient(self.config) as api_client:
            api = pymeshdb.BuildingsApi(api_client)
            building = api.api_v1_buildings_retrieve(id=id)
            building.panoramas.append(panorama_link)
            api.api_v1_buildings_update(id=id, building=building)
