import mysql.connector
from mysql.connector import errorcode
import re
import sys
import csv
import logging

logging.basicConfig(level = logging.DEBUG, format = "%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


if len(sys.argv) < 2:
    print("Error: input CSV file name containing products is required.")
    sys.exit(1)

input_file = sys.argv[1]
csv_fields = ["shahrvand_id", "raw_title", "title", "brand", "orig_price", "current_price",
          "weight_g", "volume_ml", "image_file", "keywords"]
csv_r = csv.DictReader(open(input_file, newline = ""), fieldnames = csv_fields)
next(csv_r)  # skip the header

try:
    cnx = mysql.connector.connect(option_files = "sql_conf.cnf")
    cursor = cnx.cursor(buffered = True)
    # TODO: insert the row if it doesn't exist
    for row in csv_r:
        new_price = row["orig_price"]
        if new_price != "":
            sh_id = row["shahrvand_id"]
            ## convert the price to int, skip if cannot
            try:
                new_price = int(new_price)
            except ValueError:
                logger.error(f"{sh_id}: {new_price} is not a valid price. Skipping row.")
                continue
            ## get the current price first, if any
            query = f"SELECT price FROM products WHERE shahrvand_id = '{sh_id}'"
            cursor.execute(query)
            result = cursor.fetchall()
            if cursor.rowcount == 0:
                logger.warning(f"The id {sh_id} was not found in DB. Is it a new product?")
            elif cursor.rowcount > 1:
                logger.warning(f"Too many products with the id {sh_id}. This is an error in DB. Skipping.")
            else: # rowcount == 1
                cur_price = result[0][0]
                if cur_price == new_price:
                    logger.info(f"{sh_id}: price {cur_price} is up-to-date.")
                else:
                    query = f"UPDATE products SET price = {new_price} WHERE shahrvand_id = '{sh_id}';"
                    cursor.execute(query)
                    logger.info(f"{sh_id}: price {cur_price} updated to {new_price}.")
    cnx.commit()
    
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        logger.error("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        logger.error("Database does not exist")
    else:
        logger.error(f"SQL Error {err.errno}: {err.msg}")
else:
    cnx.close()
