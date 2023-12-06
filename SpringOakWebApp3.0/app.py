from sqlite3 import IntegrityError

# from wsgiref.handlers import format_date_time
# from backports.zoneinfo import ZoneInfo
# from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import (
    String,
    asc,
    func,
)  # This is the correct import for datetime.strptime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from datetime import timedelta
from flask import render_template
from sqlalchemy import or_, cast, String
from flask import request, render_template

app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "default-secret-key")

# Database configuration
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://qxfdouabbyiwxc:839dace584e6853abff16bbd21bd31126cf6bdfdd5fa0b6193f439ed41e20f19@ec2-3-212-29-93.compute-1.amazonaws.com:5432/d2sbv72ptga2jm"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Optional: to suppress a warning
# Initialize extensions
db = SQLAlchemy(app)


# Define models
class Resident(db.Model):
    __tablename__ = "residents"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    enter_date = db.Column(db.DateTime, nullable=False)
    room_number = db.Column(db.String(), nullable=False, unique=True)
    insurance = db.Column(db.String(), nullable=True)
    emergency_contact_full_name = db.Column(db.String(), nullable=True)
    emergency_contact_phone_number = db.Column(db.String(), nullable=True)
    visitors = db.relationship("Visitor", backref="resident", lazy=True)

    # Unique constraint on the combination of last_name and room_number
    __table_args__ = (db.UniqueConstraint("last_name", "room_number"),)


class VisitRecord(db.Model):
    __tablename__ = "visit_records"
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey("visitors.id"))
    visit_date = db.Column(db.Date, nullable=False)
    visit_time = db.Column(db.Time)


class Visitor(db.Model):
    __tablename__ = "visitors"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    checked_in = db.Column(db.Boolean, default=False, nullable=False)
    checkin_time = db.Column(db.DateTime, nullable=True)
    checkout_time = db.Column(db.DateTime, nullable=True)
    resident_last_name = db.Column(db.String, nullable=False)
    resident_room_number = db.Column(db.String, nullable=False)
    visit_records = db.relationship("VisitRecord", backref="visitor", lazy=True)

    # Composite foreign key that references both last_name and room_number in residents
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["resident_last_name", "resident_room_number"],
            ["residents.last_name", "residents.room_number"],
        ),
    )


class TravelRequest(db.Model):
    __tablename__ = "travel_requests"
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("residents.id"), nullable=False)
    resident = db.relationship("Resident", backref="travel_requests")
    submission_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    destination = db.Column(db.Text, nullable=False)
    purpose = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")

    __table_args__ = (
        db.ForeignKeyConstraint(
            ["resident_id"],
            ["residents.id"],
        ),
    )


class MaintenanceRequest(db.Model):
    __tablename__ = "maintenance_requests"
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("residents.id"), nullable=False)
    resident = db.relationship("Resident", backref="maintenance_requests")
    submission_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    work_type = db.Column(db.String(20), nullable=False)
    date_completed = db.Column(db.Date, nullable=True)
    preferred_date = db.Column(db.Date, nullable=True)
    contact_number = db.Column(db.String(20), nullable=False)
    entry_permission = db.Column(db.Boolean, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")

    __table_args__ = (
        db.ForeignKeyConstraint(
            ["resident_id"],
            ["residents.id"],
        ),
    )


class DoctorRequest(db.Model):
    __tablename__ = "doctor_requests"
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("residents.id"), nullable=False)
    resident = db.relationship("Resident", backref="doctor_requests")
    submission_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    insurance_provider = db.Column(db.String(100), nullable=True)
    special_requests = db.Column(db.Text, nullable=True)
    date_seen = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")

    __table_args__ = (
        db.ForeignKeyConstraint(
            ["resident_id"],
            ["residents.id"],
        ),
    )


# Initialize the database (This will create the tables based on your models at the first run)
with app.app_context():
    db.create_all()

# Replace with database or secure authentication mechanism
STAFF_USERNAME = "admin"
STAFF_PASSWORD = "password"

# Use session to store the information which is more secure
residents = []
registered_visitors = []
checked_in_visitors = []


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == STAFF_USERNAME and password == STAFF_PASSWORD:
            return redirect(url_for("dashboard"))
        else:
            incorrect_login = True
            return render_template("login.html", incorrect_login=incorrect_login)
    return render_template("login.html")


