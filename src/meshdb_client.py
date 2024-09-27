import logging
import os

import pymeshdb
from pymeshdb.models.install import Install

log = logging.getLogger("pano.meshdb_client")

class MeshdbClient():        
    def __init__(self):
        self.config = pymeshdb.Configuration(
            host=os.environ["MESHDB_ENDPOINT"],
            access_token=os.environ["MESHDB_TOKEN"],

            api_key={'tokenAuth': os.environ["MESHDB_TOKEN"]},
            api_key_prefix={'tokenAuth': 'Token'},
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
                page = 1 # A page number within the paginated result set. Starts at 1 for some reason.
                while another_page:
                    log.info(f"Getting page {page}...")
                    api_response = api_instance.api_v1_installs_list(page=page)
                    installs.append(api_response.results)
                    if api_response.next:
                        page += 1
                    else:
                        another_page = False
            except Exception:
                log.exception("Exception when calling InstallsApi->api_v1_installs_list.")

        return installs

    def get_building_panos(self, building_id: str) -> list[str]:
        building_panos = []
        with pymeshdb.ApiClient(self.config) as api_client:
            # Create an instance of the API class
            api = pymeshdb.BuildingsApi(api_client)
            building = api.api_v1_buildings_retrieve(id=building_id)
            building_panos = building.panoramas
        return building_panos

