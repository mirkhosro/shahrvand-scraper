from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
import logging
import sys
import csv
import re

# set up logging
logging.basicConfig(#filename = "log.txt",
                    level = logging.DEBUG, format = "%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


## load the page
logger.info(f"{__name__} started.")

if len(sys.argv) < 2:
    print("Input file path is required as the first argument.")
    sys.exit(1)
elif len(sys.argv) < 3:
    print("Output file path is required as the second argument.")
    sys.exit(1)

input_file_path = sys.argv[1]
output_file_path = sys.argv[2]
with open(input_file_path) as f:
    html_doc = f.read()

## setup Beautiful Soup
logger.info("Parsing page...")
soup = BeautifulSoup(html_doc, "html.parser")

## setup output file
try:
    csvfile = open(output_file_path, "w", newline = "")
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["title", "sh_id"])
except Exception as e:
    logger.error(e)
    sys.exit(1)


## actually parse html and save into csv
brand_tags = soup.find_all("input", attrs = {"name" : "brand"})
for tag in brand_tags:
    brand_title = tag["data-title"].replace("\u200c", " ").replace("  ", " ").strip()
    brand_id = tag["id"].strip()
    csv_writer.writerow([brand_title, brand_id])


    
csvfile.close()

logger.info("Done.")


