from PIL import Image
from PIL.ExifTags import TAGS
import os
from datetime import datetime

dir = "/home/wilnil/Code/nycmeshnet/node-db/data/panoramas"

for filename in os.listdir(dir):
    try:
        print(f"--- {filename} ---")

        # open the image
        image = Image.open(f"{dir}/{filename}")

        # extracting the exif metadata
        exifdata = image.getexif()

        # looping through all the tags present in exifdata
        for tagid in exifdata:
            
            # getting the tag name instead of tag id
            tagname = TAGS.get(tagid, tagid)

            # passing the tagid to get its respective value
            value = exifdata.get(tagid)
          
            # printing the final result
            print(f"{tagname:25}: {value}")

            if value and tagname == "DateTime":
                date_time_obj = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                print(f"DATETIME: {date_time_obj}")

    except Exception:
        print("Couldn't get exif data.")
