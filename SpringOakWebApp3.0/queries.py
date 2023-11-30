import sqlite3
from werkzeug.security import check_password_hash


def queryTheDabase(query, args=None, fetchOne=False):
    connection = sqlite3.connect("springoak.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if args is None:
        cursor.execute(query)
    else:
        cursor.execute(query, args)
    results = cursor.fetchone() if fetchOne else cursor.fetchall()
    connection.commit()
    connection.close()
    return results


def addResident(firstName, lastName, roomNumber):
    queryTheDabase(
        "INSERT INTO resident (FirstName, LastName, RoomNumber) VALUES (?, ?, ?)",
        (firstName, lastName, roomNumber),
    )


def allRequests():
    return queryTheDabase(
        "SELECT Description, Category, FirstName, LastName, RoomNumber FROM request JOIN resident ON request.resident = resident.ID;"
    )


def allResidents():
    return queryTheDabase("SELECT FirstName, LastName, RoomNumber FROM resident")


def allVisitors(checkedIn=True):
    return queryTheDabase("SELECT FirstName, LastName, Resident FROM visitor")


def visitorInDatabase(firstName, lastName, email):
    result = queryTheDabase(
        "SELECT * FROM visitor WHERE FirstName = ? AND LastName = ? AND Email = ?",
        (firstName, lastName, email),
    )
    return len(result) != 0


def checkStaffCredentials(username, password):
    result = queryTheDabase(
        "SELECT Username, PasswordHash from STAFF WHERE username = ?", (username,), True
    )

    validCredentials = True
    if result is None:
        validCredentials = False
    else:
        if not check_password_hash(result["PasswordHash"], password):
            validCredentials = False
    return validCredentials


def addVisitor(firstName, lastName, residentName, date, phone, email):
    queryTheDabase(
        "INSERT INTO visitor (firstName, lastName, resident, date, phone, email) VALUES(?,?,?,?,?,?)",
        (firstName, lastName, residentName, date, phone, email),
    )


def removeVisitor(firstName, lastName, email):
    queryTheDabase(
        "DELETE FROM visitor WHERE FirstName = ? AND LastName = ? AND Email = ?",
        (firstName, lastName, email),
    )
