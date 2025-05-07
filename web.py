from flask import Flask, render_template, request, jsonify,session,redirect, url_for
from mysql.connector import pooling, Error
from functools import wraps 
import requests


# Setup MySQL connection pool
pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    pool_reset_session=True,
    host="127.0.0.1",
    user="root",
    password="2001#Kamohelo",
    database="Group_20"
)

app = Flask(__name__)
app.secret_key = 'ENGINEERINGPROGRAMMING'

print("Connection pool created successfully.")

#------------------------------------------------Decorator Function----------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#------------------------------------------------Protect Routes---------------------------------------------
@app.route('/', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Registration WHERE User_Password = %s AND Username = %s", (password, username,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        if result:
            session['logged_in'] = True
            session['username'] = username
            return render_template("verify_detail.html", username=username, exists=True)
        else:
            return render_template("verify_detail.html", exists=False)
    return render_template("Login.html")

@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Registration(Username, User_Password, Student_Email) VALUES(%s, %s, %s)", (username, password, email))
        connection.commit()
        cursor.close()
        connection.close()
        return render_template("result.html", username=username, email=email)
    return render_template("register.html")

#----------------------------------------------HELPER FUNTION---------------------------------#
def fetch_latest_data(table_name, data_column):
    try:
        connection = pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT {data_column}, lastUpdated FROM {table_name} ORDER BY lastUpdated DESC LIMIT 1"
        cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()
        connection.close()

        if row:
            return jsonify({
                "timestamp": row["lastUpdated"].strftime('%Y-%m-%d %H:%M:%S'),
                "value": row[data_column]
            })
        else:
            return jsonify({"error": "No data found"}), 404
    except Error as err:
        print(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500
    
#-------------------------------------------------API'S-----------------------------------------------#
@app.route('/ldr1_data')
def ldr1_data():
    return fetch_latest_data("ldr_1", "Ldr_1_data")

@app.route('/ldr2_data')
def ldr2_data():
    return fetch_latest_data("ldr_2", "Ldr_2_data")

@app.route('/ldr3_data')
def ldr3_data():
    return fetch_latest_data("ldr_3", "Ldr_3_data")

@app.route('/pir_data')
def pir_data():
    return fetch_latest_data("pir", "PIR_STATUS")

@app.route('/humidity_data')
def humidity_data():
    return fetch_latest_data("humidity", "relative_humidity")

@app.route('/temp_data')
def temp_data():
    return fetch_latest_data("temperature", "temp_value")


#-------------------------------------------Render Templates Routes---------------------------------------#
@app.route('/ldr_1', methods=["POST", "GET"])
@login_required
def Ldr_1():
    return render_template("ldr_1.html")

@app.route('/ldr_2', methods=["POST", "GET"])
@login_required
def Ldr_2():
    return render_template("ldr_2.html")

@app.route('/ldr_3', methods=["POST", "GET"])
@login_required
def Ldr_3():
    return render_template("ldr_3.html")

@app.route('/temperature', methods=["POST", "GET"])
@login_required
def temp():
    return render_template("temperature.html")

@app.route('/pir', methods=["POST", "GET"])
@login_required
def pir():
    return render_template("pir.html")

@app.route('/admin_2', methods=["POST", "GET"])
@login_required
def humidity():
    return render_template("admin.html")

@app.route('/admin', methods=["POST", "GET"])
@login_required
def admin():
    connection = pool.get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Registration")
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template("humidity.html", data=data)

@app.route('/sensor-data', methods=['POST'])
def esp32_data():
    try:
        data = request.get_json()
        id = data['id']
        ldr_1_value = data['ldr_1_value']
        ldr_2_value = data['ldr_2_value']
        ldr_3_value = data['ldr_3_value']
        Humidity = data['humidity']
        Temperature = data['temperature']
        PIR_info = data['motion_detected']

        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Ldr_1(Ldr_1_data) VALUES (%s)", (ldr_1_value,))
        cursor.execute("INSERT INTO Ldr_2(Ldr_2_data) VALUES (%s)", (ldr_2_value,))
        cursor.execute("INSERT INTO Ldr_3(Ldr_3_data) VALUES (%s)", (ldr_3_value,))
        cursor.execute("INSERT INTO humidity(relative_humidity) VALUES (%s)", (Humidity,))
        cursor.execute("INSERT INTO temperature(temp_value) VALUES (%s)", (Temperature,))
        cursor.execute("INSERT INTO pir(PIR_STATUS) VALUES (%s)", (PIR_info,))
        connection.commit()
        cursor.close()
        connection.close()

        print("Received data:", data)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error inserting sensor data: {e}")
        return jsonify({"status": "failure", "error": str(e)}), 500
    
#--------------------------------------------Logout Route-------------------------------------------#
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
    
#--------------------------------------------Message Route------------------------------------------#

# Add your bot token and group chat ID
BOT_TOKEN = '7979187386:AAFDbDhFEqpZUJBEAFJka4uxHyO96b2VDAU'
CHAT_ID = '-4653857680'

@app.route('/send-message', methods=['GET', 'POST'])
@login_required
def send_message():
    success = None
    if request.method == 'POST':
        message = request.form['message']
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        payload = {
            'chat_id': CHAT_ID,
            'text': message
        }
        response = requests.post(url, data=payload)
        success = response.status_code == 200
    return render_template('send_alerts.html', success=success)




if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

    
    
    
 
 