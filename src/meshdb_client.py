import logging
import os

import pymeshdb
from pymeshdb.models.install import Install

log = logging.getLogger("pano.meshdb_client")

class MeshdbClient():        
    def __init__(self):
        self.config = pymeshdb.Configuration(
            host=os.environ["PANO_MESHDB_ENDPOINT"],
            access_token=os.environ["PANO_MESHDB_TOKEN"],

            api_key={'tokenAuth': os.environ["PANO_MESHDB_TOKEN"]},
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

    # FIXME (willnilges): This is yak shaving 
    def map_installs_to_nns(self) -> dict[int, list[int]]:
        mapped_installs = {}
        installs = self.get_all_installs()

        # XXX(willnilges): I don't believe that this API response will ever
        # map an install to more than one NN, so this should be fine.
        for install in installs:
            mapped_installs[install.install_number] = install.network_number

        return mapped_installs
