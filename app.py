from flask import Flask, render_template, jsonify, request, redirect
import mysql.connector
import bcrypt

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
    # Serve the home page
    return render_template('index.html')

# Serve the various different pages
@app.route('/purchase')
def purchase():
    return render_template('purchase.html')

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

        #hash the password
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

@app.route('/sign-in')
def sign_in():
    return render_template('sign-in.html')
    #app.logger.info(bcrypt.checkpw(plain_password_bytes, hashed_password))

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

if __name__ == '__main__':
    app.run(debug=True)