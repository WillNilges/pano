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

    # Naively gets all installs, one page at a time.
    # There's gotta be a faster way. It would be dumb, but maybe we could
    # parallelize them.
    def get_all_installs(self) -> list[Install]:
        installs = []
        # Enter a context with an instance of the API client
        with pymeshdb.ApiClient(self.config) as api_client:
            # Create an instance of the API class
            api_instance = pymeshdb.InstallsApi(api_client)

            try:
                another_page = True
                page = 1  # A page number within the paginated result set. Starts at 1 for some reason.
                while another_page:
                    log.info(f"Getting page {page}...")
                    api_response = api_instance.api_v1_installs_list(page=page)
                    installs.append(api_response.results)
                    if api_response.next:
                        page += 1
                    else:
                        another_page = False
            except Exception:
                log.exception(
                    "Exception when calling InstallsApi->api_v1_installs_list."
                )

        return installs

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