@app.route("/resident-database", methods=["GET", "POST"])
def resident_database():
    if request.method == "POST":
        # Parse dates from form input in the format YYYY-MM-DD
        birthdate_str = request.form.get("birthdate", "")
        enter_date_str = request.form.get("enter_date", "")
        try:
            birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
            enter_date = datetime.strptime(enter_date_str, "%Y-%m-%d")
        except ValueError:
            flash("Incorrect date format. Please use YYYY-MM-DD.", "error")
            return redirect(url_for("resident_database"))

        # Create a new instance of Resident
        new_resident = Resident(
            first_name=request.form.get("first_name", ""),
            last_name=request.form.get("last_name", ""),
            birthdate=birthdate,
            enter_date=enter_date,
            room_number=request.form.get("room_number", ""),
            insurance=request.form.get("insurance"),  # Optional field, defaults to None
            emergency_contact_full_name=request.form.get(
                "emergency_contact_full_name"
            ),  # Optional field, defaults to None
            emergency_contact_phone_number=request.form.get(
                "emergency_contact_phone_number"
            ),  # Optional field, defaults to None
        )

        # Add to the session and commit
        db.session.add(new_resident)
        try:
            db.session.commit()
            flash("New resident added successfully!", "success")
        except IntegrityError as e:
            db.session.rollback()
            flash("A database error occurred. Please try again.", "error")
            app.logger.error("IntegrityError: %s", e)
        except Exception as e:
            db.session.rollback()
            flash("An unexpected error occurred. Please try again.", "error")
            app.logger.error("Exception: %s", e)

        # After POST redirect to the same page to see the list of residents
        return redirect(url_for("resident_database"))

    # GET request - retrieve and display residents
    residents = Resident.query.order_by(Resident.id).all()
    return render_template("resident_database.html", residents=residents)


@app.route("/search-residents", methods=["GET"])
def search_residents():
    query = request.args.get("query", "")
    search = "%{}%".format(query)
    residents = Resident.query.filter(
        (Resident.first_name.like(search))
        | (Resident.last_name.like(search))
        | (func.cast(Resident.birthdate, String).like(search))
    ).all()
    return render_template("resident_database.html", residents=residents)


@app.route("/resident-login", methods=["POST"])
def resident_login():
    room_number = request.form.get("roomNumber")
    last_name = request.form.get("lastName")

    # Query the database to find the resident
    resident = Resident.query.filter_by(
        room_number=room_number, last_name=last_name
    ).first()

    # Check if resident exists
    if resident:
        # Store relevant information in the session
        session["resident_id"] = resident.id
        session["resident_name"] = f"{resident.first_name} {resident.last_name}"

        # Give feedback to the user
        flash("Login successful!", "success")

        # Redirect to the resident requests portal
        return redirect(url_for("resident_requests_portal"))
    else:
        # Give feedback to the user
        flash("Invalid login credentials. Please try again.", "error")

        # Redirect back to the login page
        return redirect(
            url_for("login")
        )  # Make sure 'login' is the endpoint for the login page.


@app.route("/logout")
def resident_logout():
    session.pop("resident_id", None)
    # Clear the session or any other logout logic
    # session.pop('user_id', None)  # Example of clearing session data

    flash("You have been logged out.", "success")

    # Redirect to the login screen
    return redirect(url_for("resident_database"))


@app.route("/resident-requests-portal")
def resident_requests_portal():
    if "resident_id" not in session:
        # If not, redirect to login page
        return redirect(url_for("login"))
    # Render the resident requests portal page
    return render_template("resident_request_portal.html")


@app.route("/resident/edit/<int:resident_id>", methods=["GET", "POST"])
def edit_resident(resident_id):
    resident = Resident.query.get_or_404(resident_id)
    if request.method == "POST":
        # Extracting form data
        room_number = request.form["room_number"]
        insurance = request.form["insurance"]
        emergency_contact_full_name = request.form["emergency_contact_full_name"]
        emergency_contact_phone_number = request.form["emergency_contact_phone_number"]

        # Updating resident object
        resident.room_number = room_number
        resident.insurance = insurance
        resident.emergency_contact_full_name = emergency_contact_full_name
        resident.emergency_contact_phone_number = emergency_contact_phone_number

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            print("Error during database commit:", e)

        return redirect(
            url_for(
                "resident_profile",
                room_number=resident.room_number,
                resident_last_name=resident.last_name,
            )
        )

    return render_template("edit_resident.html", resident=resident)


