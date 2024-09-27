from abc import ABC, abstractmethod

class Storage(ABC):
    # Upload images to this storage interface.
    # Takes a dictionary where the key is the file path to upload to, and the
    # value is the path of the file.
    @abstractmethod
    def upload_images(self, images: dict[str, str]) -> None:
        pass

    # Downloads images from this storage interface
    # Takes a list of file paths, and returns the path/url where they are stored.
    @abstractmethod
    def download_images(self, images: list[str]) -> list[str]:
        pass

    # Returns a list of all the images this storage knows about
    # Returns a list of paths or URLs
    # Example: ["/path/to/a", "/path/to/b", "/path/to/c", ...]
    @abstractmethod
    def list_all_images(self) -> list[str]:
        pass

    # Returns a list of all the images this storage knows about, while also
    # handling any differences in abstraction *cough* github *cough*
    # Returns a dictionary mapping Install Numbers(?) to a list of paths
    # Example: {
    # 1001: ["/path/to/a", "/path/to/b", ...],
    # 1002: ["/path/to/a", "/path/to/b", ...]
    # }
    #@abstractmethod
    #def get_inventory(self) -> dict[int, list[str]]:
    #    pass
