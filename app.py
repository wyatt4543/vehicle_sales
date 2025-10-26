from flask import Flask, render_template, jsonify
import mysql.connector

app = Flask(__name__)

@app.route('/')
def home():
    # Serve the home page
    return render_template('index.html')

# Serve the various different pages
@app.route('/purchase')
def purchase():
    return render_template('purchase.html')

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    return render_template('sign-up.html')
    if request.method == 'POST':
        #username = request.form['username']
        #password = request.form['password']
        #email = request.form['email']

        #hashed_password = generate_password_hash(password)

        #cursor = mysql.connection.cursor()
        #cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
                       #(username, hashed_password, email))
        #mysql.connection.commit()
        #cursor.close()
        print(request.form)
        return redirect('sign-in.html')

@app.route('/sign-in')
def sign_in():
    return render_template('sign-in.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

#code for loading vehicles on the vehicle selection page
@app.route('/get-data')
def get_data():
    config = {
        'host': 'fplg27.h.filess.io',
        'user': 'VehicleSales_selection',
        'password': '3964f4ec577fce81b6857f4807a2dee1e5e94ad3',
        'port': '61032',
        'database': 'VehicleSales_selection'
    }

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