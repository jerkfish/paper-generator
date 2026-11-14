"""Model answers for the remaining normalization questions (V4 completion)."""
from __future__ import annotations

from ._blocks import p, schema, sub, table

ANSWERS = {
    "ICT450-2018-JUN-Q3": {
        "confidence": "high",
        "assumptions": ["The table is treated as one course with a repeating "
                        "list of enrolled students."],
        "blocks": [
            p("The table mixes course, tutor and student data. The student "
              "rows repeat for the course, so the data is flattened to one "
              "row per student before normalisation."),
            sub("a", 3, "Normal form of Table 1.0.", [
                "The table is in first normal form (1NF) when flattened to "
                "one row per student, because each cell is atomic and a key "
                "can be formed.",
                "It is not in 2NF or 3NF because student data depends only on "
                "StudentID, tutor data depends on CourseCode, and TutorName "
                "depends transitively on TutorID.",
            ]),
            sub("b", 7, "Dependency diagram and partial/transitive "
                "dependencies.", blocks=[
                    schema([
                        "CourseCode → CourseName, TutorID, TutorName",
                        "TutorID → TutorName",
                        "StudentID → StudentName, DOB, Gender",
                        "CourseCode, StudentID → LastAttendanceDate",
                    ], "Functional dependencies."),
                    p("Partial dependencies: CourseCode → CourseName/TutorID/"
                      "TutorName and StudentID → StudentName/DOB/Gender. "
                      "Transitive dependency: CourseCode → TutorID → "
                      "TutorName."),
                ]),
            sub("c", 10, "Normalise to 3NF.", blocks=[
                p("1NF: one row per course-student attendance; key "
                  "(CourseCode, StudentID)."),
                p("2NF: remove partial dependencies into COURSE, STUDENT and "
                  "ATTENDANCE."),
                schema([
                    "COURSE (CourseCode, CourseName, TutorID, TutorName)",
                    "STUDENT (StudentID, StudentName, DOB, Gender)",
                    "ATTENDANCE (CourseCode, StudentID, LastAttendanceDate)",
                ], "2NF relations."),
                p("3NF: remove TutorID → TutorName from COURSE."),
                schema([
                    "COURSE (CourseCode, CourseName, TutorID)",
                    "TUTOR (TutorID, TutorName)",
                    "STUDENT (StudentID, StudentName, DOB, Gender)",
                    "ATTENDANCE (CourseCode, StudentID, LastAttendanceDate)",
                ], "3NF relations."),
                table("3NF sample data: COURSE and TUTOR",
                      ["CourseCode", "CourseName", "TutorID", "TutorName"],
                      [["ICT450", "Database Design and Development",
                        "306612", "Professor Albus Dumbledore"]]),
            ]),
        ],
        "marking": [
            "a) 3 marks: 1NF identified, with reasons why 2NF/3NF fail.",
            "b) 7 marks: dependency diagram (3), partial dependencies (2), "
            "transitive dependency (2).",
            "c) 10 marks: 1NF (2), 2NF (4), 3NF (4).",
        ],
    },
    "ICT450-2019-JUN-Q4": {
        "confidence": "high",
        "assumptions": ["The receipt is treated as one header with repeating "
                        "menu lines; Amount = Quantity × Price."],
        "blocks": [
            p("The AB Bistro receipt contains one receipt header and a "
              "repeating list of menu items. It is flattened to one row per "
              "menu line."),
            sub("a", 3, "Normal form of the receipt.", [
                "The flattened receipt is in 1NF because each cell is atomic "
                "and the key (ReceiptNo, MenuID) can be formed.",
                "It is not in 2NF: receipt date/time/server/table/total "
                "depend only on ReceiptNo, while MenuDescription and Price "
                "depend only on MenuID.",
                "It is not in 3NF because ServerName depends transitively on "
                "ServerID.",
            ]),
            sub("b", 3, "Purpose of normalization.", [
                "Normalization removes redundant data and update anomalies by "
                "placing each fact in one table and linking tables with keys.",
            ]),
            sub("c", 14, "Normalise to 3NF.", blocks=[
                p("1NF: one row per receipt-menu line; key (ReceiptNo, "
                  "MenuID)."),
                schema([
                    "RECEIPT_1NF (ReceiptNo, ReceiptDate, ReceiptTime, "
                    "ServerID, ServerName, TableNo, MenuID, MenuDescription, "
                    "Quantity, Price, Amount, Total, Payment, Balance)",
                ], "1NF relation."),
                p("2NF: remove partial dependencies."),
                schema([
                    "RECEIPT (ReceiptNo, ReceiptDate, ReceiptTime, ServerID, "
                    "ServerName, TableNo, Total, Payment, Balance)",
                    "MENU (MenuID, MenuDescription, Price)",
                    "RECEIPT_ITEM (ReceiptNo, MenuID, Quantity, Amount)",
                ], "2NF relations."),
                p("3NF: remove ServerID → ServerName."),
                schema([
                    "SERVER (ServerID, ServerName)",
                    "RECEIPT (ReceiptNo, ReceiptDate, ReceiptTime, ServerID, "
                    "TableNo, Total, Payment, Balance)",
                    "MENU (MenuID, MenuDescription, Price)",
                    "RECEIPT_ITEM (ReceiptNo, MenuID, Quantity, Amount)",
                ], "3NF relations."),
                table("Sample receipt data",
                      ["ReceiptNo", "Date", "Server", "Table", "Total",
                       "Payment", "Balance"],
                      [["101", "17/01/2019", "Nurul Najwa", "30", "34.00",
                        "50.00", "16.00"]]),
                table("Sample menu data",
                      ["MenuID", "Description", "Price"],
                      [["M10", "Tomyam Thai", "10.00"],
                       ["M12", "Daging Masak Pedas", "7.00"],
                       ["D4", "Teh Ais", "2.50"]]),
            ]),
        ],
        "marking": [
            "a) 3 marks: 1NF identified, with 2NF and 3NF reasons.",
            "b) 3 marks: redundancy/anomaly purpose.",
            "c) 14 marks: 1NF (3), 2NF partial dependencies (5), 3NF "
            "transitive dependency (6).",
        ],
    },
    "ICT450-2022-FEB-Q3": {
        "confidence": "medium",
        "assumptions": ["The menu field is multi-valued; the reservation key "
                        "is (ReservationID, MenuID). Staff and customer names "
                        "depend on their IDs."],
        "blocks": [
            p("Table 4 is a hotel reservation form with repeating menu lines "
              "and repeated customer and staff data."),
            sub("a", 3, "Normal form of Table 4.", [
                "The table is in 1NF when flattened to one row per reservation "
                "menu line; each cell is atomic.",
                "It is not in 2NF because customer, staff and menu details "
                "depend on parts of the composite key.",
                "It is not in 3NF because MenuName and TypeOfCuisine depend "
                "on MenuID, which is not the whole key.",
            ]),
            sub("b", 6, "Relational schema, keys and dependencies.", blocks=[
                schema([
                    "RESERVATION (CustomerID, ReservationID, ReservationDate, "
                    "TimeSlot, FirstName, LastName, Email, PhoneNumber, "
                    "NumberOfGuests, StaffID, StaffName, CuisineType, MenuID, "
                    "MenuName)",
                ], "Flattened relation."),
                schema([
                    "CustomerID → FirstName, LastName, Email, PhoneNumber",
                    "StaffID → StaffName",
                    "MenuID → MenuName, CuisineType",
                    "ReservationID → ReservationDate, TimeSlot, CustomerID, "
                    "NumberOfGuests, StaffID",
                    "ReservationID, MenuID → (reservation menu line)",
                ], "Functional dependencies."),
            ]),
            sub("c", 11, "Normalise to 3NF.", blocks=[
                p("1NF: one row per reservation-menu line; key "
                  "(ReservationID, MenuID)."),
                p("2NF: remove customer, staff and menu partial dependencies."),
                schema([
                    "CUSTOMER (CustomerID, FirstName, LastName, Email, "
                    "PhoneNumber)",
                    "STAFF (StaffID, StaffName)",
                    "RESERVATION (ReservationID, ReservationDate, TimeSlot, "
                    "CustomerID, NumberOfGuests, StaffID)",
                    "MENU (MenuID, MenuName, CuisineType)",
                    "RESERVATION_MENU (ReservationID, MenuID)",
                ], "2NF/3NF relations."),
                p("3NF: MenuName and CuisineType depend on MenuID, so MENU is "
                  "already separated; no further transitive dependency "
                  "remains."),
                table("Sample 3NF data: CUSTOMER",
                      ["CustomerID", "FirstName", "LastName", "Email",
                       "Phone"],
                      [["A01", "Intan", "Nasa", "intan@gmail.com",
                        "017-12345678"],
                       ["A02", "Fatin", "Ruslan", "fatin@gmail.com", ""]]),
                table("Sample 3NF data: RESERVATION",
                      ["ReservationID", "Date", "TimeSlot", "CustomerID",
                       "Guests", "StaffID"],
                      [["R1", "19/02/2022", "8:00 PM", "A01", "2", "111"],
                       ["R3", "20/02/2022", "8:00 PM", "A01", "3", "222"]]),
            ]),
        ],
        "marking": [
            "a) 3 marks: 1NF and reasons why not 2NF/3NF.",
            "b) 6 marks: schema (2), key (2), dependencies (2).",
            "c) 11 marks: 1NF (2), 2NF (4), 3NF (5).",
        ],
    },
    "ICT450-2023-FEB-Q3": {
        "confidence": "medium",
        "assumptions": ["The curly braces in the printed schema denote a "
                        "repeating group of flight/destination attributes."],
        "blocks": [
            p("The boarding schema contains a repeating group of flight and "
              "destination attributes for each customer booking."),
            sub("a", 3, "Define normalization and its importance.", [
                "Normalization is the process of evaluating and correcting "
                "table structures to minimise redundancy and anomalies.",
                "It is important because it prevents insertion, update and "
                "deletion anomalies and keeps each fact in one place.",
            ]),
            sub("b", 6, "Three requirements for good normalized tables.", [
                "Each cell must be atomic and there must be no repeating "
                "groups; example: one row per boarding pass, not a list of "
                "flights in one cell.",
                "Every non-key attribute must depend on the whole primary "
                "key; example: customer name depends on CustIC, not on "
                "FlightID.",
                "There must be no transitive dependency; example: "
                "DestinationName must depend on DestinationID, not on "
                "FlightID through the destination.",
            ]),
            sub("c", 11, "Normalise to 3NF.", blocks=[
                p("1NF: expand the repeating group to one row per customer-"
                  "flight-date; key (CustIC, FlightID, DateDepart)."),
                p("2NF: remove customer, flight and destination partial "
                  "dependencies."),
                schema([
                    "CUSTOMER (CustIC, CustFirstName, CustLastName)",
                    "FLIGHT (FlightID, PlaneType, Capacity, DestinationID)",
                    "DESTINATION (DestinationID, DestinationName)",
                    "BOARDING (CustIC, FlightID, DateDepart, DateArrive, "
                    "TimeDepart, TimeArrive, Seat)",
                ], "2NF relations."),
                p("3NF: separate the flight schedule so date/time attributes "
                  "depend on FlightID and DateDepart, not on the passenger."),
                schema([
                    "CUSTOMER (CustIC, CustFirstName, CustLastName)",
                    "DESTINATION (DestinationID, DestinationName)",
                    "FLIGHT (FlightID, PlaneType, Capacity, DestinationID)",
                    "FLIGHT_SCHEDULE (FlightID, DateDepart, DateArrive, "
                    "TimeDepart, TimeArrive)",
                    "BOARDING (CustIC, FlightID, DateDepart, Seat)",
                ], "3NF relations."),
            ]),
        ],
        "marking": [
            "a) 3 marks: definition and importance.",
            "b) 6 marks: 2 marks for each requirement with example.",
            "c) 11 marks: 1NF (2), 2NF (4), 3NF (5).",
        ],
    },
    "ICT450-2023-JUL-Q3": {
        "confidence": "medium",
        "assumptions": ["The reservation form asset is a blank template; the "
                        "answer models one reservation with many menu lines "
                        "and one optional facility."],
        "blocks": [
            p("The reservation form stores a reservation header, a repeating "
              "list of menu items and one selected facility."),
            sub("a", 3, "Define normalization and its purpose.", [
                "Normalization is the staged process of removing repeating "
                "groups, partial dependencies and transitive dependencies "
                "from relations.",
                "Its purpose is to reduce redundancy and prevent insertion, "
                "update and deletion anomalies.",
            ]),
            sub("b", 6, "Three effects of poor database design.", [
                "Data redundancy — the same customer or menu data is stored "
                "many times.",
                "Update anomalies — a change must be repeated in several rows "
                "and can become inconsistent.",
                "Insertion/deletion anomalies — a new menu cannot be added "
                "without a reservation, or deleting a reservation removes "
                "the only menu record.",
            ]),
            sub("c", 11, "Normalise to 3NF.", blocks=[
                p("1NF: one row per reservation-menu line; key "
                  "(ReservationID, MenuCode)."),
                schema([
                    "RESERVATION (ReservationID, ReservationDate, CustomerID, "
                    "CustomerName, MenuCode, MenuName, MenuDescription, "
                    "Quantity, FacilityCode, FacilityName, "
                    "FacilityDescription)",
                ], "Flattened relation."),
                p("2NF: remove customer, menu and facility partial "
                  "dependencies."),
                schema([
                    "CUSTOMER (CustomerID, CustomerName)",
                    "FACILITY (FacilityCode, FacilityName, "
                    "FacilityDescription)",
                    "MENU (MenuCode, MenuName, MenuDescription)",
                    "RESERVATION (ReservationID, ReservationDate, CustomerID, "
                    "FacilityCode)",
                    "RESERVATION_MENU (ReservationID, MenuCode, Quantity)",
                ], "2NF/3NF relations."),
                p("3NF: the remaining non-key attributes depend on their "
                  "table keys; no transitive dependency remains."),
            ]),
        ],
        "marking": [
            "a) 3 marks: definition and purpose.",
            "b) 6 marks: 2 marks for each effect.",
            "c) 11 marks: 1NF (2), 2NF (4), 3NF (5).",
        ],
    },
    "ICT450-2024-JUL-Q3": {
        "confidence": "high",
        "assumptions": ["The invoice has no printed item ID; ItemName is "
                        "treated as the product identifier. The duplicate "
                        "Argan Oil line is a repeated purchase line."],
        "blocks": [
            p("The Sasa eStore invoice contains a repeated item list and "
              "member data. It is flattened to one row per invoice line."),
            sub("a", 3, "Normal form of Figure 1.", [
                "The invoice is in 1NF when flattened to one row per item; "
                "all values are atomic.",
                "It is not in 2NF because member details depend on MemberID, "
                "while item price depends on ItemName, not on the full invoice "
                "key.",
                "It is not in 3NF because MemberName and Address depend "
                "transitively on MemberID, and totals are repeated.",
            ]),
            sub("b", 6, "Primary key and dependencies.", blocks=[
                schema([
                    "INVOICE (InvoiceNo, InvoiceDate, MemberID, MemberName, "
                    "Address, ItemName, Quantity, UnitPrice, Amount, Total, "
                    "PaidAmount, BalanceDue)",
                ], "Flattened invoice relation."),
                schema([
                    "InvoiceNo → InvoiceDate, MemberID, Total, PaidAmount, "
                    "BalanceDue",
                    "MemberID → MemberName, Address",
                    "ItemName → UnitPrice",
                    "InvoiceNo, ItemName → Quantity, Amount",
                ], "Functional dependencies."),
            ]),
            sub("c", 11, "Normalise from 1NF to 3NF.", blocks=[
                p("1NF: one row per invoice item; key (InvoiceNo, ItemName)."),
                p("2NF: remove partial dependencies."),
                schema([
                    "INVOICE (InvoiceNo, InvoiceDate, MemberID, MemberName, "
                    "Address, Total, PaidAmount, BalanceDue)",
                    "ITEM (ItemName, UnitPrice)",
                    "INVOICE_ITEM (InvoiceNo, ItemName, Quantity, Amount)",
                ], "2NF relations."),
                p("3NF: remove MemberID → MemberName/Address."),
                schema([
                    "MEMBER (MemberID, MemberName, Address)",
                    "INVOICE (InvoiceNo, InvoiceDate, MemberID, Total, "
                    "PaidAmount, BalanceDue)",
                    "ITEM (ItemName, UnitPrice)",
                    "INVOICE_ITEM (InvoiceNo, ItemName, Quantity, Amount)",
                ], "3NF relations."),
                table("Sample 3NF data: ITEM",
                      ["ItemName", "UnitPrice"],
                      [["Green Deep Lip & Eye Remover", "65.00"],
                       ["Argan Oil Cleansing Foam", "49.00"],
                       ["10% Niacinamide Serum", "56.00"]]),
            ]),
        ],
        "marking": [
            "a) 3 marks: 1NF plus 2NF/3NF reasons.",
            "b) 6 marks: key (2), dependencies (4).",
            "c) 11 marks: 1NF (2), 2NF (4), 3NF (5).",
        ],
    },
    "ICT450-2025-FEB-Q3": {
        "confidence": "medium",
        "assumptions": ["The logbook has no printed order or customer ID; "
                        "OrderID and CustomerID are introduced as surrogate "
                        "keys for the normalized design."],
        "blocks": [
            p("The logbook records one row per customer visit, but the order "
              "list is a repeating group and customer/staff/menu data is "
              "repeated."),
            sub("a", 3, "Three problems in the logbook.", [
                "The “List of orders and Quantity” is a repeating group, so "
                "the table is not atomic.",
                "Customer, staff and menu details are duplicated, creating "
                "redundancy and update anomalies.",
                "Totals can be inconsistent because they are manually copied "
                "from the order lines.",
            ]),
            sub("b", 6, "Keys and dependencies.", blocks=[
                schema([
                    "LOGBOOK (Date, CustomerName, TotalOrders, OrderList, "
                    "TotalPayment, PaymentType, StaffName)",
                ], "Flattened logbook."),
                schema([
                    "Assumed OrderID is the order key",
                    "CustomerName → customer details",
                    "StaffName → staff details",
                    "MenuCode → MenuName, Price",
                    "OrderID → Date, CustomerName, TotalPayment, PaymentType, "
                    "StaffName",
                    "OrderID, MenuCode → Quantity",
                ], "Functional dependencies."),
            ]),
            sub("c", 11, "Normalise from 1NF to 3NF.", blocks=[
                p("1NF: one row per order item; use OrderID and MenuCode."),
                schema([
                    "ORDER (OrderID, Date, CustomerName, TotalPayment, "
                    "PaymentType, StaffName)",
                    "ORDER_ITEM (OrderID, MenuCode, Quantity)",
                    "MENU (MenuCode, MenuName, Price)",
                ], "1NF relations."),
                p("2NF: remove customer, staff and menu partial dependencies."),
                schema([
                    "CUSTOMER (CustomerName)",
                    "STAFF (StaffName)",
                    "MENU (MenuCode, MenuName, Price)",
                    "ORDER (OrderID, Date, CustomerName, StaffName, "
                    "PaymentType, TotalPayment)",
                    "ORDER_ITEM (OrderID, MenuCode, Quantity)",
                ], "2NF relations."),
                p("3NF: separate customer, staff and menu masters; no "
                  "transitive dependency remains."),
                schema([
                    "CUSTOMER (CustomerName)",
                    "STAFF (StaffName)",
                    "MENU (MenuCode, MenuName, Price)",
                    "ORDER (OrderID, Date, CustomerName, StaffName, "
                    "PaymentType, TotalPayment)",
                    "ORDER_ITEM (OrderID, MenuCode, Quantity)",
                ], "3NF relations."),
            ]),
        ],
        "marking": [
            "a) 3 marks: three problems stated.",
            "b) 6 marks: key and dependency identification.",
            "c) 11 marks: 1NF (2), 2NF (4), 3NF (5).",
        ],
    },
    "ICT450-2025-JUL-Q3": {
        "confidence": "high",
        "assumptions": ["An employee with no skill (302) has no row in the "
                        "associative table; 'Not complete yet' is treated as "
                        "a NULL completion date."],
        "blocks": [
            p("Table 3 mixes employee, department and skill data. The skill "
              "list repeats for employees with several skills, while some "
              "employees have no skill."),
            sub("a", 3, "Normal form of Table 3.", [
                "The flattened table is in 1NF because each cell is atomic and "
                "the key (StaffID, SkillID) can be formed for employees with "
                "skills.",
                "It is not in 2NF because StaffName, Position and Department "
                "depend only on StaffID, while SkillName depends only on "
                "SkillID.",
                "It is not in 3NF because DeptName depends on DeptID, which is "
                "not the whole key.",
            ]),
            sub("b", 6, "Keys and dependencies.", blocks=[
                schema([
                    "EMPLOYEE_SKILL (StaffID, StaffName, Position, DeptID, "
                    "DeptName, SkillID, SkillName, CompletionDate)",
                ], "Flattened relation."),
                schema([
                    "StaffID → StaffName, Position, DeptID",
                    "DeptID → DeptName",
                    "SkillID → SkillName",
                    "StaffID, SkillID → CompletionDate",
                ], "Functional dependencies."),
            ]),
            sub("c", 11, "Normalise to 3NF.", blocks=[
                p("1NF: one row per employee-skill certification; employee 302 "
                  "must be kept in EMPLOYEE with no skill row."),
                p("2NF: separate employee and skill partial dependencies."),
                schema([
                    "EMPLOYEE (StaffID, StaffName, Position, DeptID, "
                    "DeptName)",
                    "SKILL (SkillID, SkillName)",
                    "EMPLOYEE_SKILL (StaffID, SkillID, CompletionDate)",
                ], "2NF relations."),
                p("3NF: separate DeptID → DeptName."),
                schema([
                    "DEPARTMENT (DeptID, DeptName)",
                    "EMPLOYEE (StaffID, StaffName, Position, DeptID)",
                    "SKILL (SkillID, SkillName)",
                    "EMPLOYEE_SKILL (StaffID, SkillID, CompletionDate)",
                ], "3NF relations."),
                table("Sample employee data",
                      ["StaffID", "StaffName", "Position", "DeptID"],
                      [["304", "Intan Syafinaz", "Analyst", "D1"],
                       ["302", "Mohd Fikri Mohd Ali", "Developer", "D2"]]),
            ]),
        ],
        "marking": [
            "a) 3 marks: 1NF plus 2NF/3NF reasons.",
            "b) 6 marks: key and dependencies.",
            "c) 11 marks: 1NF (2), 2NF (4), 3NF (5).",
        ],
    },
    "ICT450-2026-FEB-Q3": {
        "confidence": "high",
        "assumptions": ["RegisterID identifies one registration; each "
                        "registration can list several skills. Years of "
                        "experience belongs to the registration-skill pair."],
        "blocks": [
            p("Table 1 repeats the registration and volunteer data for each "
              "skill, so the skill list is a repeating group."),
            sub("a", 3, "Two problems in Table 1.", [
                "RegisterID, RegisterDate, VolunteerID and VolunteerName repeat "
                "for every skill, creating redundancy.",
                "Skill and YearsOfExperience are stored in a repeating group "
                "rather than in a separate registration-skill relation.",
                "The blank VolunteerName cells also show inconsistent data "
                "entry.",
            ]),
            sub("b", 6, "Keys and dependencies.", blocks=[
                schema([
                    "REGISTRATION_SKILL (RegisterID, RegisterDate, "
                    "VolunteerID, VolunteerName, SkillID, SkillName, "
                    "YearsOfExperience)",
                ], "Flattened relation."),
                schema([
                    "RegisterID → RegisterDate, VolunteerID",
                    "VolunteerID → VolunteerName",
                    "SkillID → SkillName",
                    "RegisterID, SkillID → YearsOfExperience",
                ], "Functional dependencies."),
            ]),
            sub("c", 11, "Normalise to 3NF.", blocks=[
                p("1NF: one row per registration-skill pair; key (RegisterID, "
                  "SkillID)."),
                p("2NF: remove volunteer, registration and skill partial "
                  "dependencies."),
                schema([
                    "VOLUNTEER (VolunteerID, VolunteerName)",
                    "REGISTRATION (RegisterID, RegisterDate, VolunteerID)",
                    "SKILL (SkillID, SkillName)",
                    "REGISTRATION_SKILL (RegisterID, SkillID, "
                    "YearsOfExperience)",
                ], "2NF/3NF relations."),
                p("3NF: VolunteerName depends on VolunteerID and SkillName on "
                  "SkillID; no further transitive dependency remains."),
                table("Sample 3NF data: REGISTRATION",
                      ["RegisterID", "RegisterDate", "VolunteerID"],
                      [["101", "28/9/2025", "V15"],
                       ["102", "5/10/2025", "V17"],
                       ["103", "30/10/2025", "V20"]]),
                table("Sample 3NF data: REGISTRATION_SKILL",
                      ["RegisterID", "SkillID", "YearsOfExperience"],
                      [["101", "J1", "5"], ["101", "S2", "2"],
                       ["102", "M1", "25"], ["103", "W1", "10"]]),
            ]),
        ],
        "marking": [
            "a) 3 marks: two problems with reasons.",
            "b) 6 marks: key and dependencies.",
            "c) 11 marks: 1NF (2), 2NF (4), 3NF (5).",
        ],
    },
}