@app.route("/resident_profile/<int:room_number>/<resident_last_name>")
def resident_profile(room_number, resident_last_name):
    room_number_str = str(room_number)  # Convert to string
    resident = Resident.query.filter_by(
        room_number=room_number_str, last_name=resident_last_name
    ).first_or_404()
    visitors = Visitor.query.filter_by(
        resident_room_number=room_number_str, resident_last_name=resident_last_name
    ).all()

    for visitor in visitors:
        # Apply manual adjustment for check-in time
        if visitor.checkin_time:
            adjusted_checkin_time = visitor.checkin_time - timedelta(hours=5)
            visitor.local_checkin_time = adjusted_checkin_time.strftime("%I:%M %p")
        else:
            visitor.local_checkin_time = "N/A"

        # Apply manual adjustment for check-out time
        if visitor.checkout_time:
            adjusted_checkout_time = visitor.checkout_time - timedelta(hours=5)
            visitor.local_checkout_time = adjusted_checkout_time.strftime("%I:%M %p")
        else:
            visitor.local_checkout_time = "N/A"

    return render_template(
        "resident_profile.html", resident=resident, visitors=visitors
    )


@app.route("/resident/delete/<int:resident_id>", methods=["POST"])
def delete_resident(resident_id):
    resident = Resident.query.get_or_404(resident_id)
    db.session.delete(resident)
    db.session.commit()
    flash("Resident deleted successfully!", "success")
    return redirect(url_for("resident_database"))


@app.route("/dashboard")
def dashboard():
    checked_in_count = len(checked_in_visitors)
    checked_out_count = len(registered_visitors) - checked_in_count
    registered_count = len(registered_visitors)
    return render_template(
        "dashboard.html",
        checked_in_count=checked_in_count,
        checked_out_count=checked_out_count,
        registered_count=registered_count,
    )


@app.route("/visitors")
def visitors():
    # Retrieve the filter type from the query parameter
    visitor_type = request.args.get("type", "all")

    # Filter the visitors based on the visitor_type
    if visitor_type == "checked_in":
        visitors = Visitor.query.filter_by(checked_in=True).all()
    elif visitor_type == "checked_out":
        visitors = Visitor.query.filter(
            Visitor.checked_in == False, Visitor.checkout_time.isnot(None)
        ).all()
    else:
        visitors = Visitor.query.all()

    return render_template("visitors.html", visitors=visitors)


