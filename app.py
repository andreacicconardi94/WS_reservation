from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
from dotenv import load_dotenv


# Load variable from file .env
load_dotenv()

print("DB_HOST:", os.getenv("DB_HOST"))


# Set the database
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

app = Flask(__name__)

# Function to connect to the database
def create_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            gssencmode = "disable"
        )
        return conn
    except Exception as e:
        print("Connection error:", e)
        return None

# Route to visualize the reservations
@app.route('/')
def index():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings ORDER BY date, time_slot;")
        bookings = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('index.html', bookings=bookings)
    else:
        return "Connection error to the database"

# Route per add a reservation
@app.route('/book', methods=['POST'])
def book():
    user_name = request.form['user_name']
    date = request.form['date']
    time_slot = request.form['time_slot']

    if user_name and date and time_slot:
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bookings WHERE date = %s AND time_slot = %s;", (date, time_slot))
            if cursor.fetchone():  # Check if the slot is already reserved
                cursor.close()
                conn.close()
                return redirect(url_for('index', error="The slot is already booked"))
            
            # Add the reservation
            cursor.execute("INSERT INTO bookings (user_name, date, time_slot) VALUES (%s, %s, %s);", (user_name, date, time_slot))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('index'))
        else:
            return "Connection error to the database"
    else:
        return redirect(url_for('index', error="All fields are mandatory"))

# Route per delete a reservation
@app.route('/cancel/<int:booking_id>', methods=['GET'])
def cancel(booking_id):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE id = %s;", (booking_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    else:
        return "Errore di connessione al database"

# Start the server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

