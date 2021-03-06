from flask import Flask, render_template, request, url_for, redirect
import sqlite3
import sys      # for error catching
from datetime import datetime

app = Flask(__name__)

# if __name__ == '__main__':
#     app.debug = True
#     app.run()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login/', methods=['POST', 'GET'])
def login():
    error = ""
    email = ""

    # Used in case of mulitple accounts: c = customer, v = vendor ...:
    c = False
    v = False
    o = False
    a = False

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # to_return = ( bool(len(cus_acc)), bool(len(ven_acc)), bool(len(off_acc)), bool(len(adm_acc)))

        accounts = find_account(email, password)

        if accounts[0] == False and accounts[1] == False and accounts[2] == False and accounts[3] == False:
            error = "Invalid email or password."
        else:
            # count number of accounts with the given email and password

            count = 0
            for i in accounts:
                if i == True:
                    count += 1

            if count > 1:  # after setting these variables, reder template login.html again because the below else condition wont run as we have more than 1 account
                c = accounts[0]
                v = accounts[1]
                o = accounts[2]
                a = accounts[3]

            else:  # only 1 account present
                # redirect according to account type from : customer,vendor,govt official,db admin

                if accounts[0] == True:
                    return redirect(url_for('home', acc_type="customer", email=email))
                elif accounts[1] == True:
                    return redirect(url_for('home', acc_type="vendor", email=email))
                elif accounts[2] == True:
                    return redirect(url_for('home', acc_type="govt_official", email=email))
                elif accounts[3] == True:
                    return redirect(url_for('home', acc_type="db_admin", email=email))

    return render_template('login.html', error=error, c=c, v=v, o=o, a=a, email=email)


@app.route('/signup/', methods=['POST', 'GET'])
def signup():
    error = ""
    success = ""

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        re_password = request.form['re-password']
        acc_type = request.form['account-type']

        if password != re_password:
            error = "The two password inputs don't match. Enter Again."
        else:
            added = add_account(name, email, password, acc_type)
            if added == True:
                success = "Account Created Successfully. Please proceed to log in:"
            else:
                error = "There's already an account with this email."

    return render_template('signup.html', error=error, success=success)


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/home/<acc_type>/<email>')
def home(acc_type, email):
    # homepage for specific acc_type and email

    home_url = "/home/" + acc_type + "/" + email

    if acc_type == "customer":
        return render_template('home_customer.html', name=get_name(email, acc_type), home_url=home_url)
    elif acc_type == "vendor":
        return render_template('home_vendor.html', name=get_name(email, acc_type), home_url=home_url)
    elif acc_type == "govt_official":
        return render_template('home_official.html', name=get_name(email, acc_type), home_url=home_url)
    elif acc_type == "db_admin":
        return render_template('home_admin.html', name=get_name(email, acc_type), home_url=home_url)


# Vendor Screens:

def extractNameAndCategory(allItems):
    retList = []  # list of tuples where each tuple contains item_name, item_category

    for currRow in allItems:
        tempTuple = (currRow[0], currRow[1])
        retList.append(tempTuple)

    return retList


