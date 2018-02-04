import requests
from requests.exceptions import RequestException
import logging
import sys
import csv
import time
from pathlib import Path


logging.basicConfig(level = logging.DEBUG, format = "%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


logger.info(f"{sys.argv[0]} app started...")

## arg 1 is URL to download from, arg 2 is saved file path
if len(sys.argv) < 2:
    logger.error("Shahrvand download URL is required.")
    sys.exit(1)
elif len(sys.argv) < 3:
    logger.error("Output folder is required.")
    sys.exit(1)
    
base_url = sys.argv[1]
out_folder_path = Path(sys.argv[2])
out_folder_path.mkdir(exist_ok = True)
page_size = 500
max_pages = 10000 / page_size
sleep_time = 2
page = 1
finished = False

logger.info(f"Downloading from {base_url}")
while not finished:
    url = base_url + f"&pagesize[]={page_size}&page[]={page}"
    try:
        r = requests.get(url)
        out_file_path = out_folder_path / f"page_{page}.html" 
        with out_file_path.open("w") as f:
            f.write(r.text)
            f.close()
        logger.info(f"Downloaded page {page}.")
        page = page + 1
        if page > max_pages:
            finished = True
        if "نتیجه ای یافت نشد" in r.text:
            finished = True
    except Exception as ex:
        logger.error(ex)
        
    time.sleep(sleep_time)
        
logger.info("Done.")


    
