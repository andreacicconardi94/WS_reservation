from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load variable from file .env
load_dotenv()

# Database credentials
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
            gssencmode="disable"
        )
        return conn
    except Exception as e:
        print("Connection error:", e)
        return None

# Route to visualize reservations
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

# Route to add a reservation
@app.route('/book', methods=['POST'])
def book():
    user_name = request.form['user_name']
    workstation = int(request.form['workstation'])  # Workstation choice
    date = request.form['date']
    time_slot = request.form['time_slot']

    # Convert start time to proper format
    time_slot = datetime.strptime(time_slot, "%H:%M").strftime("%H:%M")

    # Define reservation duration (e.g., 2 hours)
    duration = timedelta(hours=2)
    start_time = datetime.strptime(time_slot, "%H:%M")
    end_time = (start_time + duration).strftime("%H:%M")

    conn = create_connection()
    if conn:
        cursor = conn.cursor()

        # Check for overlapping reservations on the same workstation
        query = """
        SELECT * FROM bookings 
        WHERE date = %s 
        AND workstation = %s
        AND (
            (time_slot <= %s AND end_time > %s) OR
            (time_slot < %s AND end_time >= %s)
        );
        """
        cursor.execute(query, (date, workstation, end_time, end_time, time_slot, time_slot))
        
        if cursor.fetchone():  # If a conflicting booking is found
            cursor.close()
            conn.close()
            return redirect(url_for('index', error="The slot is already booked on this workstation"))

        # Insert the new booking
        cursor.execute(
            "INSERT INTO bookings (user_name, workstation, date, time_slot, end_time) VALUES (%s, %s, %s, %s, %s);",
            (user_name, workstation, date, time_slot, end_time)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    else:
        return "Connection error to the database"

# Route to delete a reservation
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
        return "Connection error to the database"

# Start the server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