@app.route('/home/vendor/<email>/add_stock/', methods=['POST', 'GET'])
def vendor_stock_add(email):
    # The system asks the vendor to tell it item name that it wants to sell (all of possible items that can be sold will be shown)
    # Vendor inputs the item name,selling price,quantity
    # give an output message if price is OUT OF ALLOWED BOUND (but still accept the entry)

    error = ""
    success = ""

    allItems = getAllItems()
    # itemData = extractNameAndCategory(allItems)

    if request.method == 'POST':
        requestItemName = request.form['itemName']
        try:
            requestSellingPrice = float(request.form['sellingPrice'])

        except:
            error = "invalid selling price"
            return render_template('vendor_stock_add.html', home_url="/home/vendor/" + email, itemData=allItems, success=success, error=error)

        try:
            requestQuantity = float(request.form['quantity'])
        except:
            error = "invalid quantity"
            return render_template('vendor_stock_add.html', home_url="/home/vendor/" + email, itemData=allItems, success=success, error=error)

        if requestQuantity <= 0:
            error = "Quantity should be a positive value."
            return render_template('vendor_stock_add.html', home_url="/home/vendor/" + email, itemData=allItems, success=success, error=error)

        if requestSellingPrice <= 0:
            error = "Selling price should be a positive value."
            return render_template('vendor_stock_add.html', home_url="/home/vendor/" + email, itemData=allItems, success=success, error=error)

        validItemName = False
        matchedData = []  # will have one matched row from items table corresponding to the item name input by the user trying to add stock
        for currRow in allItems:
            tempName = currRow[0]
            if tempName == requestItemName:
                validItemName = True
                matchedData = currRow
                break

        # here
        if validItemName:  # item will be added. Either updated or newly added
            itemMinPrice = matchedData[3]
            itemMaxPrice = matchedData[2]

            if requestSellingPrice > itemMaxPrice:
                error = "Selling price is more than maximum allowed price. You will be fined !"
            if requestSellingPrice < itemMinPrice:
                error = "Selling price is less than minimum allowed price. You will be fined !"

            # check if this vendor is already selling the item or not?
            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()
            myQuery = """ SELECT EXISTS(SELECT 1 FROM overall_stock WHERE item_name= ? AND vendor_email = ?) """
            resultTuple = cur.execute(myQuery,
                                      (requestItemName, email)).fetchone()
            conn.commit()
            conn.close()

            alreadySelling = resultTuple[0]

            if alreadySelling == 1:  # need to update stock
                conn = sqlite3.connect('IBDMS.db')
                cur = conn.cursor()

                myQuery = """UPDATE overall_stock SET selling_price = ?, quantity = ? WHERE item_name = ? AND vendor_email = ? """
                cur.execute(myQuery,
                            (requestSellingPrice, requestQuantity, requestItemName, email))

                conn.commit()
                conn.close()

                success = "Stock Updated!"

            else:  # need to add stock

                conn = sqlite3.connect('IBDMS.db')
                cur = conn.cursor()
                myQuery = """INSERT INTO overall_stock (item_name,vendor_email,selling_price,quantity) VALUES ( ?,?,?,?)"""
                cur.execute(myQuery, (requestItemName, email,
                                      requestSellingPrice, requestQuantity))

                conn.commit()
                conn.close()
                success = "New Stock Added"

                # allItems = getAllItems()
                # itemData = extractNameAndCategory(allItems) #updated list of items

            return render_template('vendor_stock_add.html', home_url="/home/vendor/" + email, itemData=allItems, success=success, error=error)
        else:
            error = "This item cannot be sold. Item not present in list of allowed items that can be sold."
            return render_template('vendor_stock_add.html', home_url="/home/vendor/" + email, itemData=allItems, success=success, error=error)

    return render_template('vendor_stock_add.html', home_url="/home/vendor/" + email, itemData=allItems, success=success, error=error)


@app.route('/home/vendor/<email>/view_stock/', methods=['POST', 'GET'])
def vendor_stock_view(email):

    # error = ""
    # success = ""

    vendorName = get_name(email, "vendor")
    # get stock just join operation
    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    myQuery = """ SELECT item_name, item_category,selling_price,quantity,item_units 
                    FROM items natural join overall_stock
                    where overall_stock.vendor_email = ?"""
    cursor = cur.execute(myQuery, (email,))
    resultOfQuery = cursor.fetchall()
    # columnNames = list(map(lambda x: x[0], cursor.description))

    conn.commit()
    conn.close()

    return render_template('vendor_stock_view.html', home_url="/home/vendor/" + email, vendorStock=resultOfQuery, vendorName=vendorName)


@app.route('/home/vendor/<email>/remove_stock/', methods=['POST', 'GET'])
def vendor_stock_remove(email):

    error = ""
    success = ""

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    myQuery = """ SELECT vendor_name from vendor WHERE vendor_email = ? """
    resultTuple = cur.execute(myQuery, (email,)).fetchone()

    # get all item_names present in over my complete stock
    myQuery = """ SELECT item_name from overall_stock WHERE vendor_email = ? """
    resultList = cur.execute(myQuery, (email,)).fetchall()

    conn.commit()
    conn.close()
    myName = str(resultTuple[0]).title()

    # get name corresponding to email

    if request.method == 'POST':
        requestItemName = request.form['itemName']
        # check if item to delete exists in my stock or not
        validItemName = False
        for currRow in resultList:
            tempName = currRow[0]
            if tempName == requestItemName:
                validItemName = True
                break

        if validItemName:
            # delete stock
            # get updated items in my stock

            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()
            myQuery = """ DELETE from overall_stock WHERE vendor_email = ? AND item_name = ? """
            cur.execute(
                myQuery, (email, requestItemName)).fetchall()

            # get all item_names present in over my complete stock
            myQuery = """ SELECT item_name from overall_stock WHERE vendor_email = ? """
            resultList = cur.execute(myQuery, (email,)).fetchall()

            conn.commit()
            conn.close()
            success = "Deletion Successful."

        else:
            error = "Item does not exist in your stock."

    return render_template('vendor_stock_remove.html', home_url="/home/vendor/" + email, itemData=resultList, myName=myName, success=success, error=error)


@app.route('/home/vendor/<email>/view_sales/', methods=['POST', 'GET'])
def vendor_sales(email):

    error = ""
    success = ""
    query = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    cur.execute(''' select sales_id,item_name,quantity,price,discount,time_stamp,customer_email from sales where vendor_email = ?;''', (email, ))

    query = cur.fetchall()

    conn.commit()
    conn.close()
    if request.method == 'POST':
        pass

    return render_template('vendor_sales.html', home_url="/home/vendor/" + email, itemData=query, success=success, error=error)


