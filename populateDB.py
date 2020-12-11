# Reading an excel file using Python
from struct import pack_into
from werkzeug.datastructures import iter_multi_items
import xlrd
import sqlite3
import sys      # for error catching
import datetime
from datetime import datetime
import random
# generate random integer values
from random import seed
from random import randint

seed(1)

govt_table = {}
customer_table = {}
time_slot_table = {}
items_data = {}
# each row of location table is stored in here as a string comma separated
# location_data = []
location_ids = []
vendor_data = {}
vendor_emails = []
fine_id_list = []

stall_info = []


def populateGovtOfficial():

    # Give the location of the file
    path = ("allData.xlsx")

    # To open Workbook
    inputWorkbook = xlrd.open_workbook(path)
    govtSheet = inputWorkbook.sheet_by_index(0)

    totalRows = govtSheet.nrows
    totalColumns = govtSheet.ncols
    # populate complete sheet into a table
    for i in range(totalColumns):
        currColumnName = govtSheet.cell_value(0, i)
        govt_table[currColumnName] = []

        for j in range(1, totalRows):
            columnValue = govtSheet.cell_value(j, i)
            govt_table[currColumnName].append(columnValue)

    # extract data from sheet and insert into database via query
    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    for i in range(1, totalRows):
        # extract i-th row
        name = govtSheet.cell_value(i, 0)
        email = govtSheet.cell_value(i, 1)
        password = govtSheet.cell_value(i, 2)

        myQuery = """INSERT INTO government_officials (govt_off_name,govt_off_email,govt_off_pass) VALUES ( ?,?,?)"""
        cur.execute(myQuery, (name, email, password))

    conn.commit()
    conn.close()

    # print(govt_table)


def populateCustomer():

    # Give the location of the file
    path = ("allData.xlsx")

    # To open Workbook
    inputWorkbook = xlrd.open_workbook(path)
    customerSheet = inputWorkbook.sheet_by_index(1)

    totalRows = customerSheet.nrows
    totalColumns = customerSheet.ncols
    # populate complete sheet into a table
    for i in range(totalColumns):
        currColumnName = customerSheet.cell_value(0, i)
        customer_table[currColumnName] = []

        for j in range(1, totalRows):
            columnValue = customerSheet.cell_value(j, i)
            customer_table[currColumnName].append(columnValue)

    # extract data from sheet and insert into database via query
    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    for i in range(1, totalRows):
        # extract i-th row
        name = customerSheet.cell_value(i, 0)
        email = customerSheet.cell_value(i, 1)
        password = customerSheet.cell_value(i, 2)

        myQuery = """INSERT INTO customer (customer_name,customer_email,customer_pass) VALUES ( ?,?,?)"""
        cur.execute(myQuery, (name, email, password))

    conn.commit()
    conn.close()

    # print(customer_table)


def populateTimeSlots():

    # hard code data into time slot table

    time_slot_table["time_slot_id"] = []
    time_slot_table["start_time"] = []
    time_slot_table["end_time"] = []

    # insert into database via query
    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    for i in range(2):  # ONLY TWO TIMESLOTS
        # extract i-th row
        time_slot_id = i+1
        if i == 0:

            start_time = "06:00"
            end_time = "14:00"

            myQuery = """INSERT into time_slot (time_slot_id,start_time,end_time) VALUES ( ?,?,?)"""
            cur.execute(myQuery, (time_slot_id, start_time, end_time))

            time_slot_table["time_slot_id"].append(time_slot_id)
            time_slot_table["start_time"].append(start_time)
            time_slot_table["end_time"].append(end_time)

        if i == 1:

            start_time = "14:00"
            end_time = "22:00"

            myQuery = """INSERT into time_slot (time_slot_id,start_time,end_time) VALUES ( ?,?,?)"""

            cur.execute(myQuery, (time_slot_id, start_time, end_time))

            time_slot_table["time_slot_id"].append(time_slot_id)
            time_slot_table["start_time"].append(start_time)
            time_slot_table["end_time"].append(end_time)

    conn.commit()
    conn.close()

    # print(time_slot_table)


def randomNumGenerator(min, max):
    # seed random number generator

    return randint(min, max)


