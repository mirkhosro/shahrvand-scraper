import mysql.connector
from mysql.connector import errorcode
import re


def fix_size(old_size):
    try:
        quantity, value = old_size.split(":")
        value = value.split(" ")[0]
        if quantity == "Wgt":
            return f"{value} گرمی"
        elif quantity == "Vol":
            return f"{value} میلی‌لیتری"
    except Exception as err:
        print(f"Parse error: {err}")
        return old_size
    
try:
    cnx = mysql.connector.connect(option_files = "sql_conf.cnf")
    cursor1 = cnx.cursor(buffered = True)
    cursor2 = cnx.cursor(buffered = True)
    
    query = "SELECT id, name, size FROM products WHERE shahrvand_id IS NOT NULL"
    cursor1.execute(query)
    for (pid, pname, psize) in cursor1.fetchall():
        print(f"{pid}, {pname}, {psize}")
        new_size = fix_size(psize)
        query = f"UPDATE products SET size = '{new_size}' WHERE id = {pid}"
        cursor2.execute(query)
    cnx.commit()
    
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(f"SQL Error {err.errno}: {err.msg}")
else:
    cnx.close()
