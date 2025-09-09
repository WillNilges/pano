from PIL import Image
from PIL.ExifTags import TAGS

def get_exif_data(path: str) -> dict[str, str]:
    print(f"Retrieving EXIF data for image: {path}")
    image = Image.open(path)
    exifdata = image.getexif()
    tags = {}

    for tagid in exifdata:
        tagname = TAGS.get(tagid, tagid)
        value = exifdata.get(tagid)
        tags[tagname] = value

    return tags