def populateItemsTable():

    # Give the location of the file
    path = ("allData.xlsx")

    # To open Workbook
    inputWorkbook = xlrd.open_workbook(path)
    itemSheet = inputWorkbook.sheet_by_index(3)

    totalRows = itemSheet.nrows
    totalColumns = itemSheet.ncols

    categoryToUnits = {}
    columnNameList = itemSheet.row_values(0)
    unitsList = ["per kg", "per kg", "per litre", "per kg", "per packet", ""]
    for i in range(len(columnNameList)):
        categoryToUnits[columnNameList[i]] = unitsList[i]

    # populate complete sheet into a table
    for i in range(totalColumns):
        currColumnName = itemSheet.cell_value(0, i)
        items_data[currColumnName] = []
        tempList = itemSheet.col_values(i)
        lastFilledRow = 0
        for element in tempList:
            if element == '':
                break
            else:
                lastFilledRow += 1

        items_data[currColumnName] = tempList[1:lastFilledRow]
        # print(items_data[currColumnName])

    # extract data from sheet and insert into database via query
    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    for columnName in columnNameList:
        # list of all items in the given category
        columnList = items_data[columnName]
        # unit corresponding to the given category
        categoryUnit = categoryToUnits[columnName]

        for item in columnList:

            item_name = item
            item_category = columnName
            min_price = randomNumGenerator(50, 200)
            max_price = randomNumGenerator(min_price, 1000)
            item_units = categoryUnit

            myQuery = """INSERT INTO items (item_name,item_category,max_price,min_price,item_units) VALUES ( ?,?,?,?,?)"""
            cur.execute(myQuery, (item_name, item_category,
                                  max_price, min_price, item_units))

    conn.commit()
    conn.close()


def listToCommaString(list):
    return ",".join([str(x) for x in list])


def populateLocationTable():

    totalLocations = 200
    # extract data from sheet and insert into database via query
    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    for i in range(totalLocations):
        id = i+1
        location_ids.append(id)
        shopID1 = 0
        if i < 100:
            shopID1 = i+1

            time_slot_id = 1

            myQuery = """INSERT INTO location (location_id,shop_number,time_slot_id) VALUES ( ?,?,?)"""
            cur.execute(myQuery, (id, shopID1, time_slot_id))
        else:
            shopID1 = (i+1) - 100

            time_slot_id = 2

            # print(id, shopID1, time_slot_id)
            myQuery = """INSERT INTO location (location_id,shop_number,time_slot_id) VALUES ( ?,?,?)"""
            cur.execute(myQuery, (id, shopID1, time_slot_id))

    conn.commit()
    conn.close()


def populateVendorTable():

    # Give the location of the file
    path = ("allData.xlsx")

    # To open Workbook
    inputWorkbook = xlrd.open_workbook(path)
    vendorSheet = inputWorkbook.sheet_by_index(4)

    totalRows = vendorSheet.nrows
    totalColumns = vendorSheet.ncols
    # populate complete sheet into a table
    for i in range(totalColumns):
        currColumnName = vendorSheet.cell_value(0, i)
        vendor_data[currColumnName] = []

        for j in range(1, totalRows):
            columnValue = vendorSheet.cell_value(j, i)
            vendor_data[currColumnName].append(columnValue)

    # vendor emails
    vendor_emails = vendorSheet.col_values(1, 1)

    # extract data from sheet and insert into database via query
    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    # add 200-20 vendors
    for i in range(1, totalRows - 20):
        # extract i-th row
        name = vendorSheet.cell_value(i, 0)
        email = vendorSheet.cell_value(i, 1)
        password = vendorSheet.cell_value(i, 2)
        loc_id = i
        time_slot_id = 1

        if i > 100:
            time_slot_id = 2

        # print(name, email, password, loc_id, time_slot_id)
        myQuery = """INSERT INTO vendor (vendor_name,vendor_email,vendor_pass,location_id,time_slot_id) VALUES ( ?,?,?,?,?)"""
        cur.execute(myQuery, (name, email, password, loc_id, time_slot_id))

    conn.commit()
    conn.close()


def populateFinesTable():

    # Give the location of the file
    path = ("allData.xlsx")

    # To open Workbook
    inputWorkbook = xlrd.open_workbook(path)
    govtSheet = inputWorkbook.sheet_by_index(0)
    gov_emails_list = govtSheet.col_values(1, 1)

    vendorSheet = inputWorkbook.sheet_by_index(4)
    vendor_emails_list = vendorSheet.col_values(1, 1)

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    # generate 10 fines
    for i in range(1, 11):
        fineID = i
        fine_id_list.append(fineID)
        gov_email = gov_emails_list[i-1]
        ven_email = vendor_emails_list[i*2]
        details = "fine due in month number " + str(randomNumGenerator(1, 12))
        paid = False

        # print(fineID, gov_email, ven_email, details, paid)
        myQuery = """INSERT INTO fines (fine_id,govt_off_email,vendor_email,details,paid) VALUES ( ?,?,?,?,?)"""
        cur.execute(myQuery, (fineID, gov_email, ven_email, details, paid))

    conn.commit()
    conn.close()

