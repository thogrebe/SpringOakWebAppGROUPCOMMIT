import sqlite3
import time
import datetime
from flask_bootstrap import Bootstrap5
from flask import Flask, render_template, request, redirect, url_for, flash


app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'
bootstrap = Bootstrap5(app)


# Dummy staff username and password (replace this with a secure authentication mechanism)
STAFF_USERNAME = "admin"
STAFF_PASSWORD = "password"


# In-memory list to store registered visitors
registered_visitors = []


# In-memory list to store checked-in visitors
checked_in_visitors = []


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == STAFF_USERNAME and password == STAFF_PASSWORD:
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password. Please try again."
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    checked_in_count = len(checked_in_visitors)
    checked_out_count = len(registered_visitors) - checked_in_count
    registered_count = len(registered_visitors)
    return render_template('dashboard.html', checked_in_count=checked_in_count, checked_out_count=checked_out_count, registered_count=registered_count)


@app.route('/visitors')
def visitors():
    visitor_type = request.args.get('type', 'registered')
    checked_in_count = len([visitor for visitor in registered_visitors if visitor['checked_in']])
    checked_out_count = len(registered_visitors) - checked_in_count

    if visitor_type == 'checked_in':
        filtered_visitors = [visitor for visitor in registered_visitors if visitor['checked_in']]
    elif visitor_type == 'checked_out':
        filtered_visitors = [visitor for visitor in registered_visitors if not visitor['checked_in']]
    else:
        filtered_visitors = registered_visitors

    return render_template('visitors.html', visitors=filtered_visitors, checked_in_visitors=checked_in_visitors, type=visitor_type, checked_in_count=checked_in_count, checked_out_count=checked_out_count)

@app.route('/registration-success')
def registration_success():
    return render_template('registration_success.html')
# Modify the register route to include the 'checked_in' field
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("Register route received a POST request")
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        residentname = request.form.get('residentname')
        date = request.form.get('date')
        phonenumber = request.form.get('phonenumber')
        email = request.form.get('email')

        # Create a dictionary to represent the visitor
        visitor = {
            'name': f'{firstname} {lastname}',
            'resident_name': residentname,
            'date': date,
            'phone': phonenumber,
            'email': email,
            'checked_in': False  # Initialize 'checked_in' to False when registering
        }

        # Add the visitor to the list of registered visitors
        registered_visitors.append(visitor)
        return redirect(url_for('registration_success'))

    return render_template('index.html')

@app.route('/visitor-dashboard', methods=['GET', 'POST'])
def visitor_dashboard():
    if request.method == 'POST':
        if 'register' in request.form:
            return redirect(url_for('register'))
        elif 'checkin' in request.form:
            visitor_email = request.form['visitor_email']
            print(f"Check-in request for email: {visitor_email}")
            for visitor in registered_visitors:
                if visitor['email'] == visitor_email:
                    if not visitor['checked_in']:
                        visitor['checked_in'] = True
                        visitor['checkin_time'] = datetime.datetime.now()  # Capture check-in time
                        checked_in_visitors.append(visitor)
                        print("Check-in successful!")
                        return render_template('checkin_success.html')  # Render checkin_success.html on success
                    else:
                        print("Visitor is already checked in.")
                        return "Visitor is already checked in."
            print("Visitor not found.")
            return "Visitor not found."
        elif 'checkout' in request.form:
            visitor_email = request.form['visitor_email']
            print(f"Check-out request for email: {visitor_email}")
            for visitor in checked_in_visitors:
                if visitor['email'] == visitor_email:
                    if visitor['checked_in']:
                        visitor['checked_in'] = False
                        visitor['checkout_time'] = datetime.datetime.now()  # Capture check-out time
                        checked_in_visitors.remove(visitor)
                        print("Check-out successful!")
                        return render_template('checkout_success.html')  # Render checkout_success.html on success
                    else:
                        print("Visitor is not checked in. Cannot check out.")
                        return "Visitor is not checked in. Cannot check out."
            print("Visitor not found or not checked in.")
            return "Visitor not found or not checked in."

    return render_template('visitor_dashboard.html')


# Resident dashboard login
@app.route('/resident-login', methods=['GET', 'POST'])
def resident_login():
    if request.method == 'POST':
        username = request.form['username']
        room_number = request.form['room_number']

        # Check that the resident exists
        cursor = db_connection()
        resident_data = cursor.execute('SELECT * FROM Residents WHERE residentFirstName = ? AND roomNumber = ?',
                                       (username, room_number)).fetchone()

        if resident_data:
            session['resident_loggedin'] = True
            session['resident_id'] = resident_data['residentID']
            session['resident_username'] = resident_data['residentFirstName']
            # Redirect to the resident dashboard
            return redirect(url_for('resident_homepage'))

        else:
            flash('Invalid resident credentials. Please try again.')

    return render_template('resident_login.html')


@app.route('/resident-homepage')
def resident_homepage():
    if 'resident_loggedin' in session and session['resident_loggedin']:
        # Render the resident dashboard template
        return render_template('resident_homepage.html')
    else:
        # Redirect to the resident login page if the resident isn't logged in
        return redirect(url_for('resident_login'))


@app.route('/logout', methods=['POST'])
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
