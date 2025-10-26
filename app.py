from flask import Flask, render_template, jsonify, request, redirect
import mysql.connector

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
    app.logger.info("sign up page loaded")
    if request.method == 'POST':
        #get all of the information for creating an account
        first_name = request.form['first-name']
        last_name = request.form['last-name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        #hashed_password = generate_password_hash(password)

        #cursor = mysql.connection.cursor()
        #cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
                       #(username, hashed_password, email))
        #mysql.connection.commit()
        #cursor.close()
        app.logger.info(f"information in post request: {first_name} {last_name} {username} {email} {password}")
        return redirect('sign-in')
    return render_template('sign-up.html')

@app.route('/sign-in')
def sign_in():
    return render_template('sign-in.html')

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