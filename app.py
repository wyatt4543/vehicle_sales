from flask import Flask, render_template, jsonify, request, redirect, flash, session, url_for
import mysql.connector
import bcrypt
import smtplib
from datetime import date

app = Flask(__name__)

config = {
    'host': 'fplg27.h.filess.io',
    'user': 'VehicleSales_selection',
    'password': '3964f4ec577fce81b6857f4807a2dee1e5e94ad3',
    'port': '61032',
    'database': 'VehicleSales_selection'
}

@app.route('/')
def home():
    if 'username' in session:
        username = session['username']
        app.logger.info(username)
    # Serve the home page
    return render_template('index.html')

# Serve the various different pages
@app.route('/purchase')
def purchase():
    return render_template('purchase.html')

# recieve purchase information
@app.route('/purchase-info', methods=['POST'])
def purchase_info():
    if request.is_json:
        data = request.get_json()
        emailPurchase = data.get('emailPurchase')
        customer = data.get('customer')
        vehicleName = data.get('vehicleName')
        vehiclePrice = data.get('vehiclePrice')
        deliveryCode = data.get('deliveryCode')
        dateToday = date.today()
        
        #update vehicle stock in the database and email user if needed
        try:
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor()
            cursor.execute("UPDATE vehicles SET stock = stock - 1 WHERE vehicleID = %s;", (data.get('vehicleID'),))
            cnx.commit()
        except mysql.connector.Error as err:
            app.logger.info("error:" + str(err))
        finally:
            if 'cnx' in locals() and cnx.is_connected():
                cursor.close()
                cnx.close()

        #check if the user should be emailed
        try:
            if emailPurchase == True:
                customer_email = ""

                # fetch the user's email
                cnx = mysql.connector.connect(**config)
                cursor = cnx.cursor()
                cursor.execute("SELECT email FROM users WHERE username = %s", (session['username'],))
                customer_email = cursor.fetchone()
                if 'cnx' in locals() and cnx.is_connected():
                    cursor.close()
                    cnx.close()
                customer_email = customer_email[0]
                if customer_email == "":
                    raise Exception("email not found.")

                #insert the order's details into the database
                cnx = mysql.connector.connect(**config)
                cursor = cnx.cursor()
                cursor.execute("INSERT INTO orders (username, vehicle, price, date) VALUES (%s, %s, %s, %s)", (session['username'], vehicleName, int(vehiclePrice.replace(',', '')), dateToday))
                cnx.commit()
                if 'cnx' in locals() and cnx.is_connected():
                    cursor.close()
                    cnx.close()

                #setup the rest of the details for the email
                email = "vehiclesalesbot@gmail.com"

                text = f"Subject: Online Vehicle Purchase Receipt\n\nCustomer: {customer}\r\nVehicle: {vehicleName}\r\nPrice: ${vehiclePrice}\r\nDate: {dateToday}"
                #check if the user has a pick-up code
                if deliveryCode != -1:
                    text += f"\r\n\r\nThe pick-up code is: {deliveryCode}"

                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()

                server.login(email, "qewutidqrqlfokjh")
                
                server.sendmail(email, customer_email, text)

                app.logger.info("Email has been sent to " + customer_email)

        except Exception as e:
            app.logger.exception(f"An unexpected error occurred: {e}")

        return 'success', 200
    else:
        return 'bad data', 400

# load the sales report
@app.route('/sales-report')
def sales_report():
    return render_template('sales-report.html')

# code for updating the vehicle inventory
@app.route('/vehicle-inventory', methods=['GET', 'POST'])
def vehicle_inventory():
    if request.method == 'POST':
        #get all of the information for the vehicle stock update
        name = request.form['name']
        stock = request.form['stock']
        price = request.form['price']
        make, model = name.split(' ', 1)

        #update the selected vehicle
        try:
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor()
            cursor.execute("UPDATE vehicles SET stock = %s, price = %s WHERE make = %s AND model = %s", (stock, price, make, model))
            cnx.commit()
        except mysql.connector.Error as err:
            app.logger.info("error:" + str(err))
        finally:
            if 'cnx' in locals() and cnx.is_connected():
                cursor.close()
                cnx.close()
    return render_template('vehicle-inventory.html')


