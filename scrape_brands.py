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


# start scraping
## load the page
logger.info("App started.")
page_url = "http://www.shahrvand.ir/fa/product/cat/1.html"
try:
    logger.info("Downloading page...")
    html_doc = requests.get(page_url).text
    # with open("brands.html") as f:
    #     html_doc = f.read()
    logger.info("Page downloaded.")
except RequestException as ex:
    logger.error(ex)
    sys.exit(1)

## setup Beautiful Soup
logger.info("Parsing page...")
soup = BeautifulSoup(html_doc, "html.parser")

## setup output file
try:
    csvfile = open("../data/shahrvand_brands.csv", "w", newline = "")
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


