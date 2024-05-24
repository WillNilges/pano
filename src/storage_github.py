import logging
import os
from github import Github

# Authentication is defined via github.Auth
from github import Auth

log = logging.getLogger("pano.storage_github")

# Confusingly, I don't know if I want to make this implement the storage interface yet. This might be fucked.
class StorageGit():
    def __init__(self):
        access_token = os.environ["PANO_GITHUB_TOKEN"]
        self.auth = Auth.Token(access_token)
                
        # Public Web Github
        self.client = Github(auth=self.auth)
        
        log.info(self.client.get_user().get_repo("nycmeshnet/node-db"))

        for repo in self.client.get_user().get_repos():
            print(repo)
        self.client.close()



