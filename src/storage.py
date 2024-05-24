from abc import ABC, abstractmethod

class Storage(ABC):
    # Upload images to this storage interface.
    # Takes a dictionary where the key is the file path to upload to, and the
    # value is the path of the file.
    @abstractmethod
    def upload_images(self, images: dict[str, str]) -> None:
        pass
