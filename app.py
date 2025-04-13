from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
DATABASE = 'appointments.db'

# Initialize the database
def init_db():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    time TEXT NOT NULL
                )
            ''')
            conn.commit()
            print("Database and table initialized successfully!")  # Debug statement
    except Exception as e:
        print(f"Error initializing database: {e}")  # Debug statement

def get_today_appointments():
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Debug: Print the query and today's date
        print(f"Query: SELECT * FROM appointments WHERE date(time) = '{today}'")
        cursor.execute('SELECT * FROM appointments WHERE date(time) = ?', (today,))
        appointments = cursor.fetchall()
        print(f"Today's appointments: {appointments}")  # Debug statement
        return appointments

def add_appointment(name, phone, time):
    # Combine today's date with the selected time
    appointment_time = datetime.now().strftime('%Y-%m-%d') + ' ' + time + ':00'
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO appointments (name, phone, time) VALUES (?, ?, ?)', (name, phone, appointment_time))
        conn.commit()
        print(f"Appointment added: {name}, {phone}, {appointment_time}")  # Debug statement

# Check if the appointment time is available
def is_time_available(time):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM appointments WHERE time = ?', (time,))
        return cursor.fetchone() is None

# Generate available time slots
def generate_time_slots():
    start_time = datetime.strptime('09:00', '%H:%M')
    end_time = datetime.strptime('17:00', '%H:%M')
    time_slots = []
    current_time = start_time

    while current_time < end_time:
        time_slots.append(current_time.strftime('%H:%M'))
        # Add 30 minutes using timedelta
        current_time += timedelta(minutes=30)

    return time_slots

def send_sms(phone, name, time):
    # ClickSend API endpoint
    sms_endpoint = "https://rest.clicksend.com/v3/sms/send"
    
    # Prepare the message
    message = f"Hi {name}, your appointment is scheduled for {time}."
    
    # Prepare the payload
    payload = {
        "messages": [
            {
                "body": message,
                "to": phone,
                "from": "+61447038711"  # Replace with your sender number
            }
        ]
    }
    
    # Send the request with Basic Auth
    response = requests.post(
        sms_endpoint,
        json=payload,
        auth=HTTPBasicAuth("engramar@code.sydney", "BA405B6A-4D4C-DF61-BE11-FF310F62C258")
    )
    
    # Check if the SMS was sent successfully
    if response.status_code == 200 and response.json().get("response_code") == "SUCCESS":
        print(f"SMS sent to {phone}: {message}")
        return True
    else:
        print(f"Failed to send SMS to {phone}. Response: {response.text}")
        return False

@app.route('/', methods=['GET', 'POST'])
def home():
    message_sent = False  # Flag to indicate if the SMS was sent
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        time = request.form['time']

        if is_time_available(time):
            add_appointment(name, phone, time)  # Add the appointment to the database
            if send_sms(phone, name, time):  # Send SMS notification
                message_sent = True
        else:
            return "Time slot is already booked. Please choose another time."

    # Fetch the updated list of appointments
    time_slots = generate_time_slots()
    appointments = get_today_appointments()  # Re-fetch appointments from the database
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', time_slots=time_slots, appointments=appointments, today_date=today_date, message_sent=message_sent)
    
if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)