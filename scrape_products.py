from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
import logging
import sys
import csv
import re
import time
from pathlib import Path

zwnj_ptrn = re.compile("\u200c+")
white_ptrn = re.compile("[\u200c\u200f ]+")
size_ptrn = re.compile("\d+([\.،]\d+)? (گرمی|عددی|میلی لیتری|کیلویی|عدد|رول|برگ|میلی|سانتی متری) ")

# set up logging
logging.basicConfig(#filename = "log.txt",
                    level = logging.DEBUG, format = "%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

## helper functions
def get_id(tag):
    # e.g. <div class = "product product1495">
    # product id is included in the second value of class atribute
    # so look for the second item (index 1) and after the word 'product' (length 7)
    return(tag["class"][1][7:])

    
def clean_price(price_text):
    "Cleans price tags by removing currency units and thousand separators."
    if price_text:
        return price_text.string.replace("تومان", "").replace(",", "").strip()
    else:
        return ""


def normalize_text(some_text):
    ## replace extra white spaces and ZWNJ with just one space
    some_text = white_ptrn.sub(" ", some_text)
    ## remove accents
    some_text = re.sub("[\u064e-\u0651]", "", some_text)
    ## use Persian letters
    some_text = some_text.replace("ي", "ی").replace("ك", "ک")
    return some_text.strip()


def clean_title(a_title):
    "Remove unnecessary stuff from a product title."
    clean_title = normalize_text(a_title)
    clean_title = re.sub("-", " ", clean_title)
    clean_title = size_ptrn.sub("", clean_title)
    return clean_title.strip()


def fix_brand(brand, all_brands):
    fixed = None
    if fixed is None:
        for good_brand in all_brands:
            if good_brand.replace(" ", "") == brand.replace(" ", ""):
                fixed = good_brand
    if fixed is None:
        for good_brand in all_brands:
            if brand in good_brand.split(" "):
                fixed = good_brand
                #logger.debug(f"{brand} found in {good_brand}")
    if fixed is None:
        for good_brand in all_brands:
            if brand.replace(" ", "") in good_brand.replace(" ", ""):
                fixed = good_brand
                #logger.debug(f"{brand} found in {good_brand}")
    return fixed

    
def get_brand(title: str, all_brands: set) -> str:
    brand = title.split(" ")[-1]
    brand = normalize_text(brand)
    if all_brands is None or brand in all_brands:
        return brand
    else:
        fixed = fix_brand(brand, all_brands)
        if fixed is None:
            logger.info(f"The brand {brand} not found in brands.")
            return brand
        else:
            #logger.info(f"The brand {brand} replaced with {fixed}.")
            return fixed


def get_image_file_name(tag):
    image_file = tag.find("img")["src"]
    m = re.search(".*/(.+\.jpg)$", image_file)
    return m.group(1)


def get_keywords(title, brand):
    filtered = title
    ## remove these words
    filtered = re.sub(" (ها|ای|با|و|در|شده|های|کننده|دهنده|حاوی|دارای|کن) ", " ", filtered)
    ## removed quanitities
    filtered = re.sub("\d+([\.،]\d+)? \w+ ", "", filtered)
    ## remove numbers
    filtered = re.sub("\d+([\.،]\d+)?", "", filtered)
    ## remove symobs
    filtered = re.sub("[-()*+]", "", filtered)
    ## remove brand (to be replaced later)
    filtered = filtered.replace(brand, "").strip()
    all_keywords = filtered.split(" ")
    all_keywords.append(brand)
    ## use only the the first and last words as keywords
    keywords = all_keywords[0:2]
    if len(all_keywords) > 3:
        keywords.append(all_keywords[-2])
    if len(all_keywords) > 2:
        keywords.append(all_keywords[-1])
    return keywords


def augment_keywords_old(keywords):
    """Augment keywords to generate all possible combinations."""
    stack = []
    full_kw = []
    def gen_for(k : int):
        stack.append(keywords[k])
        full_kw.append(" ".join(reversed(stack)))
        if (k > 0):
            for i in reversed(range(0, k)):
                gen_for(i)
        stack.pop()

    gen_for(len(keywords) - 1)
    return("-".join(full_kw))

def augment_keywords(keywords):
    """Augment keywords to generate all possible combinations."""
    ## brand is always one keyword
    full_kw = [keywords[-1]]
    ## stack dynamically changes
    stack = [keywords[0]]
    def gen_for(k : int):
        stack.insert(1, keywords[k])
        full_kw.append(" ".join(stack))
        if (k > 1):
            for i in reversed(range(1, k)):
                gen_for(i)
        stack.pop(1)

    gen_for(len(keywords) - 1)
    return("-".join(full_kw))


def parsePage(soup, csv_w):
    ## actually parse html and save into csv
    tags = soup("div", class_ = "product")
    for tag in tags:
        shahrvand_id = get_id(tag)
        if (shahrvand_id in id_set):
            logger.warning(f"The id {shahrvand_id} was already seen. Skipping.")
            continue
        id_set.add(shahrvand_id)
        url_tag = tag.find("a", class_ = "title")
        raw_title = url_tag.string.strip()
        title = clean_title(raw_title)
        current_price = clean_price(tag.find("div", class_ = "new_price"))
        orig_price = clean_price(tag.find("div", class_ = "old_price").span)
        if orig_price == "":
            orig_price = current_price
        brand = get_brand(raw_title, all_brands)        
        keywords = get_keywords(title, brand)
        full_keywords = augment_keywords(keywords)
        image_file = get_image_file_name(tag)
        row_dict = {"shahrvand_id": shahrvand_id, "raw_title": raw_title, "title": title,
                    "brand": brand, "orig_price": orig_price, "current_price": current_price,
                    "image_file": image_file, "keywords": full_keywords}
        desc = tag.find("div", class_ = "description")
        for attr in desc("li"):
            spans = [s.string.strip() for s in attr.find_all("span") if s.string is not None]
            if len(spans) > 1:
                key = spans[0]
                value = spans[1]
                value = "|".join([s.strip() for s in value.split("|")])
                if (key == "وزن (گرم) :"):
                    key = "weight_g"
                if (key == "حجم (میلی‌لیتر) :"):
                    key = "volume_ml"
                # if (key == "نوع :"):
                #     key = "type"            
                # if (key == "کشور تولیدکننده :" or key == "کشور تولید کننده :" or key == "کشور سازنده :"):
                #     key = "made_in"
                # if (key == "طعم :"):
                #     key = "flavor"
                # if (key == "تعداد در بسته :" or key == "تعداد :"):
                #     key = "count"
                row_dict[key] = value
        csv_writer.writerow(row_dict)


logger.info(f"{sys.argv[0]} app started...")
## parse command line arguments
if len(sys.argv) < 2:
    print("Input file path is required as the first argument.")
    sys.exit(1)
elif len(sys.argv) < 3:
    print("Output file path is required as the second argument.")
    sys.exit(1)
elif len(sys.argv) < 4:
    logger.warning("Supplying a brands.csv file as a third argument is highly recommended. Using plain extracted brands instead.")
    brands_file_path = None
else:
    brands_file_path = sys.argv[3]

## determine if a folder is given for input or a file
input_file_path = Path(sys.argv[1])
if input_file_path.is_dir():
    html_file_list = input_file_path.glob("*.html")
if input_file_path.is_file():
    html_file_list = [input_file_path]


logger.info("Loading files...")
## setup output file
output_file_path = sys.argv[2]
try:
    csvfile = open(output_file_path, "w", newline = "")
    fields = ["shahrvand_id", "raw_title", "title", "brand", "orig_price", "current_price",
              "weight_g", "volume_ml", "image_file", "keywords"]
    csv_writer = csv.DictWriter(csvfile, fieldnames = fields, extrasaction = "ignore")
    csv_writer.writeheader()
except Exception as e:
    logger.error(e)
    sys.exit(1)

## load brands
all_brands = None
if brands_file_path is not None:
    all_brands = set()
    with open(brands_file_path, newline = "") as f:
        csv_r = csv.reader(f)
        header = next(csv_r)
        title_index = header.index("title")
        for row in csv_r:
            all_brands.add(normalize_text(row[title_index]))

## set of id so we won't read duplicate ids
id_set = set()
## load the page or html file
for file_path in html_file_list:
    with file_path.open() as f:
        html_doc = f.read()
        ## setup Beautiful Soup
        logger.info(f"Parsing HTML page {file_path.name}")
        soup = BeautifulSoup(html_doc, "html.parser")
        logger.info("Processing data...")
        row_dict = parsePage(soup, csv_writer)
    
csvfile.close()

logger.info("Done.")


