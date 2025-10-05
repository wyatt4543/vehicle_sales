from flask import Flask, render_template, jsonify
import mysql.connector

app = Flask(__name__)

@app.route('/')
def home():
    # Serve your HTML page
    return render_template('index.html')

@app.route('/purchase')
def purchase():
    return render_template('purchase.html')

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