# 140*40 tuples


def populatePromotions():
    # 140 of the 200 vendors will each give promotion to 40 customers
    # Give the location of the file
    path = ("allData.xlsx")

    # To open Workbook
    inputWorkbook = xlrd.open_workbook(path)

    vendorSheet = inputWorkbook.sheet_by_index(4)
    vendor_emails_list = vendorSheet.col_values(1, 1)

    customerSheet = inputWorkbook.sheet_by_index(1)
    cus_email_list = customerSheet.col_values(1, 1)

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    for i in range(140):
        curr_ven = vendor_emails_list[i]
        for j in range(40):
            curr_cus = cus_email_list[j]
            details = "% discount on all items: " + \
                str(5 * randomNumGenerator(1, 10))
            ended = ""
            if j % 2 == 0:
                ended = "Yes"
            else:
                ended = "No"

            # print(curr_cus, curr_ven, details, ended)

            myQuery = """INSERT INTO promotions (customer_email,vendor_email,details,ended) VALUES ( ?,?,?,?)"""
            cur.execute(myQuery, (curr_cus, curr_ven, details, ended))

    conn.commit()
    conn.close()


def populateStall():

    totalLocations = 150

    # use i for vendor email indexing
    # Give the location of the file
    path = ("allData.xlsx")

    # To open Workbook
    inputWorkbook = xlrd.open_workbook(path)
    vendorSheet = inputWorkbook.sheet_by_index(4)
    vendor_emails_list = vendorSheet.col_values(1, 1)

    # extract data from sheet and insert into database via query
    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    for i in range(totalLocations):
        curr_ven = vendor_emails_list[i]
        curr_rent = 5 * randomNumGenerator(1000, 2000)
        id = i+1

        if i < 100:

            time_slot_id = 1

            stall_info.append([time_slot_id, id])

            # print(time_slot_id, id, curr_rent, curr_ven)
            myQuery = """INSERT INTO stall (time_slot_id,location_id,rent,rentee_email) VALUES ( ?,?,?,?)"""
            cur.execute(myQuery, (time_slot_id, id, curr_rent, curr_ven))
        else:

            time_slot_id = 2

            stall_info.append([time_slot_id, id])

            # print(time_slot_id, id, curr_rent, curr_ven)
            myQuery = """INSERT INTO stall (time_slot_id,location_id,rent,rentee_email) VALUES ( ?,?,?,?)"""
            cur.execute(myQuery, (time_slot_id, id, curr_rent, curr_ven))

    conn.commit()
    conn.close()

#  150 vendors each with around 40 items = 6000 tuples


def populateOverallStock():
    path = ("allData.xlsx")

    inputWorkbook = xlrd.open_workbook(path)

    overallStockSheet = inputWorkbook.sheet_by_index(5)
    ven_email_list = overallStockSheet.col_values(1, 1)
    itemsList = overallStockSheet.col_values(0, 1)

    lastRow = 0
    for elem in itemsList:
        if elem == '':
            break
        lastRow += 1

    itemsList = itemsList[:lastRow]
    numOfItems = len(itemsList)

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    for j in range(150):

        vendor = ven_email_list[j]
        indexListItems = random.sample(range(0, numOfItems-1), numOfItems - 30)

        # print(vendor)
        # print(indexListItems)

        for i in range(len(indexListItems)):
            item_to_sell = itemsList[indexListItems[i]]
            sell_price = 5 * randomNumGenerator(10, 200)
            quantity = 5 * randomNumGenerator(0, 100)

            # print(item_to_sell, vendor, sell_price, quantity)

            myQuery = """INSERT INTO overall_stock (item_name,vendor_email,selling_price,quantity) VALUES ( ?,?,?,?)"""
            cur.execute(myQuery, (item_to_sell, vendor, sell_price, quantity))

    # print(itemsList)
    # print(numOfItems)

    conn.commit()
    conn.close()


def main():

    populateGovtOfficial()
    populateCustomer()
    populateTimeSlots()
    populateItemsTable()
    populateLocationTable()
    # requests table added from website
    populateVendorTable()
    populateFinesTable()
    populatePromotions()
    populateStall()
    populateOverallStock()
    # sales table added from website


if __name__ == "__main__":
    main()
