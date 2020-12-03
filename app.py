from flask import Flask, render_template, request, url_for, flash, redirect
import sqlite3
import sys      # for error catching
import datetime

from werkzeug.datastructures import RequestCacheControl

app = Flask(__name__)

if __name__ == '__main__':
    app.debug = True
    app.run()


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
        requestSellingPrice = float(request.form['sellingPrice'])
        requestQuantity = float(request.form['quantity'])

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
    # TODO
    error = ""
    success = ""

    if request.method == 'POST':
        pass

    return render_template('vendor_sales.html', home_url="/home/vendor/" + email, success=success, error=error)


@app.route('/home/vendor/<email>/promotions/', methods=['POST', 'GET'])
def vendor_promotions(email):
    
    error = ""
    success = ""
    validCustomerName = False
    if request.method == 'POST':
        request_customer_email = request.form['customer_email']
        request_details = request.form['details']
        request_ended = request.form['ended']

        if not((request_ended == 'Y') or (request_ended == 'N')):
            error = "Either enter a 'Y' or a 'N' in the last line"
            return render_template('vendor_promos.html', home_url="/home/vendor/<email>/promotions/" + email,    success=success, error=error)


        if request_ended == 'N':
            boolean_ended = 0  
            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()

            myQuery = """INSERT INTO promotions (customer_email,vendor_email,details,ended) VALUES ( ?,?,?,?)"""
            cur.execute(myQuery, (request_customer_email, email,request_details, boolean_ended))

            conn.commit()
            conn.close()
            success = "Promotion Added Successfully."
        
        if request_ended == 'Y':
            boolean_ended = 1
               
            
            all_customer_emails = get_All_customers_with_promotions()
            for currRow in all_customer_emails:
                tempName = currRow[0]
                if tempName == request_customer_email:
                    validCustomerName = True
                    break

            if  validCustomerName == True:
                conn = sqlite3.connect('IBDMS.db')
                cur = conn.cursor()

                myQuery = """UPDATE promotions SET ended = ? WHERE customer_email = ?"""
                cur.execute(myQuery, (boolean_ended, request_customer_email))

                conn.commit()
                conn.close()
                success = "Promotion Ended Successfully."
            else:
                error = "Customer not in the database"
                return render_template('vendor_promos.html', home_url="/home/vendor/<email>/promotions/" + email,    success=success, error=error)


       
      


        

    return render_template('vendor_promos.html', home_url="/home/vendor/" + email, success=success, error=error)


@app.route('/home/vendor/<email>/rent/', methods=['POST', 'GET'])
def vendor_rent(email):
    # TODO
    error = ""
    success = ""

    if request.method == 'POST':
        pass

    return render_template('vendor_rent.html', home_url="/home/vendor/" + email, success=success, error=error)

# Customer Screens:


@app.route('/home/customer/<email>/search_items/', methods=['POST', 'GET'])
def customer_search_items(email):
    # TODO
    error = ""
    success = ""

    if request.method == 'POST':
        pass

    return render_template('customer_search_item.html', home_url="/home/customer/" + email, success=success, error=error)


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

        if currentQuantityAvailable >= requestQuantity:  # if yes then give error that you can buy the requested quantity from the list of vendors selling this item with this much of current quanitty available
            error = "Requested quantity already available in Itwaar Bazaar !"
            quantityAvailable = True
            # get vendor details who is selling and what quantity
            # join overall_stock with vendor table on vendor_email where quantity > 0 and item_name = requestItem
            # extract vendor email,selling price,quantity,vendor name, shop number, start end times, location cordinates

            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()

            # myQuery = """ SELECT
            #                 vendor.vendor_name ,overall_stock.selling_price ,overall_stock.quantity,location.shop_number,location.x_coordinate,location.y_coordinate,time_slot.start_time,time_slot.end_time
            #             FROM
            #                 vendor cross join overall_stock ON vendor.vendor_email = overall_stock.vendor_email
            #                 cross join location ON  vendor.location_id = location.location_id
            #                 cross join time_slot ON location.time_slot_id = time_slot.time_slot_id
            #             where
            #                 overall_stock.quantity > 0 And overall_stock.item_name = ?"""

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


@app.route('/home/customer/<email>/cart/', methods=['POST', 'GET'])
def customer_cart(email):
    # TODO
    error = ""
    success = ""

    if request.method == 'POST':
        pass

    return render_template('customer_cart.html', home_url="/home/customer/" + email, success=success, error=error)

# Govt Official screens:


@app.route('/home/govt_official/<email>/add_time_location/', methods=['POST', 'GET'])
def add_time_location(email):
    error = ""
    success = ""

    if request.method == 'POST':
        shop_num = request.form['shop_num']
        st_time = request.form['st-time']
        en_time = request.form['en-time']

        start_time = datetime.datetime.strptime(
            st_time, "%H:%M")  # convert string to time
        end_time = datetime.datetime.strptime(en_time, "%H:%M")
        diff = end_time - start_time
        delta = diff.total_seconds()

        if (delta < 0):
            error = "End time cannot be before start time."
        else:
            error = insert_location_time(st_time, en_time, shop_num)
            if error == "":
                success = "Time and location added successfully"

    return render_template('official_add_time_location.html', home_url="/home/govt_official/" + email, success=success, error=error)


@app.route('/home/govt_official/<email>/remove_time_location/', methods=['POST', 'GET'])
def remove_time_location(email):
    error = ""
    success = ""

    list_of_shops_and_times = get_all_shops_with_slots()

    if request.method == 'POST':
        time_ID_to_remove = request.form['ID']

        exists = False
        for i in list_of_shops_and_times:
            for j in i:
                if j[0] == int(time_ID_to_remove):
                    exists = True
        if exists == False:
            error = "The entered ID does not exist. "
        else:
            query = "delete from location where time_slot_id = " + \
                str(time_ID_to_remove) + ";"
            col_names, q_result, error = execute_query(query)

            if error == "":
                success = "Shop given time slot with id " + \
                    str(time_ID_to_remove) + " removed successfully."
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
    # TODO
    return render_template('official_statistics.html', home_url="/home/govt_official/" + email)


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
        email = request.form['email']
        password = request.form['password']
        acc_type = "govt_official"

        added = add_account(name, email, password, acc_type)
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
        execute_query(query)

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


def insert_location_time(st_time, en_time, shop_num_str):
    """
    Inserts tuples into location and time_slot tables with the given values.

    @param st_time: string of HH:MM form in 24 hour time
    @param en_time: string of HH:MM form in 24 hour time
    @param shop_num: string containing shop num
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

        cur.execute(
            '''
        INSERT INTO location (location_id, shop_number, time_slot_id)
        VALUES (?, ?, ?);
        ''', (this_location_id, shop_num, this_time_slot_id)
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
        SELECT location.time_slot_id, shop_number, start_time, end_time
        FROM time_slot INNER JOIN location
        ON time_slot.time_slot_id = location.time_slot_id
        ORDER BY location.time_slot_id;
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


def get_All_customers_with_promotions():
    
    result = []

    conn = sqlite3.connect('IBDMS.db')
    cur = conn.cursor()
    cur.execute(
        '''
            select customer_email from promotions;
            '''
    )

    result = cur.fetchall()

    conn.commit()
    conn.close()

    return result

