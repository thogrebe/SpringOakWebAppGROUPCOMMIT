import sqlite3
import string
import random
import queries as q
from werkzeug.security import generate_password_hash


def createTables():
    connection = sqlite3.connect("springoak.db")
    cursor = connection.cursor()
    with open("db-init.sql") as f:
        cursor.executescript(f.read())
    connection.close()


def makeStaff():
    first = ["Alyssia", "Crystal", "Menachem", "Ruth", "Tori"]
    last = ["M", "L", "R", "W", "H"]
    usernames = [x.lower() for x in first]
    hashes = [generate_password_hash(x) for x in first]

    connection = sqlite3.connect("springoak.db")
    cursor = connection.cursor()

    for first, last, username, hash in zip(first, last, usernames, hashes):
        cursor.execute(
            f"INSERT INTO staff (FirstName, LastName, Username, PasswordHash) VALUES (?,?,?,?)",
            (first, last, username, hash),
        )
    connection.commit()
    connection.close()


def mockData():
    firstNames = ["Alice", "Bob", "Chip", "Dale", "Errol"]
    lastNames = ["Andrews", "Brentley", "Coolidge", "Doolittle", "Engenschuck"]
    residentNames = ["P", "Q", "R", "S", "T"]

    def randomEmail():
        email = ""
        symbols = string.ascii_lowercase + string.digits
        length = random.randint(3, 10)
        for i in range(length):
            email += random.choice(symbols)
        return email.casefold() + "@example.com"

    def randomPhone():
        number = ""
        for i in range(10):
            number += random.choice(string.digits)
        return number[:3] + " " + number[3:6] + " " + number[6:]

    def randomDate():
        return (
            str(random.randint(1, 12))
            + "/"
            + str(random.randint(1, 31))
            + "/"
            + str(random.randint(1986, 2023))
        )

    for i in range(5):
        q.addVisitor(
            firstNames[i],
            lastNames[i],
            residentNames[i],
            randomDate(),
            randomPhone(),
            randomEmail(),
        )


def main():
    createTables()


if __name__ == "__main__":
    createTables()