@app.route('/home/vendor/<email>/promotions/', methods=['POST', 'GET'])
def vendor_promotions(email):

    error = ""
    success = ""
    validCustomerName = False
    valid_Customer_in_table = False
    promotions_data = get_All_promotion_details(email)

    if request.method == 'POST':

        # outputting all customer_ids relevant to this vendor and their relevant promotion details

        request_customer_email = request.form['customer_email']
        request_details = request.form['details']
        request_ended = request.form['ended']

        # if not((request_ended == 'Yes') or (request_ended == 'No')):
        #     error = "Either enter a \"Yes\" or a \"No\" in the last line"
        #     return render_template('vendor_promos.html', home_url="/home/vendor/<email>/promotions/" + email, itemData=promotions_data,   success=success, error=error)

        all_customer_emails = get_All_customers()
        for currRow in all_customer_emails:
            tempName = currRow[0]
            if tempName == request_customer_email:
                valid_Customer_in_table = True
                break

        if valid_Customer_in_table == False:
            error = "No Customer registered with this account"
            return render_template('vendor_promos.html', home_url="/home/vendor/" + email, itemData=promotions_data, success=success, error=error)

        all_customer_emails = get_All_customers_with_promotions(email)
        for currRow in all_customer_emails:
            tempName = currRow[0]
            if tempName == request_customer_email:
                validCustomerName = True
                break

        if validCustomerName == False:

            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()

            myQuery = """INSERT INTO promotions (customer_email,vendor_email,details,ended) VALUES ( ?,?,?,?)"""
            cur.execute(myQuery, (request_customer_email,
                                  email, request_details, request_ended))

            conn.commit()
            conn.close()
            success = "New Promotion Added."

        if validCustomerName == True:

            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()

            myQuery = """UPDATE promotions SET details = ? ,ended = ? WHERE customer_email = ?"""
            cur.execute(myQuery, (request_details,
                                  request_ended, request_customer_email))

            conn.commit()
            conn.close()
            success = "Promotion Updated."

    if(success != ""):
        promotions_data = get_All_promotion_details(email)

    return render_template('vendor_promos.html', home_url="/home/vendor/" + email, itemData=promotions_data, success=success, error=error)


@app.route('/home/vendor/<email>/rent/', methods=['POST', 'GET'])
def vendor_rent(email):
    success = ""
    error = ""
    current_rent_list, _ = get_current_rented_details(email)
    available_rent_list, _ = get_available_locations_times()

    if request.method == 'POST':
        location_ID_to_rent = request.form['ID']

        exists = False
        for i in available_rent_list:
            for j in i:
                if str(j) == str(location_ID_to_rent):
                    exists = True

        if exists == False:
            error = "The entered ID does not exist. "
        else:
            try:
                conn = sqlite3.connect('IBDMS.db')
                cur = conn.cursor()

                cur.execute(
                    '''
                UPDATE stall 
                SET rentee_email = ?
                WHERE location_id = ?;
                ''', (email, str(location_ID_to_rent)))

                conn.commit()
                conn.close()

            except:
                error = str(sys.exc_info()[1])

            if error == "":
                success = "Rented Successfully."
                current_rent_list, _ = get_current_rented_details(email)
                available_rent_list, _ = get_available_locations_times()

    return render_template('vendor_rent.html', home_url="/home/vendor/" + email, success=success, error=error, current_rent_list=current_rent_list, available_rent_list=available_rent_list)


@app.route('/home/vendor/<email>/add_sale/', methods=['POST', 'GET'])
def vendor_add_sale(email):

    error = ""
    success = ""
    valid_Stock = False
    valid_Customer_in_table = False
    stock = []
    global sale_id_final
    sale_id = []

    if request.method == 'POST':
        request_customer_email = request.form['customer_email']
        request_item_name = request.form['item_name']
        request_quantity = request.form['quantity']

        request_price = request.form['price']

        request_discount = request.form['discount']

        stock = get_stock(email, request_item_name)

        if not stock:
            error = "The Item is not in your stock"
            return render_template('vendor_add_sale.html', home_url="/home/vendor/" + email, success=success, error=error)

        if float(request_quantity) > stock[0][1]:
            error = "The Requested Quantity of the item is greater than the quantity of the item in your stock."
            return render_template('vendor_add_sale.html', home_url="/home/vendor/" + email, success=success, error=error)

        all_customer_emails = get_All_customers()
        for currRow in all_customer_emails:
            tempName = currRow[0]
            if tempName == request_customer_email:
                valid_Customer_in_table = True
                break

        if valid_Customer_in_table == False:
            error = "The Customer is not registered in the database"
            return render_template('vendor_add_sale.html', home_url="/home/vendor/" + email, success=success, error=error)

        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()

        myQuery1 = """UPDATE overall_stock SET quantity = ? WHERE vendor_email = ? and item_name = ?"""
        cur.execute(
            myQuery1, (stock[0][1] - float(request_quantity), email, request_item_name))

        conn.commit()
        conn.close()

        # compute Sales ID
        myQuery = "select COALESCE(MAX(sales_id), 0) from sales"
        _, tempResult, error = execute_query(myQuery)

        sale_id_final = tempResult[0][0] + 1

        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        myQuery3 = """INSERT INTO sales (sales_id, item_name, vendor_email, quantity, price, discount, time_stamp, customer_email) VALUES ( ?,?,?,?,?,?,?,?)"""
        cur.execute(myQuery3, (sale_id_final, request_item_name, email, request_quantity,
                               request_price, request_discount, dt_string, request_customer_email))

        conn.commit()
        conn.close()
        success = "New Sale Added."

    return render_template('vendor_add_sale.html', home_url="/home/vendor/" + email, success=success, error=error)


