from flask import Flask, render_template, request, url_for, flash, redirect
import sqlite3

app = Flask(__name__)

# if __name__ == "__main__":
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
        
        accounts = find_account(email, password)

        if accounts[0] == False and accounts[1] == False and accounts[2] == False and accounts[3] == False:
            error = "Invalid email or password."
        else:            
            count = 0
            for i in accounts:
                if i == True:
                    count += 1

            if count > 1:
                c=accounts[0]
                v=accounts[1]
                o=accounts[2]
                a=accounts[3]
            
            else:
                if accounts[0] == True:
                    return redirect(url_for('home', acc_type="customer", email=email))
                elif accounts[1] == True:
                    return redirect(url_for('home', acc_type="vendor", email=email))
                elif accounts[2] == True:
                    return redirect(url_for('home', acc_type="govt_official", email=email))
                elif accounts[3] == True:
                    return redirect(url_for('home', acc_type="db_admin", email=email))

    return render_template('login.html', error = error, c=c, v=v, o=o, a=a, email=email)

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

    return render_template('signup.html', error = error, success = success)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/home/<acc_type>/<email>')
def home(acc_type, email):
    home_url = "/home/" + acc_type + "/" + email
    return render_template('home.html', name=get_name(email,acc_type), home_url=home_url, acc_type=acc_type) 

def add_account(name, email, password, acc_type):
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
        else:
            cur.execute(
                '''
                insert into vendor values(?, ?, ?, null, null);
                ''', (name, email, password)
            )

        conn.commit()
        conn.close()
        to_return = True

    except:
        to_return = False

    return to_return

def find_account(email, password):
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

        to_return = ( bool(len(cus_acc)), bool(len(ven_acc)), bool(len(off_acc)), bool(len(adm_acc)))

    except:
        to_return = False

    return to_return

def get_name(email, acc_type):
    # acc_type = "customer", "vendor", "govt_official", or "db_admin"
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

