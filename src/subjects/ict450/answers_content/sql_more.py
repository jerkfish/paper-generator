"""Model answers for the remaining SQL questions (V4 completion)."""
from __future__ import annotations

from ._blocks import p, schema, sql, sub

ANSWERS = {
    "ICT450-2018-DEC-Q3": {
        "confidence": "high",
        "assumptions": ["Data types are not printed; reasonable types are "
                        "chosen. Dates use ISO literals in the examples."],
        "blocks": [
            schema([
                "TEAM (TEAM_ID, TEAM_NAME)",
                "GAME (GAME_ID, GAME_NAME)",
                "FOOTBALL (FOOTBALL_ID, TEAM_ID*, GAME_ID*, DATE, TIME, "
                "LOCATION)",
                "PLAYER (PLAYER_ID, P_NAME, ADDRESS, PHONE_NO, SALARY, "
                "POSITION, TEAM_ID*)",
            ], "Football league schema."),
            sub("a", 3, "Create the PLAYER table with integrity requirements.",
                blocks=[sql("""CREATE TABLE PLAYER (
    PLAYER_ID   VARCHAR(10) NOT NULL,
    P_NAME      VARCHAR(60) NOT NULL,
    ADDRESS     VARCHAR(150),
    PHONE_NO    VARCHAR(20),
    SALARY      DECIMAL(12,2) CHECK (SALARY >= 0),
    POSITION    VARCHAR(30),
    TEAM_ID     VARCHAR(10) NOT NULL,
    PRIMARY KEY (PLAYER_ID),
    FOREIGN KEY (TEAM_ID) REFERENCES TEAM (TEAM_ID)
);""")]),
            sub("b", 2, "Insert the specified player row.", blocks=[
                sql("""INSERT INTO PLAYER
(PLAYER_ID, P_NAME, ADDRESS, PHONE_NO, SALARY, POSITION, TEAM_ID)
VALUES
('10067', 'Safiq Rahim',
 'No.168, Damai Country Height, 40100, Shah Alam, Selangor',
 '019-3451212', 30000.00, 'Defence', 'FAM326');"""),
            ]),
            sub("c", 2, "Give strikers of The Red Warrior a 10% increment.",
                blocks=[sql("""UPDATE PLAYER
SET SALARY = SALARY * 1.10
WHERE POSITION = 'Striker'
  AND TEAM_ID = (SELECT TEAM_ID
                 FROM TEAM
                 WHERE TEAM_NAME = 'The Red Warrior');""")]),
            sub("d", 3, "Teams that played at Bukit Jalil in May 2018.", blocks=[
                sql("""SELECT DISTINCT t.*
FROM TEAM t
JOIN FOOTBALL f ON f.TEAM_ID = t.TEAM_ID
WHERE f.LOCATION = 'Bukit Jalil National Stadium'
  AND f.DATE BETWEEN DATE '2018-05-01' AND DATE '2018-05-31';"""),
            ]),
            sub("e", 3, "Number of games in the first quarter of 2018.", blocks=[
                sql("""SELECT COUNT(DISTINCT GAME_ID) AS total_games
FROM FOOTBALL
WHERE DATE BETWEEN DATE '2018-01-01' AND DATE '2018-03-31';"""),
            ]),
            sub("f", 3, "Number of games played by each team.", blocks=[
                sql("""SELECT TEAM_ID, COUNT(DISTINCT GAME_ID) AS games_played
FROM FOOTBALL
GROUP BY TEAM_ID;"""),
            ]),
            sub("g", 4, "Teams and players at Merdeka Stadium with salary "
                "2000 or 3000.", blocks=[
                    sql("""SELECT DISTINCT t.TEAM_NAME, p.P_NAME
FROM TEAM t
JOIN PLAYER p   ON p.TEAM_ID = t.TEAM_ID
JOIN FOOTBALL f ON f.TEAM_ID = t.TEAM_ID
WHERE f.LOCATION = 'Merdeka Stadium'
  AND p.SALARY IN (2000, 3000);"""),
                ]),
        ],
        "marking": [
            "a) 3 marks: columns (1), primary key (1), foreign key (1).",
            "b) 2 marks: correct INSERT with all values.",
            "c) 2 marks: UPDATE with striker/team predicate and 10%.",
            "d) 3 marks: team-football join (2), location/date filter (1).",
            "e) 3 marks: COUNT DISTINCT game and Q1 date range.",
            "f) 3 marks: GROUP BY team and COUNT DISTINCT game.",
            "g) 4 marks: three-table join (2), location filter (1), salary "
            "IN (1).",
        ],
    },
    "ICT450-2022-FEB-Q4": {
        "confidence": "high",
        "assumptions": ["Publisher and author names are matched exactly as "
                        "printed in the schema."],
        "blocks": [
            schema([
                "PUBLISHER (PublisherName, City, State, Country, PhoneNum)",
                "AUTHOR (AuthorNum, AuthorName)",
                "BOOK (ISBN, BookName, PublicationYear, AuthorNum, "
                "PublisherName)",
                "CUSTOMER (CustNum, CustName, Street, City, State, Country, "
                "Email)",
                "ORDER (OrderID, ISBN, CustNum, Date, Quantity)",
            ], "Publishing schema."),
            sub("a", 4, "Create the BOOK table.", blocks=[sql("""CREATE TABLE BOOK (
    ISBN             VARCHAR(20) NOT NULL,
    BookName         VARCHAR(150) NOT NULL,
    PublicationYear  NUMBER(4),
    AuthorNum        NUMBER(10),
    PublisherName    VARCHAR(100),
    PRIMARY KEY (ISBN),
    FOREIGN KEY (AuthorNum) REFERENCES AUTHOR (AuthorNum),
    FOREIGN KEY (PublisherName) REFERENCES PUBLISHER (PublisherName)
);""")]),
            sub("b", 4, "Books by John Wiley & Sons Inc and Pustaka Berhad.",
                blocks=[sql("""SELECT b.ISBN, b.BookName, a.AuthorName
FROM BOOK b
JOIN AUTHOR a ON a.AuthorNum = b.AuthorNum
WHERE b.PublisherName IN ('John Wiley & Sons Inc', 'Pustaka Berhad')
ORDER BY b.BookName DESC;""")]),
            sub("c", 4, "Books published in 2021 by Pustaka Trading in Jasin, "
                "Melaka.", blocks=[sql("""SELECT COUNT(*) AS total_books
FROM BOOK b
JOIN PUBLISHER p ON p.PublisherName = b.PublisherName
WHERE b.PublicationYear = 2021
  AND p.PublisherName = 'Pustaka Trading'
  AND p.City = 'Jasin'
  AND p.State = 'Melaka';""")]),
            sub("d", 4, "Publisher that published more than 50 books.", blocks=[
                sql("""SELECT PublisherName, COUNT(*) AS total_books
FROM BOOK
GROUP BY PublisherName
HAVING COUNT(*) > 50;"""),
            ]),
            sub("e", 4, "Book name with total orders more than 3.", blocks=[
                sql("""SELECT b.BookName, SUM(o.Quantity) AS total_ordered
FROM BOOK b
JOIN "ORDER" o ON o.ISBN = b.ISBN
GROUP BY b.ISBN, b.BookName
HAVING SUM(o.Quantity) > 3;"""),
            ]),
        ],
        "marking": [
            "a) 4 marks: columns/types (2), primary key (1), foreign keys (1).",
            "b) 4 marks: joins (2), IN filter (1), descending order (1).",
            "c) 4 marks: joins (2), year/city/state filters (2).",
            "d) 4 marks: GROUP BY publisher and HAVING > 50.",
            "e) 4 marks: join (2), SUM/GROUP BY/HAVING (2).",
        ],
    },
    "ICT450-2023-FEB-Q4": {
        "confidence": "high",
        "assumptions": ["Status is limited to 'delivered' or "
                        "'unsuccessful' by a check constraint."],
        "blocks": [
            schema([
                "RIDER (riderID, riderName, startDate, hpNum)",
                "CUSTOMER (icNum, custName, custPhone, custAddress)",
                "DELIVERY (packageID, dateDeliver, riderID, icNum, status)",
            ], "Ninja Package schema."),
            sub("a", 4, "Create the DELIVERY table.", blocks=[sql("""CREATE TABLE DELIVERY (
    packageID    VARCHAR(10) NOT NULL,
    dateDeliver  DATE,
    riderID      VARCHAR(10) NOT NULL,
    icNum        VARCHAR(20) NOT NULL,
    status       VARCHAR(15) NOT NULL
                 CHECK (status IN ('delivered', 'unsuccessful')),
    PRIMARY KEY (packageID),
    FOREIGN KEY (riderID) REFERENCES RIDER (riderID),
    FOREIGN KEY (icNum) REFERENCES CUSTOMER (icNum)
);""")]),
            sub("b", 4, "Customers successfully receiving packages in November "
                "2022.", blocks=[sql("""SELECT COUNT(DISTINCT icNum) AS "
                                     "successful_customers
FROM DELIVERY
WHERE status = 'delivered'
  AND dateDeliver BETWEEN DATE '2022-11-01' AND DATE '2022-11-30';""")]),
            sub("c", 4, "Unsuccessful deliveries per rider.", blocks=[
                sql("""SELECT riderID, COUNT(*) AS unsuccessful_deliveries
FROM DELIVERY
WHERE status = 'unsuccessful'
GROUP BY riderID;"""),
            ]),
            sub("d", 4, "Rider names that made at least one delivery.", blocks=[
                sql("""SELECT DISTINCT r.riderName
FROM RIDER r
JOIN DELIVERY d ON d.riderID = r.riderID;"""),
            ]),
            sub("e", 4, "Produce Package ID, Customer Name and Status.", blocks=[
                sql("""SELECT d.packageID, c.custName, d.status
FROM DELIVERY d
JOIN CUSTOMER c ON c.icNum = d.icNum
WHERE d.status = 'delivered';"""),
            ]),
        ],
        "marking": [
            "a) 4 marks: columns (1), primary key (1), both foreign keys (1), "
            "status check (1).",
            "b) 4 marks: delivered filter (1), date range (1), COUNT DISTINCT "
            "(2).",
            "c) 4 marks: unsuccessful filter (2), GROUP BY rider (2).",
            "d) 4 marks: rider-delivery join and DISTINCT names.",
            "e) 4 marks: join (2), selected columns (1), status filter (1).",
        ],
    },
    "ICT450-2023-JUL-Q4": {
        "confidence": "high",
        "assumptions": ["APPLYLOAN is an associative entity between CLIENT "
                        "and LOAN with a composite key."],
        "blocks": [
            schema([
                "DEPARTMENT (DeptID, DeptName)",
                "APPLYLOAN (ClientNum, LoanID, LoanTotal, LoanRemainder, "
                "LoanDate)",
                "LOAN (LoanID, LoanType, StaffID)",
                "CLIENT (ClientNum, ClientName, ClientAddress, ClientPhoneNum)",
                "OFFICER (StaffID, StaffName, DeptID)",
            ], "Loan database schema."),
            sub("a", 4, "Create the APPLYLOAN table.", blocks=[sql("""CREATE TABLE APPLYLOAN (
    ClientNum      VARCHAR(10) NOT NULL,
    LoanID         VARCHAR(10) NOT NULL,
    LoanTotal      DECIMAL(12,2),
    LoanRemainder  DECIMAL(12,2),
    LoanDate       DATE,
    PRIMARY KEY (ClientNum, LoanID),
    FOREIGN KEY (ClientNum) REFERENCES CLIENT (ClientNum),
    FOREIGN KEY (LoanID) REFERENCES LOAN (LoanID)
);""")]),
            sub("b", 4, "Client names with a personal loan, using a subquery.",
                blocks=[sql("""SELECT ClientName
FROM CLIENT
WHERE ClientNum IN (
    SELECT ClientNum
    FROM APPLYLOAN
    WHERE LoanID IN (
        SELECT LoanID
        FROM LOAN
        WHERE LoanType = 'Personal'
    )
);""")]),
            sub("c", 4, "Total loan from 2021 until 2023.", blocks=[sql("""SELECT SUM(LoanTotal) AS total_loan
FROM APPLYLOAN
WHERE LoanDate BETWEEN DATE '2021-01-01' AND DATE '2023-12-31';""")]),
            sub("d", 4, "Officers managing housing loans in the finance "
                "department.", blocks=[sql("""SELECT DISTINCT o.StaffName
FROM OFFICER o
JOIN LOAN l      ON l.StaffID = o.StaffID
JOIN DEPARTMENT d ON d.DeptID = o.DeptID
WHERE l.LoanType = 'Housing'
  AND d.DeptName = 'Finance';""")]),
            sub("e", 4, "Total loan for each loan type.", blocks=[sql("""SELECT l.LoanType, SUM(a.LoanTotal) AS total_loan
FROM LOAN l
JOIN APPLYLOAN a ON a.LoanID = l.LoanID
GROUP BY l.LoanType;""")]),
        ],
        "marking": [
            "a) 4 marks: columns (1), composite primary key (1), both foreign "
            "keys (2).",
            "b) 4 marks: nested subqueries and personal-loan filter.",
            "c) 4 marks: SUM and date range.",
            "d) 4 marks: three-table join, housing and finance filters.",
            "e) 4 marks: join, GROUP BY loan type, SUM.",
        ],
    },
    "ICT450-2024-JAN-Q4": {
        "confidence": "high",
        "assumptions": ["DateRelease is stored as a date; 'most reviews' is "
                        "answered with a top-1 ordered query."],
        "blocks": [
            schema([
                "MOVIE (MovieID, MovieName, Genre, DateRelease, NetProfit, "
                "DirectorID*)",
                "DIRECTOR (DirectorID, DirectorName, Nationality)",
                "REVIEW (ReviewID, Description, MovieID*, ReviewerID*)",
                "REVIEWER (ReviewerID, ReviewerName)",
            ], "Movie database schema."),
            sub("a", 4, "Movies released from 2021 until 2023.", blocks=[
                sql("""SELECT *
FROM MOVIE
WHERE DateRelease BETWEEN DATE '2021-01-01' AND DATE '2023-12-31';"""),
            ]),
            sub("b", 4, "Total movies directed by Malaysian directors.", blocks=[
                sql("""SELECT COUNT(*) AS total_movies
FROM MOVIE m
JOIN DIRECTOR d ON d.DirectorID = m.DirectorID
WHERE d.Nationality = 'Malaysian';"""),
            ]),
            sub("c", 4, "Average net profit for each genre.", blocks=[
                sql("""SELECT Genre, AVG(NetProfit) AS "Average Net Profit"
FROM MOVIE
GROUP BY Genre;"""),
            ]),
            sub("d", 4, "Reviewers with more than two reviews.", blocks=[
                sql("""SELECT r.ReviewerName
FROM REVIEWER r
JOIN REVIEW v ON v.ReviewerID = r.ReviewerID
GROUP BY r.ReviewerID, r.ReviewerName
HAVING COUNT(*) > 2;"""),
            ]),
            sub("e", 4, "Movie that received the most reviews.", blocks=[
                sql("""SELECT m.MovieName
FROM MOVIE m
JOIN REVIEW v ON v.MovieID = m.MovieID
GROUP BY m.MovieID, m.MovieName
ORDER BY COUNT(*) DESC
FETCH FIRST 1 ROW ONLY;"""),
                p("MySQL: replace FETCH FIRST 1 ROW ONLY with LIMIT 1."),
            ]),
        ],
        "marking": [
            "a) 4 marks: date range and SELECT.",
            "b) 4 marks: movie-director join and Malaysian filter.",
            "c) 4 marks: AVG, GROUP BY genre and alias.",
            "d) 4 marks: join, GROUP BY reviewer, HAVING > 2.",
            "e) 4 marks: join, COUNT, descending order and top-1.",
        ],
    },
    "ICT450-2025-FEB-Q4": {
        "confidence": "high",
        "assumptions": ["TripDate is the date used for the February/March "
                        "filters."],
        "blocks": [
            schema([
                "CUSTOMERS (CustomerID, FirstName, LastName, PhoneNumber)",
                "BOOKING (BookingID, BookingDate, NumberOfPax, TripDate, "
                "CustomerID*, GuideID*, PackageID*)",
                "GUIDE (GuideID, GuideName, BasicSalary, HireDate)",
                "PACKAGE (PackageID, PackageName, PricePerPax, PackageDetails)",
            ], "e-Travel schema."),
            sub("a", 4, "Total number of trips for each date.", blocks=[
                sql("""SELECT TripDate, COUNT(*) AS total_trips
FROM BOOKING
GROUP BY TripDate;"""),
            ]),
            sub("b", 4, "Customer with the highest number of bookings.", blocks=[
                sql("""SELECT c.*
FROM CUSTOMERS c
JOIN BOOKING b ON b.CustomerID = c.CustomerID
GROUP BY c.CustomerID, c.FirstName, c.LastName, c.PhoneNumber
ORDER BY COUNT(*) DESC
FETCH FIRST 1 ROW ONLY;"""),
            ]),
            sub("c", 4, "Increase 10% salary for guides on a February 2025 "
                "trip.", blocks=[sql("""UPDATE GUIDE
SET BasicSalary = BasicSalary * 1.10
WHERE GuideID IN (
    SELECT GuideID
    FROM BOOKING
    WHERE TripDate BETWEEN DATE '2025-02-01' AND DATE '2025-02-28'
);""")]),
            sub("d", 4, "Packages booked more than 70 times.", blocks=[
                sql("""SELECT p.PackageName
FROM PACKAGE p
JOIN BOOKING b ON b.PackageID = p.PackageID
GROUP BY p.PackageID, p.PackageName
HAVING COUNT(*) > 70;"""),
            ]),
            sub("e", 4, "Customers who booked between February and March "
                "2025.", blocks=[sql("""SELECT COUNT(DISTINCT CustomerID) AS total_customers
FROM BOOKING
WHERE TripDate BETWEEN DATE '2025-02-01' AND DATE '2025-03-31';""")]),
        ],
        "marking": [
            "a) 4 marks: GROUP BY date and COUNT.",
            "b) 4 marks: join, GROUP BY customer, descending order/top-1.",
            "c) 4 marks: UPDATE, 10%, February subquery.",
            "d) 4 marks: join, GROUP BY package, HAVING > 70.",
            "e) 4 marks: COUNT DISTINCT and date range.",
        ],
    },
    "ICT450-2025-JUL-Q4": {
        "confidence": "high",
        "assumptions": ["Total charge is AssignHours multiplied by the "
                        "employee's JobChargeHour."],
        "blocks": [
            schema([
                "EMPLOYEE (EmpID, EmpFirstName, EmpLastName, EmpHireDate, "
                "JobCode)",
                "JOB (JobCode, JobName, JobChargeHour)",
                "PROJECT (ProjCode, ProjName)",
                "ASSIGN (AssignID, AssignDate, AssignHours, ProjCode, EmpID)",
            ], "XY Company schema."),
            sub("a", 4, "Project names assigned from January to April 2025.",
                blocks=[sql("""SELECT DISTINCT p.ProjName
FROM PROJECT p
JOIN ASSIGN a ON a.ProjCode = p.ProjCode
WHERE a.AssignDate BETWEEN DATE '2025-01-01' AND DATE '2025-04-30';""")]),
            sub("b", 5, "Total charge for each employee.", blocks=[sql("""SELECT e.EmpID,
       e.EmpFirstName || ' ' || e.EmpLastName AS EmployeeName,
       SUM(a.AssignHours * j.JobChargeHour) AS "Total Charge"
FROM EMPLOYEE e
JOIN ASSIGN a ON a.EmpID = e.EmpID
JOIN JOB j    ON j.JobCode = e.JobCode
GROUP BY e.EmpID, e.EmpFirstName, e.EmpLastName;""")]),
            sub("c", 5, "Employees assigned to more than two projects.", blocks=[
                sql("""SELECT e.EmpFirstName, e.EmpLastName
FROM EMPLOYEE e
JOIN ASSIGN a ON a.EmpID = e.EmpID
GROUP BY e.EmpID, e.EmpFirstName, e.EmpLastName
HAVING COUNT(DISTINCT a.ProjCode) > 2;"""),
            ]),
            sub("d", 6, "Job name with charge RM50 and more than 10 "
                "employees, using a subquery.", blocks=[
                    sql("""SELECT JobName
FROM JOB
WHERE JobChargeHour = 50
  AND JobCode IN (
      SELECT JobCode
      FROM EMPLOYEE
      GROUP BY JobCode
      HAVING COUNT(*) > 10
  );"""),
                ]),
        ],
        "marking": [
            "a) 4 marks: project-assign join and date filter.",
            "b) 5 marks: joins (2), hours × rate (2), alias/grouping (1).",
            "c) 5 marks: join (2), GROUP BY employee and HAVING count > 2 (3).",
            "d) 6 marks: job filter (2), subquery grouping (2), HAVING > 10 "
            "(2).",
        ],
    },
    "ICT450-2026-FEB-Q4": {
        "confidence": "high",
        "assumptions": ["Mech_Salary is numeric and Center_City stores the "
                        "city name."],
        "blocks": [
            schema([
                "CENTER (Center_ID, Center_Name, Center_City)",
                "MECHANIC (Mech_ID, Mech_Name, Mech_Specialty, Mech_Salary, "
                "Center_ID*)",
                "CUSTOMER (Cust_ID, Cust_Name, Cust_CarModel)",
                "SERVICE (Service_ID, Service_Date, Mech_ID*, Cust_ID*)",
            ], "Mechanic center schema."),
            sub("a", 4, "Create the MECHANIC table.", blocks=[sql("""CREATE TABLE MECHANIC (
    Mech_ID        VARCHAR(10) NOT NULL,
    Mech_Name      VARCHAR(60) NOT NULL,
    Mech_Specialty VARCHAR(30),
    Mech_Salary    DECIMAL(12,2),
    Center_ID      VARCHAR(10),
    PRIMARY KEY (Mech_ID),
    FOREIGN KEY (Center_ID) REFERENCES CENTER (Center_ID)
);""")]),
            sub("b", 4, "ENGINE mechanics earning more than RM5000, sorted by "
                "salary descending.", blocks=[sql("""SELECT Mech_Name, Mech_Salary
FROM MECHANIC
WHERE Mech_Specialty = 'ENGINE'
  AND Mech_Salary > 5000
ORDER BY Mech_Salary DESC;""")]),
            sub("c", 6, "Different customers served at Melaka centers.", blocks=[
                sql("""SELECT COUNT(DISTINCT s.Cust_ID) AS total_customers
FROM SERVICE s
JOIN MECHANIC m ON m.Mech_ID = s.Mech_ID
JOIN CENTER c   ON c.Center_ID = m.Center_ID
WHERE c.Center_City = 'Melaka';"""),
            ]),
            sub("d", 6, "Center and mechanic with the highest salary, using a "
                "subquery.", blocks=[sql("""SELECT c.Center_Name, c.Center_City, m.Mech_Name
FROM CENTER c
JOIN MECHANIC m ON m.Center_ID = c.Center_ID
WHERE m.Mech_Salary = (
    SELECT MAX(Mech_Salary)
    FROM MECHANIC
);""")]),
        ],
        "marking": [
            "a) 4 marks: columns (2), primary key (1), foreign key (1).",
            "b) 4 marks: specialty (1), salary filter (1), ORDER BY (2).",
            "c) 6 marks: three-table join (3), Melaka filter (1), COUNT "
            "DISTINCT (2).",
            "d) 6 marks: join (2), MAX subquery (3), selected columns (1).",
        ],
    },
    "ICT450-2018-JUN-Q4": {
        "confidence": "medium",
        "assumptions": ["The printed question total is 14 and several "
                        "sub-parts have no printed mark; part (h)'s SQL "
                        "statement is missing from the extraction."],
        "blocks": [
            schema([
                "STUDENT (StudID, StudFName, Programme, GPA)",
                "COURSE (CourseID, CourseName, Department, CreditHour)",
                "OFFERED (CourseID, InstructorID, Semester, Year, Location)",
                "INSTRUCTOR (InstructorID, Name, Department)",
                "ENROLLED (StudID, CourseID, Semester, Year, Grade)",
            ], "Student course schema."),
            sub("a", 3, "Create the ENROLLED table.", blocks=[sql("""CREATE TABLE ENROLLED (
    StudID    VARCHAR(10) NOT NULL,
    CourseID  VARCHAR(10) NOT NULL,
    Semester  VARCHAR(10) NOT NULL,
    Year      NUMBER(4) NOT NULL,
    Grade     VARCHAR(2),
    PRIMARY KEY (StudID, CourseID, Semester, Year),
    FOREIGN KEY (StudID) REFERENCES STUDENT (StudID),
    FOREIGN KEY (CourseID) REFERENCES COURSE (CourseID)
);""")]),
            sub("b", 2, "Insert the new course.", blocks=[sql("""INSERT INTO COURSE
(CourseID, CourseName, Department, CreditHour)
VALUES ('ITS432', 'Database Design and Application',
        'Information Technology', 3);""")]),
            sub("c", 0, "Students whose names begin with Siti and who are in "
                "Data Science.", blocks=[sql("""SELECT StudFName
FROM STUDENT
WHERE StudFName LIKE 'Siti%'
  AND Programme = 'Data Science';""")]),
            sub("d", 2, "Add a last-name attribute to STUDENT.", blocks=[
                sql("""ALTER TABLE STUDENT
ADD StudLName VARCHAR(50);"""),
            ]),
            sub("e", 2, "Instructors and the course names they teach.", blocks=[
                sql("""SELECT i.*, c.CourseName
FROM INSTRUCTOR i
JOIN OFFERED o ON o.InstructorID = i.InstructorID
JOIN COURSE c  ON c.CourseID = o.CourseID;"""),
            ]),
            sub("f", 0, "Name and grade of students who took ELC501 with A or "
                "B.", blocks=[sql("""SELECT s.StudFName, e.Grade
FROM STUDENT s
JOIN ENROLLED e ON e.StudID = s.StudID
WHERE e.CourseID = 'ELC501'
  AND e.Grade IN ('A', 'B');""")]),
            sub("g", 2, "Number of instructors who taught four-credit courses.",
                blocks=[sql("""SELECT COUNT(DISTINCT o.InstructorID) AS total_instructors
FROM OFFERED o
JOIN COURSE c ON c.CourseID = o.CourseID
WHERE c.CreditHour = 4;""")]),
            sub("h", 3, "Result of the printed SQL statement.", [
                "The statement itself was not included in the extracted "
                "question text, so its result cannot be determined without "
                "inventing the query. This is recorded as an extraction gap.",
            ]),
        ],
        "marking": [
            "a) 3 marks: columns, composite primary key and foreign keys.",
            "b) 2 marks: correct INSERT.",
            "c) 0 marks printed; answer shows the LIKE/Programme query.",
            "d) 2 marks: ALTER TABLE ADD column.",
            "e) 2 marks: instructor-offered-course join.",
            "f) 0 marks printed; answer shows the ELC501/grade query.",
            "g) 2 marks: DISTINCT instructor count with credit-hour filter.",
            "h) 3 marks: the query was missing from the extraction, so no "
            "result is invented.",
        ],
    },
}