# Customer Screens:


@app.route('/home/customer/<email>/search_items/', methods=['POST', 'GET'])
def customer_search_items(email):

    error = ""
    success = ""

    result = []
    items = []
    items = getAllItems()
    if request.method == 'POST':

        requestItemName = request.form['itemName']

        validItemName = False
        for currRow in items:
            tempName = currRow[0]
            if tempName == requestItemName:
                validItemName = True
                break

        if validItemName == False:
            error = "No such item exists"
            return render_template('customer_search_item.html', home_url="/home/customer/" + email, success=success, error=error)

        if validItemName == True:

            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()

            myquery = """ select item_name, vendor_email, selling_price from overall_stock where item_name = ?; """
            cur.execute(myquery, (requestItemName,))
            result = cur.fetchall()
            conn.commit()
            conn.close()

    return render_template('customer_search_item.html', home_url="/home/customer/" + email, itemData=result, success=success, error=error)


@app.route('/home/customer/<email>/req_items/', methods=['POST', 'GET'])
def customer_req_items(email):
    error = ""
    success = ""

    if request.method == 'POST':
        requestItemName = request.form['itemName']
        requestQuantity = float(request.form['quantity'])

        # if item name not part of allowed items set by govt official then give error
        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()
        myQuery = """ SELECT EXISTS(SELECT 1 FROM items WHERE item_name= ?) """
        resultTuple = cur.execute(myQuery,
                                  (requestItemName,)).fetchone()
        conn.commit()
        conn.close()
        itemExists = resultTuple[0]
        if not itemExists:
            error = "Requested item not allowed by govt_official to be sold !"
            return render_template('customer_req_item.html', home_url="/home/customer/" + email, success=success, error=error)

        # if quantity <= 0 then give error
        if requestQuantity <= 0:
            error = "Requested Quantity Should Be Positive Integer."
            return render_template('customer_req_item.html', home_url="/home/customer/" + email, success=success, error=error)

        # check if the requested Quantity is available at itwaar bazaar even if sold by diff vendors with diff small quantities such that all add up to be  >= requestedQuantity
        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()
        myQuery = """ SELECT SUM(quantity) from overall_stock WHERE item_name= ? """
        resultTuple = cur.execute(myQuery, (requestItemName,)).fetchone()
        conn.commit()
        conn.close()
        currentQuantityAvailable = resultTuple[0]

        # if yes then give error that you can buy the requested quantity from the list of vendors selling this item with this much of current quanitty available
        if currentQuantityAvailable != None and currentQuantityAvailable >= requestQuantity:
            error = "Requested quantity already available in Itwaar Bazaar !"
            quantityAvailable = True
            # get vendor details who is selling and what quantity
            # join overall_stock with vendor table on vendor_email where quantity > 0 and item_name = requestItem
            # extract vendor email,selling price,quantity,vendor name, shop number, start end times, location cordinates

            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()

            myQuery = """ SELECT
                            vendor.vendor_name,vendor.vendor_email ,overall_stock.selling_price ,overall_stock.quantity
                        FROM
                            vendor inner join overall_stock ON vendor.vendor_email = overall_stock.vendor_email
                        where
                            overall_stock.quantity > 0 And overall_stock.item_name = ?"""

            cursor = cur.execute(myQuery,
                                 (requestItemName,))

            tableData = cursor.fetchall()
            # get table column names and remove _ from the columns
            tableColumns = list(map(lambda x: x[0], cursor.description))
            tableColumnsList = []
            for currItem in tableColumns:
                tempStr = str(currItem).replace("_", " ")
                tableColumnsList.append(tempStr)

            conn.commit()
            conn.close()
            return render_template('customer_req_item.html', home_url="/home/customer/" + email, success=success, error=error, quantityAvailable=quantityAvailable, tableData=tableData, tableColumnsList=tableColumnsList)

        else:  # final case: add to request table and give success message

            # compute reqID
            myQuery = "select COALESCE(MAX(request_id), 0) from requests"
            _, tempResult, error = execute_query(myQuery)
            requestID = tempResult[0][0] + 1

            # insert request
            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()

            myQuery = """ INSERT into requests values(?,?,?,?) """

            cur.execute(myQuery, (requestID, requestItemName,
                                  requestQuantity, False))
            conn.commit()
            conn.close()
            success = "Request Added Successfully !"

            return render_template('customer_req_item.html', home_url="/home/customer/" + email, success=success, error=error)

    return render_template('customer_req_item.html', home_url="/home/customer/" + email, success=success, error=error)


