"""Model answers for the SQL questions used in seeds 1–3."""
from __future__ import annotations

from ._blocks import callout, p, schema, sql, sub

ANSWERS = {
    "ICT450-2019-JUN-Q3": {
        "confidence": "high",
        "assumptions": [
            "The printed BOOKING schema is missing a comma between studID* "
            "and bookDate; the answer inserts the comma.",
            "Data types and sizes are not printed, so reasonable types are "
            "chosen and stated in the CREATE TABLE answer.",
            "The SQL is written in portable SQL; Oracle/MySQL may also accept "
            "MODIFY instead of ALTER COLUMN.",
        ],
        "blocks": [
            schema([
                "BRAND (brandID, brandName)",
                "BOOKING (bookID, equipID*, studID*, bookDate, returnDate)",
                "STUDENT (studID, studName, studAddr, studPhone)",
                "EQUIPMENT (equipID, equipName, equipPrice, category, "
                "brandID*, quantity, supplier)",
            ], "Relational schema used by the question."),
            sub("a", 3, "Create the BOOKING table.", blocks=[
                sql("""CREATE TABLE BOOKING (
    bookID      VARCHAR(10) NOT NULL,
    equipID     VARCHAR(10) NOT NULL,
    studID      VARCHAR(10) NOT NULL,
    bookDate    DATE,
    returnDate  DATE,
    PRIMARY KEY (bookID),
    FOREIGN KEY (equipID) REFERENCES EQUIPMENT (equipID),
    FOREIGN KEY (studID)  REFERENCES STUDENT (studID)
);"""),
            ]),
            sub("b", 3, "Increase equipment prices by 10%.", blocks=[
                sql("""UPDATE EQUIPMENT
SET equipPrice = equipPrice * 1.10;"""),
            ]),
            sub("c", 3, "Change the width of the student address column.",
                blocks=[
                    sql("""ALTER TABLE STUDENT
MODIFY studAddr VARCHAR(50);"""),
                    p("For SQL Server, the equivalent statement is "
                      "ALTER TABLE STUDENT ALTER COLUMN studAddr "
                      "VARCHAR(50)."),
                ]),
            sub("d", 3, "Equipments supplied by Al-Ikhsan in the racket or "
                "ball category, sorted by category.", blocks=[
                    sql("""SELECT *
FROM EQUIPMENT
WHERE supplier = 'Al-Ikhsan'
  AND category IN ('racket', 'ball')
ORDER BY category ASC;"""),
                ]),
            sub("e", 4, "Equipments that have not been booked by any "
                "student.", blocks=[
                    sql("""SELECT e.*
FROM EQUIPMENT e
WHERE NOT EXISTS (
    SELECT 1
    FROM BOOKING b
    WHERE b.equipID = e.equipID
);"""),
                    p("A LEFT JOIN with IS NULL is also correct: "
                      "SELECT e.* FROM EQUIPMENT e LEFT JOIN BOOKING b "
                      "ON e.equipID = b.equipID WHERE b.equipID IS NULL."),
                ]),
            sub("f", 4, "Number of equipment types under each brand; show "
                "only brands with more than five types.", blocks=[
                    sql("""SELECT brandID,
       COUNT(DISTINCT equipID) AS number_of_types
FROM EQUIPMENT
GROUP BY brandID
HAVING COUNT(DISTINCT equipID) > 5;"""),
                ]),
        ],
        "marking": [
            "a) 3 marks: CREATE TABLE with columns (1), primary key (1) and "
            "both foreign keys (1).",
            "b) 3 marks: correct UPDATE (2) and 10% calculation (1).",
            "c) 3 marks: correct ALTER TABLE (2) and VARCHAR(50) (1).",
            "d) 3 marks: supplier and category predicates (2), ORDER BY "
            "category (1).",
            "e) 4 marks: correct anti-join/not-exists logic (3), correct "
            "equipment output (1).",
            "f) 4 marks: GROUP BY brand (1), COUNT (1), HAVING > 5 (2).",
        ],
    },
    "ICT450-2019-DEC-Q3": {
        "confidence": "medium",
        "assumptions": [
            "The printed schema has no customer identifier in ACCOUNT or "
            "LOAN. The answer assumes ACCOUNT.custIC and LOAN.custIC are the "
            "foreign keys to CUSTOMER; without such a link the customer-level "
            "questions cannot be answered.",
            "“Melaka branch” is matched from BRANCH.branchAddress.",
            "The loan branch is the branch recorded in LOAN.branchCode.",
        ],
        "blocks": [
            schema([
                "BANK (bankCode, bankName, bankAddress)",
                "ACCOUNT (accNo, balance, accType, branchCode)",
                "LOAN (loanNo, amount, loanType, branchCode)",
                "CUSTOMER (custIC, custName, custAddress, branchCode)",
                "BRANCH (branchCode, branchAddress, bankCode)",
            ], "Relational schema used by the question."),
            callout("Schema note: the printed ACCOUNT and LOAN relations do "
                    "not show a customer identifier. The answers below assume "
                    "ACCOUNT.custIC and LOAN.custIC as foreign keys to "
                    "CUSTOMER (custIC), which is required to link a customer "
                    "to an account or loan."),
            sub("a", 3, "Create the ACCOUNT table.", blocks=[
                sql("""CREATE TABLE ACCOUNT (
    accNo       VARCHAR(20) NOT NULL,
    balance     DECIMAL(12,2),
    accType     VARCHAR(20),
    branchCode  VARCHAR(10),
    custIC      VARCHAR(20),
    PRIMARY KEY (accNo),
    FOREIGN KEY (branchCode) REFERENCES BRANCH (branchCode),
    FOREIGN KEY (custIC)     REFERENCES CUSTOMER (custIC)
);"""),
            ]),
            sub("b", 2, "Add the customer phone number attribute.", blocks=[
                sql("""ALTER TABLE CUSTOMER
ADD custPhone VARCHAR(20);"""),
            ]),
            sub("c", 2, "Total number of customers who opened an account at "
                "Aprilbank.", blocks=[
                    sql("""SELECT COUNT(DISTINCT c.custIC) AS "
                          "total_customers
FROM CUSTOMER c
JOIN ACCOUNT a ON a.custIC = c.custIC
JOIN BRANCH b  ON b.branchCode = a.branchCode
JOIN BANK bk   ON bk.bankCode = b.bankCode
WHERE bk.bankName = 'Aprilbank';"""),
                ]),
            sub("d", 3, "Customers with more than RM 30,000 in an account at "
                "the Melaka branch.", blocks=[
                    sql("""SELECT DISTINCT c.custIC, c.custName
FROM CUSTOMER c
JOIN ACCOUNT a ON a.custIC = c.custIC
JOIN BRANCH b  ON b.branchCode = a.branchCode
WHERE a.balance > 30000
  AND b.branchAddress LIKE '%Melaka%';"""),
                ]),
            sub("e", 3, "Customers with Personal or Housing loans, sorted by "
                "account type.", blocks=[
                    sql("""SELECT DISTINCT c.custIC, c.custName, a.accType
FROM CUSTOMER c
JOIN LOAN l    ON l.custIC = c.custIC
JOIN ACCOUNT a ON a.custIC = c.custIC
WHERE l.loanType IN ('Personal', 'Housing')
ORDER BY a.accType ASC;"""),
                ]),
            sub("f", 3, "Customers with an account whose names are neither "
                "Intan nor Ahmad.", blocks=[
                    sql("""SELECT DISTINCT c.custName
FROM CUSTOMER c
JOIN ACCOUNT a ON a.custIC = c.custIC
WHERE c.custName NOT IN ('Intan', 'Ahmad');"""),
                ]),
            sub("g", 4, "Total amount of personal loan for each branch.",
                blocks=[
                    sql("""SELECT branchCode,
       SUM(amount) AS total_personal_loan
FROM LOAN
WHERE loanType = 'Personal'
GROUP BY branchCode;"""),
                ]),
        ],
        "marking": [
            "a) 3 marks: CREATE TABLE (1), primary key (1), branch foreign "
            "key (1); the assumed customer foreign key is acceptable.",
            "b) 2 marks: ALTER TABLE (1) and custPhone attribute (1).",
            "c) 2 marks: COUNT with the Aprilbank join/filter.",
            "d) 3 marks: balance > 30000 (1), Melaka branch (1), correct "
            "customer output (1).",
            "e) 3 marks: loan-type predicate (1), customer join (1), ORDER BY "
            "account type (1).",
            "f) 3 marks: account join (1), NOT IN both names (2).",
            "g) 4 marks: Personal filter (1), SUM(amount) (1), GROUP BY "
            "branch (1), correct output (1).",
        ],
    },
    "ICT450-2024-JUL-Q4": {
        "confidence": "high",
        "assumptions": [
            "A candidate's faculty is the faculty of the student who is the "
            "candidate.",
            "A vote is represented by a VOTING row plus its "
            "VOTING_DETAILS rows; a student who has no VOTING_DETAILS row "
            "has not voted for a candidate.",
        ],
        "blocks": [
            schema([
                "STUDENT (StudentID, FirstName, LastName, PhoneNumber, "
                "FacultyID*)",
                "CANDIDATE (CandidateID, StudentID*)",
                "VOTING (VotingID, VotingDate, StudID*)",
                "VOTING_DETAILS (VotingID*, CandidateID*, VotingTime)",
                "FACULTY (FacultyID, FacultyName)",
            ], "Relational schema used by the question."),
            sub("a", 4, "Total number of candidates for each faculty.",
                blocks=[
                    sql("""SELECT f.FacultyID, f.FacultyName,
       COUNT(c.CandidateID) AS total_candidates
FROM FACULTY f
JOIN STUDENT s   ON s.FacultyID = f.FacultyID
JOIN CANDIDATE c ON c.StudentID = s.StudentID
GROUP BY f.FacultyID, f.FacultyName;"""),
                ]),
            sub("b", 4, "Students who do not vote for any candidate.",
                blocks=[
                    sql("""SELECT s.*
FROM STUDENT s
WHERE NOT EXISTS (
    SELECT 1
    FROM VOTING v
    JOIN VOTING_DETAILS vd ON vd.VotingID = v.VotingID
    WHERE v.StudID = s.StudentID
);"""),
                ]),
            sub("c", 4, "Total number of voters for each faculty.", blocks=[
                sql("""SELECT f.FacultyID, f.FacultyName,
       COUNT(DISTINCT v.StudID) AS total_voters
FROM FACULTY f
JOIN STUDENT s ON s.FacultyID = f.FacultyID
JOIN VOTING v  ON v.StudID = s.StudentID
GROUP BY f.FacultyID, f.FacultyName;"""),
            ]),
            sub("d", 4, "Full name of candidates with more than 500 votes.",
                blocks=[
                    sql("""SELECT c.CandidateID,
       CONCAT(s.FirstName, ' ', s.LastName) AS full_name,
       COUNT(vd.VotingID) AS total_votes
FROM CANDIDATE c
JOIN STUDENT s       ON s.StudentID = c.StudentID
JOIN VOTING_DETAILS vd ON vd.CandidateID = c.CandidateID
GROUP BY c.CandidateID, s.FirstName, s.LastName
HAVING COUNT(vd.VotingID) > 500;"""),
                    p("In Oracle, replace CONCAT(...) with "
                      "s.FirstName || ' ' || s.LastName."),
                ]),
            sub("e", 4, "Total number of students who vote for only one "
                "candidate.", blocks=[
                    sql("""SELECT COUNT(*) AS students_voting_once
FROM (
    SELECT v.StudID
    FROM VOTING v
    JOIN VOTING_DETAILS vd ON vd.VotingID = v.VotingID
    GROUP BY v.StudID
    HAVING COUNT(DISTINCT vd.CandidateID) = 1
) AS single_vote;"""),
                ]),
        ],
        "marking": [
            "a) 4 marks: candidate-student-faculty join (2), COUNT per "
            "faculty (2).",
            "b) 4 marks: anti-join/not-exists on voting details (3), correct "
            "student output (1).",
            "c) 4 marks: faculty-student-voting join (2), COUNT DISTINCT "
            "voters (2).",
            "d) 4 marks: candidate vote join (2), GROUP BY and HAVING > 500 "
            "(2).",
            "e) 4 marks: group votes by student (2), HAVING count = 1 and "
            "outer COUNT (2).",
        ],
    },
}
