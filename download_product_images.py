import requests
from requests.exceptions import RequestException
import logging
import sys
import csv
import time
from pathlib import Path

def download_to_folder(row: list, output_folder: Path):
    saved_file_path = output_folder / ("sh_" + row[col_id_index] + ".jpg")
    image_name = row[col_image_index]
    if len(image_name) > 14:
        image_name = image_name[:13] + "(1).jpg"
    image_url = "http://www.shahrvand.ir/upload/product/" + image_name
    if saved_file_path.exists():
        logger.info(f"File {saved_file_path} already exists. Skipping.")
    else:
        time.sleep(2)
        r = requests.get(image_url)
        r.raise_for_status()
        with saved_file_path.open("wb") as f:
            f.write(r.content)
        logger.info(f"File {saved_file_path} downloaded and saved.")
        ## wait 2 second before downloading the next
    

logging.basicConfig(#filename = "log.txt",
                    level = logging.DEBUG, format = "%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


logger.info(f"{sys.argv[0]} app started...")
## look for the csv file name to read file names to download from
if len(sys.argv) < 2:
    logger.error("Input CSV file path is required.")
    sys.exit(1)
elif len(sys.argv) < 3:
    logger.error("Output folder name is required.")
    sys.exit(1)

in_file_path = sys.argv[1]
output_folder = Path(sys.argv[2])
output_folder.mkdir(exist_ok = True)
#os.makedirs(output_folder, exist_ok = True)
try:
    with open(in_file_path, newline = "") as in_file:
        csv_r = csv.reader(in_file)
        ## discard header
        header = next(csv_r)
        col_id_index = header.index("shahrvand_id")
        col_image_index = header.index("image_file")
        for row in csv_r:
            try:
                download_to_folder(row, output_folder)
            except Exception as ex:
                logger.error(f"Couldn't download or save image for id {row[0]}: {ex}")

except Exception as ex:
    logger.error(ex)
    sys.exit(1)

    

    