# Govt Official screens:


@app.route('/home/govt_official/<email>/add_time_location/', methods=['POST', 'GET'])
def add_time_location(email):
    error = ""
    success = ""

    if request.method == 'POST':
        shop_num = request.form['shop_num']
        st_time = request.form['st-time']
        en_time = request.form['en-time']
        rent = request.form['rent']

        start_time = datetime.strptime(
            st_time, "%H:%M")  # convert string to time
        end_time = datetime.strptime(en_time, "%H:%M")
        diff = end_time - start_time
        delta = diff.total_seconds()

        if (delta < 0):
            error = "End time cannot be before start time."
        else:
            error = insert_location_time(st_time, en_time, shop_num, rent)
            if error == "":
                success = "Time and location added successfully"

    return render_template('official_add_time_location.html', home_url="/home/govt_official/" + email, success=success, error=error)


@app.route('/home/govt_official/<email>/remove_time_location/', methods=['POST', 'GET'])
def remove_time_location(email):
    error = ""
    success = ""

    list_of_shops_and_times = get_all_shops_with_slots()

    if request.method == 'POST':
        loc_ID_to_remove = request.form['ID']

        exists = False
        for i in list_of_shops_and_times:
            for j in i:
                if j[0] == int(loc_ID_to_remove):
                    exists = True
        if exists == False:
            error = "The entered ID does not exist. "
        else:
            try:
                conn = sqlite3.connect('IBDMS.db')
                cur = conn.cursor()

                cur.execute(
                    "delete from location where location_id = ?;", (str(loc_ID_to_remove),))

                cur.execute("delete from stall where location_id = ?;",
                            (str(loc_ID_to_remove),))

                conn.commit()
                conn.close()

            except:
                error = str(sys.exc_info()[1])

            if error == "":
                success = "Shop given time slot with id " + \
                    str(loc_ID_to_remove) + " removed successfully."
                list_of_shops_and_times = get_all_shops_with_slots()
                return render_template('official_remove_time_location.html', home_url="/home/govt_official/" + email, list_of_shops_and_times=list_of_shops_and_times, error=error, success=success)

    return render_template('official_remove_time_location.html', home_url="/home/govt_official/" + email, list_of_shops_and_times=list_of_shops_and_times, error=error, success=success)


@app.route('/home/govt_official/<email>/price_bounds/', methods=['POST', 'GET'])
def price_bounds(email):
    # show all items in itwaar bazaar to the govt official sorted by name
    # take input from govt official for item_id so that it can be updated - item_id,min price, max price
    # if valid prices then execute the change to the underlying database and output success/failure message

    error = ""
    success = ""

    allItems = getAllItems()  # what would this return now?

    if request.method == 'POST':
        requestItemName = (request.form['itemName'])
        requestItemCat = request.form['itemCat']
        requestMinPrice = float(request.form['inputMinPrice'])
        requestMaxPrice = float(request.form['inputMaxPrice'])
        requestItemUnits = (request.form['itemUnits'])

        if (requestMinPrice) < 0:
            error = "Min Price cannot be negative!"
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)

        if (requestMaxPrice) < 0:
            error = "Max Price cannot be negative!"
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)
        if requestMaxPrice < requestMinPrice:
            error = "Max Price cannot be less than Min Price!"
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)

        # check if item exists i.e. itemName is valid
        itemExists = False
        for currRow in allItems:
            tempName = currRow[0]
            if tempName == requestItemName:
                itemExists = True
                # if requestItemCat != currRow[1]:
                #     error2 = "you input wrong category with an already existing item of another category"
                break
        # should also check if prices are floats/int??
        if itemExists:
            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()

            myQuery = """UPDATE items SET max_price = ?, min_price = ? WHERE item_name = ? """
            cur.execute(myQuery,
                        (requestMaxPrice, requestMinPrice, requestItemName))

            conn.commit()
            conn.close()
            # How do we print out success?????????????????????

            success = "Prices updated as requested."

            allItems = getAllItems()
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)

        else:  # else new item being added so insert into table

            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()
            myQuery = """INSERT INTO items (item_name,item_category,max_price,min_price,item_units) VALUES ( ?,?,?,?,?)"""
            cur.execute(myQuery, (requestItemName, requestItemCat,
                                  requestMaxPrice, requestMinPrice, requestItemUnits))

            conn.commit()
            conn.close()
            # How do we print out success?????????????????????
            success = "New Item added as requested."

            allItems = getAllItems()
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)

    return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)


@app.route('/home/govt_official/<email>/statistics/', methods=['POST', 'GET'])
def statistics(email):
    error = ""
    success = ""
    query = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    cur.execute(
        ''' select item_name, avg(selling_price), sum(quantity), count(item_name) from overall_stock group by item_name''')

    query = cur.fetchall()

    conn.commit()
    conn.close()

    return render_template('official_statistics.html', home_url="/home/govt_official/" + email, itemData=query, error=error, success=success)


