CREATE TABLE IF NOT EXISTS visitor(
    ID INTEGER PRIMARY KEY,
    FirstName NOT NULL,
    LastName NOT NULL,
    Resident NULL,
    date NOT NULL,
    Phone NULL,
    Email NULL,
    FOREIGN KEY (Resident) references Resident(ID)
);

CREATE TABLE IF NOT EXISTS staff(
    ID INTEGER PRIMARY KEY,
    FirstName NOT NULL,
    LastName NOT NULL,
    Phone NULL,
    Email NULL,
    Username NOT NULL,
    PasswordHash NOT NULL
);

CREATE TABLE IF NOT EXISTS resident(
    ID INTEGER PRIMARY KEY,
    FirstName,
    LastName,
    RoomNumber,
    DOB,
    Arrival,
    Emergency contact,
    Insurance
);

CREATE TABLE IF NOT EXISTS request(
    ID INTEGER PRIMARY KEY,
    Resident NOT NULL,
    Description NOT NULL,
    Category NULL,
    FOREIGN KEY (Resident) references Resident(ID)
);

SELECT
    Description,
    Category,
    FirstName,
    LastName,
    RoomNumber
FROM
    request
    JOIN resident ON request.resident = resident.ID;