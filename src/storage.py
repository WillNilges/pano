from abc import ABC, abstractmethod


class Storage(ABC):
    # Upload images to this storage interface.
    # Takes a dictionary where the key is the file path to upload to, and the
    # value is the path of the file.
    @abstractmethod
    def upload_objects(self, objects: dict[str, str]) -> None:
        pass

    # Downloads images from this storage interface
    # Takes a list of file paths, and returns the path/url where they are stored.
    @abstractmethod
    def download_objects(self, objects: list[str]) -> list[str]:
        pass

    # Returns a list of all the images this storage knows about
    # Returns a list of paths or URLs
    # Example: ["/path/to/a", "/path/to/b", "/path/to/c", ...]
    @abstractmethod
    def list_all_objects(self, install_number: int) -> list[str]:
        pass