@app.route('/home/govt_official/<email>/fines/', methods=['POST', 'GET'])
def impose_fines(email):
    email = str(email).lower()

    error = ""
    success = ""

    finesQuery = "select * from fines"
    # resultOfQuery is a list containing all tuples (comma separated) corresponding to our query.
    _, resultOfQuery, error = execute_query(finesQuery)

    if request.method == 'POST':
        # requestFineId = int(request.form['fineID'])
        requestFineId = 0
        requestVendorEmail = request.form['vendorEmail']
        requestVendorEmail = str(requestVendorEmail).lower()
        requestFineDetails = request.form['details']
        govt_off_email = email
        finePaid = False

        # check if valid vendor email

        allVendorEmails = all_accounts("vendor")
        validVendorEmail = False
        for currRow in allVendorEmails:
            tempEmail = currRow[0]
            if tempEmail == requestVendorEmail:
                validVendorEmail = True
                break

        if not validVendorEmail:
            error = "There does not exist a vendor with the given Email ID."
            return render_template('official_fines.html', home_url="/home/govt_official/" + email, finesData=resultOfQuery, error=error, success=success)

        # compute fineID
        myQuery = "select COALESCE(MAX(fine_id), 0) from fines"
        _, tempResult, error = execute_query(myQuery)
        requestFineId = tempResult[0][0] + 1

        # at this point vendor email ID  is valid that was input by the user so we run the query and add fine

        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()
        cur.execute(
            '''
            insert into fines values(?, ?, ?,?,?);
            ''', (requestFineId, govt_off_email, requestVendorEmail, requestFineDetails, finePaid)
        )
        conn.commit()
        conn.close()
        # get updated fines table
        error2 = ""
        finesQuery = "select * from fines"
        # resultOfQuery is a list containing all tuples (comma separated) corresponding to our query.
        _, resultOfQuery, error2 = execute_query(finesQuery)
        success = "Fine Added Successfully !"
        return render_template('official_fines.html', home_url="/home/govt_official/" + email, finesData=resultOfQuery, error=error, success=success)

    return render_template('official_fines.html', home_url="/home/govt_official/" + email, finesData=resultOfQuery, error=error, success=success)


# DB admin screens:


@app.route('/home/db_admin/<email>/add_officials/', methods=['POST', 'GET'])
def add_officials(email):
    error = ""
    success = ""

    # accounts_list = all_official_accounts()
    if request.method == 'POST':
        name = request.form['name']
        email_off = request.form['email']
        password = request.form['password']
        acc_type = "govt_official"

        added = add_account(name, email_off, password, acc_type)
        if added == True:
            success = "Account Added Successfully."
        else:
            error = "There's already an account with this email."

    return render_template('admin_add_officials.html', home_url="/home/db_admin/" + email, error=error, success=success)


@app.route('/home/db_admin/<email>/remove_officials/', methods=['POST', 'GET'])
def remove_officials(email):
    email_to_remove = ""
    message = ""
    accounts_list = all_accounts("govt_official")
    if request.method == 'POST':
        for i in accounts_list:
            for j in i:
                if str(j) in request.form:
                    email_to_remove = str(j)

        query = 'delete from government_officials where govt_off_email = "' + \
            email_to_remove + '";'

        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()

        cur.execute(query)

        conn.commit()
        conn.close()

        message = 'Account with email "' + email_to_remove + '" has been removed.'
        accounts_list = all_accounts("govt_official")
        return render_template('admin_remove_officials.html', home_url="/home/db_admin/" + email, accounts_list=accounts_list, message=message)

    return render_template('admin_remove_officials.html', home_url="/home/db_admin/" + email, accounts_list=accounts_list, message=message)


@app.route('/home/db_admin/<email>/query/', methods=['POST', 'GET'])
def query_form(email):
    query = ""
    query_result = ""
    col_names = ""
    error = ""

    if request.method == 'POST':
        query = request.form['query']
        (col_names, query_result, error) = execute_query(query)

        for i in range(len(col_names)):
            col_names[i] = col_names[i].title()

    return render_template('admin_query.html', home_url="/home/db_admin/" + email, query_result=query_result, error=error, query=query, col_names=col_names)


def add_account(name, email, password, acc_type):
    """
    Adds an account in the database with the given parameters.

    @param name: string - the name of the account
    @param email: string - the email of the account 
    @param password: string - the password of the account 
    @param acc_type: string - account type, one of the following: "customer", "vendor", or "govt_official"
    @return: bool - True if the account has been added successfully. False otherwise.
    """
    to_return = False
    email = str(email).lower()
    try:
        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()

        if acc_type == "customer":
            cur.execute(
                '''
                insert into customer values(?, ?, ?);
                ''', (name, email, password)
            )
        elif acc_type == "vendor":
            cur.execute(
                '''
                insert into vendor values(?, ?, ?, null, null);
                ''', (name, email, password)
            )
        elif acc_type == "govt_official":
            cur.execute(
                '''
                insert into government_officials values(?, ?, ?);
                ''', (name, email, password)
            )

        # db admin accounts can only be manually added by another db admin

        conn.commit()
        conn.close()
        to_return = True

    except:
        to_return = False

    return to_return