# code for updating user information
@app.route('/update-user', methods=['GET', 'POST'])
def update_user():
    if request.method == "7":
        #get all of the information for the vehicle stock update
        name = request.form['name']
        stock = request.form['stock']
        price = request.form['price']
        make, model = name.split(' ', 1)

        #update the selected vehicle
        try:
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor()
            cursor.execute("UPDATE vehicles SET stock = %s, price = %s WHERE make = %s AND model = %s", (stock, price, make, model))
            cnx.commit()
        except mysql.connector.Error as err:
            app.logger.info("error:" + str(err))
        finally:
            if 'cnx' in locals() and cnx.is_connected():
                cursor.close()
                cnx.close()
    # check if the user is an admin
    if session['username'] == "Admin":
        return render_template('update-user.html')
    else:
        return "no permission"

# code for creating an account
@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        #get all of the information for creating an account
        first_name = request.form['first-name']
        last_name = request.form['last-name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        #hash the password and format the password for hashing
        plain_password_bytes = password.encode('utf-8')
        hashed_password = bcrypt.hashpw(plain_password_bytes, bcrypt.gensalt( 13 ))

        #insert the new user into the database
        try:
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor()
            cursor.execute("INSERT INTO users (first_name, last_name, username, email, password) VALUES (%s, %s, %s, %s, %s)", (first_name, last_name, username, email, hashed_password))
            cnx.commit()
        except mysql.connector.Error as err:
            app.logger.info("error:" + str(err))
        finally:
            if 'cnx' in locals() and cnx.is_connected():
                cursor.close()
                cnx.close()

        #move the user to the login page
        app.logger.info(f"information in post request: {first_name} {last_name} {username} {email} {password}")
        return redirect('sign-in')
    return render_template('sign-up.html')

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        #get all of the information for logging into an account
        username = request.form['username']
        password = request.form['password']
        result = ""

        #retrieve the user from the database
        try:
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor()
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
        except mysql.connector.Error as err:
            app.logger.info("error:" + str(err))
        finally:
            if 'cnx' in locals() and cnx.is_connected():
                cursor.close()
                cnx.close()

        #format password for being compared to hashed password
        plain_password_bytes = password.encode('utf-8')

        #check if user exists
        if result:
            stored_hashed_password = result[0]
            
            #format hashed password for being compared to password
            hashed_password_bytes = stored_hashed_password.encode('utf-8')
            
            # Compare the user-submitted password with the stored hash
            if bcrypt.checkpw(plain_password_bytes, hashed_password_bytes):
                # Password matches, log the user in
                session['username'] = username
                return redirect('/')
            else:
                # Password does not match
                flash('Invalid username or password', 'error')
        else:
            # Username not found
            flash('Invalid username or password', 'error')
    return render_template('sign-in.html')
    

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

#code for loading vehicles on the vehicle selection page
@app.route('/get-data')
def get_data():
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehicles;")
        data = cursor.fetchall()
    except mysql.connector.Error as err:
        data = {"error": str(err)}
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

    return jsonify(data)

#code for loading orders on the sales report page
@app.route('/get-order-data')
def get_order_data():
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orders;")
        data = cursor.fetchall()
    except mysql.connector.Error as err:
        data = {"error": str(err)}
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

    return jsonify(data)

#code for getting user data on the update user page
@app.route('/get-user-data', methods=['GET', 'POST'])
def get_user_data():
    if request.method == 'POST':
        #get the username target
        username = request.form['username']
    
        #find that user's information
        try:
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %$",  (username,))
            data = cursor.fetchall()
        except mysql.connector.Error as err:
            data = {"error": str(err)}
        finally:
            if 'cnx' in locals() and cnx.is_connected():
                cursor.close()
                cnx.close()

        return jsonify(data)

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True)