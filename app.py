from flask import Flask, render_template, request, url_for, flash, redirect
import sqlite3
import sys      # for error catching

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
        return "TODO"
    elif acc_type == "vendor":
        return "TODO"
    elif acc_type == "govt_official":
        return render_template('home_official.html', name=get_name(email, acc_type), home_url=home_url)
    elif acc_type == "db_admin":
        return render_template('home_admin.html', name=get_name(email, acc_type), home_url=home_url)


@app.route('/home/db_admin/<email>/query/', methods=['POST', 'GET'])
def query_form(email):
    query_result = ""
    error = ""
    if request.method == 'POST':
        query = request.form['query']
        (query_result, error) = execute_query(query)

    return render_template('admin_query.html', home_url="/home/db_admin/" + email, query_result=query_result, error=error)

# Customer Screens:
# TODO

# Vendor Screens:
# TODO

# Govt Official screens:


@app.route('/home/govt_official/<email>/add_time_location/', methods=['POST', 'GET'])
def add_time_location(email):
    # TODO
    return render_template('official_add_time_location.html', home_url="/home/govt_official/" + email)


@app.route('/home/govt_official/<email>/remove_time_location/', methods=['POST', 'GET'])
def remove_time_location(email):
    # TODO
    return render_template('official_remove_time_location.html', home_url="/home/govt_official/" + email)


@app.route('/home/govt_official/<email>/price_bounds/', methods=['POST', 'GET'])
def price_bounds(email):
    # show all items in itwaar bazaar to the govt official sorted by name
    # take input from govt official for item_id so that it can be updated - item_id,min price, max price
    # if valid prices then execute the change to the underlying database and output success/failure message

    error = ""
    success = ""

    allItems = getAllItems()

    if request.method == 'POST':
        requestItemID = int(request.form['itemId'])
        requestMinPrice = float(request.form['inputMinPrice'])
        requestMaxPrice = float(request.form['inputMaxPrice'])

        if (requestMinPrice) < 0:
            error = "Min Price cannot be negative!"
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)

        if (requestMaxPrice) < 0:
            error = "Max Price cannot be negative!"
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)
        if requestMaxPrice < requestMinPrice:
            error = "Max Price cannot be less than Min Price!"
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)

        # check if item id is valid
        itemExists = False
        for currRow in allItems:
            tempID = currRow[0]
            if tempID == requestItemID:
                itemExists = True
                break
        # should also check if prices are floats/int??
        if itemExists:
            conn = sqlite3.connect('IBDMS.db')
            cur = conn.cursor()
            conn.execute('UPDATE items SET max_price = ?, min_price = ?'
                         ' WHERE item_id = ?',
                         (requestMaxPrice, requestMinPrice, requestItemID))

            conn.commit()
            conn.close()
            # How do we print out success?????????????????????
            success = "Prices updated as requested."

            allItems = getAllItems()
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)

        else:
            error = "incorrect item ID"

            # error = str(requestMinPrice) + " " + str(requestMaxPrice)
            return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)

    return render_template('official_prices.html', home_url="/home/govt_official/" + email, allItems=allItems, error=error, success=success)


def getAllItems():
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


@app.route('/home/govt_official/<email>/statistics/', methods=['POST', 'GET'])
def statistics(email):
    # TODO
    return render_template('official_statistics.html', home_url="/home/govt_official/" + email)


@app.route('/home/govt_official/<email>/fines/', methods=['POST', 'GET'])
def impose_fines(email):
    email = str(email).lower()

    error = ""
    success = ""

    finesQuery = "select fine_id , vendor_email from fines"
    # resultOfQuery is a list containing all tuples (comma separated) corresponding to our query.
    resultOfQuery, error = execute_query(finesQuery)

    if request.method == 'POST':
        requestFineId = int(request.form['fineID'])
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

        # check if Fine id is valid (should not exist)
        fineIDExists = False
        for currRow in resultOfQuery:
            tempID = currRow[0]
            if tempID == requestFineId:
                fineIDExists = True
                break

        if fineIDExists:
            error = "There exists a fine with same fine ID. Retry with a new one"
            return render_template('official_fines.html', home_url="/home/govt_official/" + email, finesData=resultOfQuery, error=error, success=success)

        # at this point vendor email ID and fineId that were input by the user are correct so we run the query and add fine

        conn = sqlite3.connect('IBDMS.db')
        cur = conn.cursor()
        cur.execute(
            '''
            insert into fines values(?, ?, ?,?,?);
            ''', (requestFineId, govt_off_email, requestVendorEmail, requestFineDetails, finePaid)
        )
        conn.commit()
        conn.close()

        error2 = ""
        finesQuery = "select fine_id , vendor_email from fines"
        # resultOfQuery is a list containing all tuples (comma separated) corresponding to our query.
        resultOfQuery, error2 = execute_query(finesQuery)
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

    return render_template('admin_remove_officials.html', home_url="/home/db_admin/" + email, accounts_list=accounts_list, message=message)


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
    try:
        conn = sqlite3.connect('IBDMS.db', detect_types=sqlite3.PARSE_COLNAMES)
        cur = conn.cursor()

        # cur.execute('''.headers on''')
        cur.execute(query)
        result = cur.fetchall()

        conn.commit()
        conn.close()

    except:
        error = str(sys.exc_info()[1])

    return (result, error)


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