def find_account(email, password):
    """
    Finds whether an account exists (for all 4 actors) in the database with the given parameters.

    @param email: string - the email of the account 
    @param password: string - the password of the account 
    @return: bool False if an error occurs. Otherwise, a tuple of whether the account exists for the four agents in the following order: customer, vendor, official, admin. e.g. (True, False, True, False) 
    """
    email = str(email).lower()
    try:
        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()

        cur.execute(
            '''
            select customer_email from customer where customer_email = ? and customer_pass = ?;
            ''', (email, password)
        )
        cus_acc = cur.fetchall()

        cur.execute(
            '''
            select vendor_email from vendor where vendor_email = ? and vendor_pass = ?;
            ''', (email, password)
        )
        ven_acc = cur.fetchall()

        cur.execute(
            '''
            select govt_off_email from government_officials where govt_off_email = ? and govt_off_pass = ?;
            ''', (email, password)
        )
        off_acc = cur.fetchall()

        cur.execute(
            '''
            select admin_email from db_admins where admin_email = ? and admin_password = ?;
            ''', (email, password)
        )
        adm_acc = cur.fetchall()

        conn.commit()
        conn.close()

        to_return = (bool(len(cus_acc)), bool(len(ven_acc)),
                     bool(len(off_acc)), bool(len(adm_acc)))

    except:
        to_return = False

    return to_return


def get_name(email, acc_type):
    # acc_type = "customer", "vendor", "govt_official", or "db_admin"
    """
    Queries the database for the given account type and email and returns the name of the account. The account must exist in the database so might want to use find_account() before calling this function.

    @param email: string - the email of the account 
    @param acc_type: string - account type, one of the following: "customer", "vendor", "govt_official", or "db_admin"
    @return: string - the name of the account.
    """
    email = str(email).lower()

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    if acc_type == "customer":
        cur.execute(
            '''
        select customer_name from customer where customer_email = ?;
        ''', (email,)
        )
    elif acc_type == "vendor":
        cur.execute(
            '''
        select vendor_name from vendor where vendor_email = ?;
        ''', (email,)
        )
    elif acc_type == "govt_official":
        cur.execute(
            '''
        select govt_off_name from government_officials where govt_off_email = ?;
        ''', (email,)
        )
    elif acc_type == "db_admin":
        cur.execute(
            '''
        select admin_name from db_admins where admin_email = ?;
        ''', (email,)
        )

    query_result = cur.fetchall()

    conn.commit()
    conn.close()

    return query_result[0][0].title()


def execute_query(query):
    """
    Executes the query given in the parameter in the database.

    @param query: string - the query to be executed.
    @:return: (result, error) - Result is list containing tuples for every result line. Error is a string which is empty if no error.
    """
    error = ""
    result = []
    names = []

    try:
        conn = sqlite3.connect('IBDMS.db', detect_types=sqlite3.PARSE_COLNAMES)
        cur = conn.cursor()

        cur.execute(query)
        names = list(map(lambda x: x[0], cur.description))
        result = cur.fetchall()

        conn.commit()
        conn.close()

    except:
        error = str(sys.exc_info()[1])

    return (names, result, error)


def all_accounts(acc_type):
    """
    Returns a list containing emails of all the accounts of the given type in the database.

    @param acc_type: string - account type, one of the following: "customer", "vendor", or "govt_official"
    @:return: list containing strings - Result is list containing strings containing email for every such account.
    """
    result = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()

    if acc_type == "customer":
        cur.execute(
            '''
            select customer_email from customer;
            '''
        )
    elif acc_type == "vendor":
        cur.execute(
            '''
            select vendor_email from vendor;
            '''
        )
    elif acc_type == "govt_official":
        cur.execute(
            '''
            select govt_off_email from government_officials;
            '''
        )

    result = cur.fetchall()

    conn.commit()
    conn.close()

    return result