@app.route("/registration-success")
def registration_success():
    return render_template("registration_success.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # POST: Process the registration form submission
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        resident_last_name = request.form.get("resident_last_name")
        resident_room_number = request.form.get("resident_room_number")
        date = request.form.get("date")
        phone = request.form.get("phonenumber")
        email = request.form.get("email")

        # Check if a resident with the provided last name and room number exists
        resident = Resident.query.filter_by(
            last_name=resident_last_name, room_number=resident_room_number
        ).first()

        if resident is None:
            flash(
                "Resident not found. Please check the details and try again.", "error"
            )
            return redirect(url_for("register"))

        try:
            new_visitor = Visitor(
                first_name=first_name,
                last_name=last_name,
                date=datetime.strptime(date, "%Y-%m-%d"),
                phone=phone,
                email=email,
                checked_in=False,
                resident_last_name=resident_last_name,
                resident_room_number=resident_room_number,
            )
            db.session.add(new_visitor)
            db.session.commit()
            flash("Visitor registration successful!", "success")
            return redirect(url_for("visitor_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for("register"))

    # GET request: Render the registration form
    return render_template("index.html")


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/visitor-dashboard", methods=["GET", "POST"])
def visitor_dashboard():
    if request.method == "POST":
        visitor_email = request.form["visitor_email"]
        local_time_str = request.form["local_time"]

        # Parse the ISO format date assuming it is in UTC
        utc_time = datetime.fromisoformat(
            local_time_str.rstrip("Z")
        )  # Remove the 'Z' before parsing

        # Convert UTC time to Eastern Time (automatically adjusts for EST/EDT)
        eastern_timezone = ZoneInfo("America/New_York")
        local_time = utc_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(
            eastern_timezone
        )

        # Check-in logic
        if "checkin" in request.form:
            visitor = Visitor.query.filter_by(email=visitor_email).first()
            if visitor:
                if not visitor.checked_in:
                    visitor.checked_in = True
                    visitor.checkin_time = local_time  # Store the local time
                    db.session.commit()
                    flash("Visitor checked in successfully.", "success")
                    return redirect(url_for("visitor_dashboard"))
                else:
                    flash("Visitor is already checked in.", "error")
                    return redirect(url_for("visitor_dashboard"))
            else:
                flash("Visitor not found.", "error")
                return redirect(url_for("visitor_dashboard"))

        # Check-out logic
        elif "checkout" in request.form:
            visitor = Visitor.query.filter_by(email=visitor_email).first()
            if visitor:
                if visitor.checked_in:
                    visitor.checked_in = False

                    # Re-confirm local time calculation at the point of check-out
                    local_time_str = request.form["local_time"]
                    utc_time = datetime.fromisoformat(local_time_str.rstrip("Z"))
                    local_time = utc_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(
                        eastern_timezone
                    )

                    visitor.checkout_time = local_time  # Store the local time

                    # Record the visit
                    new_visit = VisitRecord(
                        visitor_id=visitor.id,
                        visit_date=local_time.date(),
                        visit_time=local_time.time(),
                    )
                    db.session.add(new_visit)
                    db.session.commit()
                    flash("Visitor checked out successfully.", "success")
                    return redirect(url_for("visitor_dashboard"))
                else:
                    flash("Visitor is not checked in. Cannot check out.", "error")
                    return redirect(url_for("visitor_dashboard"))
            else:
                flash("Visitor not found or not checked in.", "error")
                return redirect(url_for("visitor_dashboard"))

    return render_template("visitor_dashboard.html")


# Custom filter for converting UTC to local time
def to_localtime(utc_dt, timezone="America/New_York"):  # Replace with your timezone
    local_timezone = ZoneInfo(timezone)
    return utc_dt.astimezone(local_timezone)


def format_datetime(value=None, format="%I:%M %p"):  # Set a default value for 'value'
    if value is None:
        return ""  # Or any placeholder you prefer
    return value.strftime(format)


@app.route("/visitor_profile/<visitor_email>")
def visitor_profile(visitor_email):
    visitor = Visitor.query.filter_by(email=visitor_email).first()

    if visitor:
        # Apply manual adjustment for check-in time using timedelta
        if visitor.checkin_time:
            adjusted_checkin_time = visitor.checkin_time - timedelta(hours=5)
            visitor.local_checkin_time = adjusted_checkin_time.strftime("%I:%M %p")
        else:
            visitor.local_checkin_time = "N/A"

        # Apply manual adjustment for check-out time using timedelta
        if visitor.checkout_time:
            adjusted_checkout_time = visitor.checkout_time - timedelta(hours=5)
            visitor.local_checkout_time = adjusted_checkout_time.strftime("%I:%M %p")
        else:
            visitor.local_checkout_time = "N/A"

        # Render the visitor profile template with the visitor
        return render_template("visitor_profile.html", visitor=visitor)

    else:
        # Handle visitor not found
        return "Visitor not found", 404


@app.route("/visitor_check_status")
def visitor_check_status():
    # Retrieve the filter type from the query parameter
    visitor_type = request.args.get("type", "all")

    # Filter the visitors based on the visitor_type
    if visitor_type == "checked_in":
        visitors = Visitor.query.filter_by(checked_in=True).all()
    elif visitor_type == "checked_out":
        visitors = Visitor.query.filter(
            Visitor.checked_in == False, Visitor.checkout_time.isnot(None)
        ).all()
    else:
        visitors = Visitor.query.all()

    # Adjust check-in and check-out times for display using timedelta
    for visitor in visitors:
        # Apply manual adjustment for check-in time using timedelta
        if visitor.checkin_time:
            adjusted_checkin_time = visitor.checkin_time - timedelta(hours=5)
            visitor.local_checkin_time = adjusted_checkin_time.strftime("%I:%M %p")
        else:
            visitor.local_checkin_time = "N/A"

        # Apply manual adjustment for check-out time using timedelta
        if visitor.checkout_time:
            adjusted_checkout_time = visitor.checkout_time - timedelta(hours=5)
            visitor.local_checkout_time = adjusted_checkout_time.strftime("%I:%M %p")
        else:
            visitor.local_checkout_time = "N/A"

    # Render the visitor_check_status.html template with the adjusted visitors data
    return render_template(
        "visitors_check_status.html", visitors=visitors, visitor_type=visitor_type
    )


@app.route("/visitor/edit/<int:visitor_id>", methods=["GET", "POST"])
def edit_visitor(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    if request.method == "POST":
        # Extracting form data
        visitor.last_name = request.form["first_name"]
        visitor.first_name = request.form["last_name"]
        visitor.phone = request.form["phone"]
        visitor.email = request.form["email"]
        visitor.resident_last_name = request.form["resident_last_name"]
        visitor.resident_room_number = request.form["resident_room_number"]

        # Add any other visitor fields you wish to update

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            print("Error during database commit:", e)

        # Redirect to the visitor profile or another appropriate page
        return redirect(url_for("visitor_profile", visitor_email=visitor.email))

    return render_template("edit_visitor.html", visitor=visitor)


@app.route("/visitor/delete/<int:visitor_id>", methods=["POST"])
def delete_visitor(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    try:
        db.session.delete(visitor)
        db.session.commit()
        flash("Visitor successfully deleted!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting visitor: {e}", "error")

    return redirect(
        url_for("visitors")
    )  # Assuming 'visitors' is the endpoint for the visitor list


@app.route("/search-visitors", methods=["GET"])
def search_visitors():
    query = request.args.get("query", "")
    search = "%{}%".format(query)
    visitors = Visitor.query.filter(
        or_(
            Visitor.first_name.like(search),
            Visitor.last_name.like(search),
            cast(Visitor.phone, String).like(search)
        )
    ).all()
    return render_template("visitors.html", visitors=visitors)


@app.route("/save-visitor-data", methods=["POST"])
def save_visitor_data():
    # Assuming you have a list of visitors who are currently checked out
    checked_out_visitors = Visitor.query.filter_by(checked_in=False).all()

    for visitor in checked_out_visitors:
        # Create a new visit record for each checked-out visitor
        new_visit = VisitRecord(
            visitor_id=visitor.id,
            visit_date=visitor.date,
            visit_time=visitor.checkin_time,
        )
        db.session.add(new_visit)

        # Reset the check-in and check-out times
        visitor.checkin_time = None
        visitor.checkout_time = None
        # Save other necessary changes to the visitor if required

    # Commit the changes to the database
    try:
        db.session.commit()
        flash("Visitor data saved successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while saving visitor data: {e}", "error")

    return redirect(url_for("visitor_check_status"))


@app.route("/submit-maintenance-request", methods=["POST"])
def submit_maintenance_request():
    if request.method == "POST":
        # Retrieve resident information from the session
        resident_id = session.get("resident_id")
        resident_name = session.get("resident_name")

        # Retrieve form data
        name = request.form.get("name", resident_name)
        room_number = request.form.get("room_number")
        contact_number = request.form.get("contact_number")
        issue_description = request.form.get("issue_description")
        preferred_date = request.form.get("preferred_date")
        entry_permission = "entry_permission" in request.form
        notes = request.form.get("notes")

        # Create a new Maintenance Request instance
        maintenance_request = MaintenanceRequest(
            resident_id=resident_id,
            submission_date=datetime.now(),
            room_number=room_number,
            work_type=issue_description,
            date_completed=None,  # Assuming this is filled later
            contact_number=contact_number,
            entry_permission=entry_permission,
            notes=notes,
            status="Pending",  # Set the default status as 'Pending'
        )

        # Add to the session and commit
        db.session.add(maintenance_request)
        try:
            db.session.commit()
            flash("Maintenance request submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {e}", "error")
            app.logger.error(f"Exception: {e}")

        return redirect(url_for("resident_requests_portal"))


@app.route("/submit-travel-request", methods=["POST"])
def submit_travel_request():
    if request.method == "POST":
        # Retrieve resident information from the session
        resident_id = session.get("resident_id")
        resident_name = session.get("resident_name")

        name = request.form.get("name", resident_name)
        destination = request.form.get("destination")
        departure_date = request.form.get("departure_date")
        return_date = request.form.get("return_date")
        travel_purpose = request.form.get("travel_purpose")
        emergency_contact = request.form.get("emergency_contact_travel")

        # Create a new Travel Request instance
        travel_request = TravelRequest(
            resident_id=resident_id,
            submission_date=datetime.now(),
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            purpose=travel_purpose,
            emergency_contact=emergency_contact,
            status="Pending",
        )

        # Add to the session and commit
        db.session.add(travel_request)
        try:
            db.session.commit()
            flash("Travel request submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred. Please try again.", "error")
            app.logger.error(f"Exception: {e}")

        return redirect(url_for("resident_requests_portal"))


# Handle Doctor Request Form Submission
@app.route("/submit-doctor-request", methods=["POST"])
def submit_doctor_request():
    if request.method == "POST":
        # Retrieve resident information from the session
        resident_id = session.get("resident_id")
        resident_name = session.get("resident_name")

        name = request.form.get("name", resident_name)
        symptoms = request.form.get("symptoms")
        preferred_date_doctor = request.form.get("preferred_date_doctor")
        contact_number_doctor = request.form.get("contact_number_doctor")
        insurance_provider = request.form.get("insurance_provider")
        special_requests = request.form.get("special_requests")

        # Create a new Doctor Request instance
        doctor_request = DoctorRequest(
            resident_id=resident_id,
            submission_date=datetime.now(),
            symptoms=symptoms,
            preferred_date=preferred_date_doctor,
            contact_number=contact_number_doctor,
            insurance_provider=insurance_provider,
            special_requests=special_requests,
            status="Pending",
        )

        # Add to the session and commit
        db.session.add(doctor_request)
        try:
            db.session.commit()
            flash("Doctor request submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred. Please try again.", "error")
            app.logger.error(f"Exception: {e}")

        return redirect(url_for("resident_requests_portal"))


from flask import render_template


@app.route("/view-requests")
def view_requests():
    travel_requests = TravelRequest.query.order_by(TravelRequest.id).all()
    maintenance_requests = MaintenanceRequest.query.order_by(
        MaintenanceRequest.id
    ).all()

    if not travel_requests:
        app.logger.error("No travel requests found")
    if not maintenance_requests:
        app.logger.error("No maintenance requests found")

    return render_template(
        "all_requests.html",
        travel_requests=travel_requests,
        maintenance_requests=maintenance_requests,
    )


@app.route("/filter-requests/<request_type>")
def filter_requests(request_type=None):
    requests = {
        "travel": TravelRequest,
        "maintenance": MaintenanceRequest,
        "doctor": DoctorRequest,
    }

    if request_type and request_type in requests:
        filtered_requests = requests[request_type].query.all()
        return render_template(
            "all_requests.html", requests=filtered_requests, request_type=request_type
        )
    else:
        return all_requests()


@app.route("/all-requests")
def all_requests():
    # Query the travel_requests table
    travel_requests = TravelRequest.query.all()
    maintenance_requests = MaintenanceRequest.query.all()

    # You can add queries for other request types and pass them to the template as well
    # doctor_requests = DoctorRequest.query.all()

    # Render a template and pass the query results to it
    return render_template(
        "all_requests.html",
        travel_requests=travel_requests,
        maintenance_requests=maintenance_requests,
    )


@app.route("/requests-made")
def requests_made():
    if "resident_id" not in session:
        return redirect(url_for("login"))

    resident_id = session["resident_id"]

    travel_requests = TravelRequest.query.filter_by(resident_id=resident_id).all()
    maintenance_requests = MaintenanceRequest.query.filter_by(
        resident_id=resident_id
    ).all()

    return render_template(
        "request-made.html",
        travel_requests=travel_requests,
        maintenance_requests=maintenance_requests,
    )


@app.route("/edit-request/<int:request_id>", methods=["GET", "POST"])
def edit_request(request_id):
    # Attempt to fetch the request from both tables
    travel_request_details = TravelRequest.query.get(request_id)
    maintenance_request_details = MaintenanceRequest.query.get(request_id)

    # Determine the type of request and choose the appropriate one
    request_details = (
        travel_request_details
        if travel_request_details
        else maintenance_request_details
    )
    is_maintenance_request = maintenance_request_details is not None

    if request.method == "POST":
        # Update the status for both types of requests
        request_details.status = request.form.get("status")

        # Update the date_completed only for maintenance requests
        if is_maintenance_request:
            date_completed = request.form.get("date_completed")
            if date_completed:
                request_details.date_completed = datetime.strptime(
                    date_completed, "%Y-%m-%d"
                ).date()

        db.session.commit()
        flash("Request updated successfully!", "success")
        return redirect(url_for("all_requests"))
    else:
        # Pass the request_details and a flag to indicate if it's a maintenance request
        return render_template(
            "edit_request.html",
            request=request_details,
            is_maintenance_request=is_maintenance_request,
        )


@app.route("/edit-maintenance-request/<int:request_id>", methods=["GET", "POST"])
def edit_maintenance_request(request_id):
    request_details = MaintenanceRequest.query.get_or_404(request_id)
    if request.method == "POST":
        # Process form data and update attributes
        db.session.commit()
        flash("Maintenance request updated successfully!", "success")
        return redirect(url_for("request_database"))
    else:
        return render_template(
            "edit_request.html", request=request_details, is_maintenance_request=True
        )


@app.route("/logout", methods=["POST"])
def logout():
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