def insert_location_time(st_time, en_time, shop_num_str, rent):
    """
    Inserts tuples into location and time_slot tables with the given values.

    @param st_time: string of HH:MM form in 24 hour time
    @param en_time: string of HH:MM form in 24 hour time
    @param shop_num: string containing shop num
    @param rent: int containing shop num
    @:return: error: a string containing error returned (if any)
    """

    shop_num = int(shop_num_str)
    query_result = []
    error = ""

    try:
        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()

        cur.execute(
            '''
        SELECT MAX(location_id)
        FROM location;
        '''
        )
        this_location_id = cur.fetchall()
        if this_location_id[0][0] == None:
            this_location_id = 0
        else:
            this_location_id = int(this_location_id[0][0]) + 1

        time_slot_already_exists = False
        cur.execute(
            '''
            SELECT time_slot_id
            FROM time_slot
            WHERE start_time = ? AND end_time = ? ;
            ''', (st_time, en_time)
        )
        existing_time_id = cur.fetchall()
        if len(existing_time_id) == 0:
            time_slot_already_exists = False
        else:
            time_slot_already_exists = True

        if time_slot_already_exists == False:
            cur.execute(
                '''
            SELECT MAX(time_slot_id)
            FROM time_slot;
            '''
            )
            this_time_slot_id = cur.fetchall()
            if this_time_slot_id[0][0] == None:
                this_time_slot_id = 0
            else:
                this_time_slot_id = int(this_time_slot_id[0][0]) + 1
            cur.execute(
                '''
            INSERT INTO time_slot (time_slot_id, start_time, end_time)
            VALUES (?, ?, ?);
            ''', (this_time_slot_id, st_time, en_time)
            )
            query_result.append(cur.fetchall())
        else:
            # get the relavant time slot id from the time slot table
            this_time_slot_id = existing_time_id[0][0]

        cur.execute(
            '''
        INSERT INTO location (location_id, shop_number, time_slot_id)
        VALUES (?, ?, ?);
        ''', (this_location_id, shop_num, this_time_slot_id)
        )

        query_result.append(cur.fetchall())

        cur.execute(
            '''
        INSERT INTO stall (location_id, rent, time_slot_id)
        VALUES (?, ?, ?) ;
        ''', (this_location_id, rent, this_time_slot_id)
        )

        query_result.append(cur.fetchall())

        conn.commit()
        conn.close()
    except:
        error = str(sys.exc_info()[1])

    return error


def get_all_shops_with_slots():
    """
    returns a list of all shops with their time slots.

    @:return: (list, error): list of of tuples containing the attributes. error stores a string of any error returned
    """

    query_result = []
    error = ""

    try:
        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()

        cur.execute(
            '''
        SELECT location.location_id, shop_number, start_time, end_time, rent, rentee_email
        FROM time_slot INNER JOIN location INNER JOIN stall
        ON time_slot.time_slot_id = location.time_slot_id and stall.location_id = location.location_id
        ORDER BY location.location_id;
        '''
        )

        query_result = cur.fetchall()

        conn.commit()
        conn.close()
    except:
        error = str(sys.exc_info()[1])

    return (query_result, error)


def getAllItems():
    """
    returns a list of all items.

    @:return: list: list of all items
    """
    result = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    cur.execute(
        '''
            select * from items;
            '''
    )

    result = cur.fetchall()

    conn.commit()
    conn.close()

    return result


def get_All_customers_with_promotions(email):

    result = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    cur.execute(
        '''
            select customer_email from promotions where vendor_email = ?;''', (email,)

    )

    result = cur.fetchall()

    conn.commit()
    conn.close()

    return result

# gives only those promotions for vendors that are linked to the given account


def get_All_promotion_details(email):
    result = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    cur.execute('''select customer_name, customer_email, details, ended from customer natural left outer join promotions where vendor_email = ?;''', (email,))

    result = cur.fetchall()

    conn.commit()
    conn.close()

    return result


def get_All_customers():
    result = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    cur.execute(
        '''
            select customer_email from customer;
            '''
    )

    result = cur.fetchall()

    conn.commit()
    conn.close()

    return result


def get_current_rented_details(email):
    """
    returns a list of all items.
    @param: email: the email of the rentee to find the currently rented locations and times

    @:return: list: list of all the rented locations and times for the given email
    """

    error = ""
    result = []

    try:
        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()

        cur.execute(
            '''
        SELECT shop_number, start_time, end_time, rent
        FROM time_slot INNER JOIN location INNER JOIN stall
        ON time_slot.time_slot_id = location.time_slot_id and stall.location_id = location.location_id and rentee_email = ?
        ORDER BY shop_number;
        ''', (email,))

        result = cur.fetchall()

        conn.commit()
        conn.close()

    except:
        error = str(sys.exc_info()[1])

    return result, error


def get_available_locations_times():
    """
    returns a list of all available locations and time for rent.

    @:return: list: list of all the location_ids available.
    """

    error = ""
    result = []

    try:
        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()

        cur.execute(
            '''
        SELECT location.location_id, shop_number, start_time, end_time, rent
        FROM time_slot INNER JOIN location INNER JOIN stall
        ON time_slot.time_slot_id = location.time_slot_id and stall.location_id = location.location_id and rentee_email IS NULL
        ORDER BY location.location_id;
        ''')

        result = cur.fetchall()

        conn.commit()
        conn.close()

    except:
        error = str(sys.exc_info()[1])

    return result, error


def get_stock(email, item_name):
    result = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    myQuery = """select item_name, quantity from overall_stock where vendor_email = ? and item_name = ?;"""
    #myQuery = """SELECT item_name, quantity (sales_id, item_name, vendor_email, quantity, price, discount, time_stamp, customer_email) VALUES ( ?,?,?,?,?,?,?)"""

    cur.execute(myQuery, (email, item_name))

    result = cur.fetchall()

    conn.commit()
    conn.close()

    return result
