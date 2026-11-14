"""Model answers for the remaining concepts questions (V4 completion)."""
from __future__ import annotations

from ._blocks import erd, p, sub

TRUCK_ERD = {
    "width": 980,
    "height": 470,
    "entities": [
        {"id": "BASE", "name": "BASE", "x": 60, "y": 60,
         "attrs": [{"name": "Base_Code", "key": "PK"},
                   {"name": "Base_City"}, {"name": "Base_State"},
                   {"name": "Base_Postcode"}, {"name": "Base_Manager"}]},
        {"id": "TRUCK", "name": "TRUCK", "x": 390, "y": 210,
         "attrs": [{"name": "Truck_Num", "key": "PK"},
                   {"name": "Truck_Miles"}, {"name": "Truck_Serial_Num"},
                   {"name": "Base_Code", "key": "FK"},
                   {"name": "Type_Code", "key": "FK"}]},
        {"id": "TYPE", "name": "TYPE", "x": 720, "y": 60,
         "attrs": [{"name": "Type_Code", "key": "PK"},
                   {"name": "Type_Description"}]},
    ],
    "relationships": [
        {"from": "BASE", "to": "TRUCK", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "left",
         "label": "has",
         "waypoints": [[152, 300], [330, 300], [330, 300]]},
        {"from": "TYPE", "to": "TRUCK", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "right",
         "label": "classifies",
         "waypoints": [[812, 300], [690, 300]]},
    ],
}

CUSTOMER_ORDER_ERD = {
    "width": 1080,
    "height": 620,
    "entities": [
        {"id": "CUSTOMER", "name": "CUSTOMER", "x": 50, "y": 70,
         "attrs": [{"name": "CustomerID", "key": "PK"},
                   {"name": "Name"}, {"name": "Address"},
                   {"name": "Phone"}]},
        {"id": "ORDER", "name": "ORDER", "x": 390, "y": 70,
         "attrs": [{"name": "OrderID", "key": "PK"},
                   {"name": "OrderDate"},
                   {"name": "CustomerID", "key": "FK"}]},
        {"id": "PRODUCT", "name": "PRODUCT", "x": 730, "y": 70,
         "attrs": [{"name": "ProductID", "key": "PK"},
                   {"name": "Name"}, {"name": "Price"}]},
        {"id": "ORDER_LINE", "name": "ORDER_LINE", "x": 390, "y": 330,
         "attrs": [{"name": "OrderID", "key": "PK/FK"},
                   {"name": "ProductID", "key": "PK/FK"},
                   {"name": "Quantity"}, {"name": "LineTotal"}]},
    ],
    "relationships": [
        {"from": "CUSTOMER", "to": "ORDER", "from_card": "one",
         "to_card": "many", "from_side": "right", "to_side": "left",
         "label": "places"},
        {"from": "ORDER", "to": "ORDER_LINE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "top",
         "label": "contains"},
        {"from": "PRODUCT", "to": "ORDER_LINE", "from_card": "one",
         "to_card": "many", "from_side": "bottom", "to_side": "right",
         "label": "appears in",
         "waypoints": [[832, 270], [832, 380], [620, 380]]},
    ],
}

ANSWERS = {
    "ICT450-2018-JUN-Q1": {
        "confidence": "high",
        "assumptions": ["The TRUCK table has a composite foreign key to BASE "
                        "and TYPE; both are mandatory."],
        "blocks": [
            sub("a", 4, "Two problems associated with a file system.", [
                "Extensive programming and program-data dependence — each "
                "file needs its own management program, and changing a file "
                "structure breaks the programs.",
                "Data redundancy and inconsistency — the same data is stored "
                "in several files and updates are not coordinated.",
                "Complex administration and weak security — file access is "
                "decentralised and difficult to control.",
            ]),
            sub("b", 4, "Basic structure of the ER model and two advantages.",
                [
                    "The ER model represents data as entities, attributes and "
                    "relationships; entities are objects, attributes describe "
                    "them and relationships connect them.",
                    "Advantage: it is a clear communication tool between "
                    "designers, programmers and users.",
                    "Advantage: it is independent of the DBMS and provides a "
                    "conceptual blueprint before implementation.",
                ]),
            sub("c", 12, "TRUCK, BASE and TYPE tables.", [
                "i) TRUCK to BASE is many-to-one: each truck has one "
                "Base_Code, while one base can have many trucks. TRUCK to "
                "TYPE is also many-to-one: each truck has one Type_Code.",
                "Entity integrity: TRUCK YES (Truck_Num is unique and "
                "non-null); BASE YES (Base_Code is unique and non-null); "
                "TYPE YES (Type_Code is unique and non-null).",
                "Referential integrity: every TRUCK.Base_Code exists in BASE "
                "and every TRUCK.Type_Code exists in TYPE.",
                "ii) ERD:",
            ], blocks=[erd("Crow's Foot ERD for TRUCK, BASE and TYPE.",
                           TRUCK_ERD)]),
        ],
        "marking": [
            "a) 2 marks for each of two file-system problems (2 × 2 = 4).",
            "b) 2 marks for the ER structure and 2 marks for each advantage "
            "(2 + 2 = 4).",
            "c)(i) 3 marks for the relationship types and 2 marks for the "
            "entity-integrity explanation (5).",
            "c)(ii) 7 marks for entities, keys, relationships, connectivity "
            "and cardinalities.",
        ],
    },
    "ICT450-2019-DEC-Q1": {
        "confidence": "medium",
        "assumptions": ["Figure 1.0 is answered as a generic parent-child "
                        "ERD because the figure is an image crop; the "
                        "referential-integrity rule is the same for any FK."],
        "blocks": [
            sub("a", 8, "Data anomalies and big data in healthcare.", [
                "i) Insertion anomaly — a new fact cannot be stored without "
                "inventing an unrelated fact; update anomaly — the same fact "
                "must be changed in several places and may become "
                "inconsistent; deletion anomaly — deleting one fact "
                "accidentally removes another.",
                "ii) Predictive healthcare analytics — hospital data is "
                "analysed to predict readmission risk; example: a model flags "
                "diabetic patients for follow-up.",
                "Population health and disease surveillance — large datasets "
                "track outbreaks and health trends; example: regional "
                "dashboards for influenza cases.",
            ]),
            sub("b", 8, "How data redundancy occurs in a file system.", [
                "The same customer or product data is stored in several "
                "independent files, such as an orders file and an invoices "
                "file.",
                "Each department maintains its own copy, so a change in one "
                "file is not reflected in the others.",
                "The result is wasted storage, inconsistent values and update "
                "anomalies.",
            ]),
            sub("c", 4, "How referential integrity is enforced.", [
                "A foreign key in the child table must either match an "
                "existing primary-key value in the parent table or be NULL.",
                "The DBMS rejects inserts, updates or deletes that would leave "
                "an orphan child row.",
            ]),
        ],
        "marking": [
            "a)(i) 2 marks for each of two anomalies (4).",
            "a)(ii) 2 marks for each healthcare application with example (4).",
            "b) 8 marks for a clear description of redundancy and its "
            "consequences.",
            "c) 4 marks for the FK rule and the DBMS enforcement action.",
        ],
    },
    "ICT450-2019-JUN-Q1": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 8, "Traditional file system and database redesign.", [
                "i) Problems: data is duplicated across separate files; "
                "programs depend on file layouts; sharing and security are "
                "weak; the same update must be repeated in several files.",
                "ii) Database approach: integrate the separate files into one "
                "logical database managed by a DBMS, define a shared schema "
                "and keys, and let applications access data through the DBMS "
                "rather than through private files.",
            ]),
            sub("b", 8, "Mobile database characteristics and SRC applications.",
                [
                    "Characteristics: location independence and ubiquitous "
                    "access; synchronization with a central database; limited "
                    "device resources.",
                    "Application 1: a campus event and announcement app for "
                    "students — SRC can push updates and students can read "
                    "them anywhere.",
                    "Application 2: a shuttle or campus facility status app — "
                    "students see live locations and schedules.",
                    "Reason: students carry mobile devices and need timely, "
                    "location-aware information.",
                ]),
            sub("c", 4, "Primary keys in the course schema.", [
                "i) COURSE: CourseCode; SUBJECT: SubjectCode; TEACHER: "
                "TeacherCode; COURSE_SUBJECT: (CourseCode, SubjectCode).",
                "ii) A primary key uniquely identifies each row, prevents "
                "duplicate records and enforces entity integrity.",
            ]),
        ],
        "marking": [
            "a)(i) 4 marks for two file-system problems.",
            "a)(ii) 4 marks for a database redesign with shared schema/DBMS.",
            "b) 2 marks for each characteristic and 2 marks for each "
            "application/reason (8).",
            "c)(i) 2 marks for all primary keys; (ii) 2 marks for the purpose.",
        ],
    },
    "ICT450-2022-FEB-Q1": {
        "confidence": "high",
        "assumptions": ["The STUDENT table has unique STUDENT_IC, STUDENT_ID "
                        "and EMAIL values; the third table is the COURSE "
                        "table shown."],
        "blocks": [
            sub("a", 4, "Four data items in online purchasing.", [
                "Customer identity and contact data.",
                "Product ID, name, price and quantity.",
                "Order ID, order date and payment status.",
                "Delivery address and tracking information.",
            ]),
            sub("b", 4, "Relational model features and importance.", [
                "Data is represented as relations (tables) of rows and "
                "columns, with keys and integrity constraints.",
                "End users see a simple tabular view and can query it with "
                "SQL without knowing physical storage.",
                "Designers gain a logical, DBMS-independent structure that "
                "supports data independence and controlled redundancy.",
            ]),
            sub("c", 12, "Keys and integrity for the academy tables.", [
                "i) Superkeys include {STUDENT_IC}, {STUDENT_ID}, {EMAIL}, "
                "{STUDENT_IC, STUDENT_ID} and {STUDENT_ID, EMAIL}.",
                "Candidate keys: STUDENT_IC, STUDENT_ID and EMAIL, because "
                "each is unique and minimal.",
                "Primary key: STUDENT_ID — it is unique, stable and shorter "
                "than the IC.",
                "ii) STUDENT: entity integrity YES because STUDENT_ID is "
                "unique and non-null; referential integrity YES because every "
                "COURSE_ID exists in COURSE.",
                "COURSE: entity integrity YES because COURSE_ID is the unique "
                "primary key; referential integrity is not applicable because "
                "it has no foreign key.",
            ]),
        ],
        "marking": [
            "a) 1 mark for each of four data items (4).",
            "b) 2 marks for the features and 2 marks for importance (4).",
            "c)(i) 2 marks for superkeys, 2 for candidate keys and 2 for the "
            "primary key/reason (6).",
            "c)(ii) 3 marks for each table's integrity explanation (6).",
        ],
    },
    "ICT450-2023-FEB-Q1": {
        "confidence": "medium",
        "assumptions": ["The printed question total is 14 and sub-part (c) "
                        "is labelled ii) without a printed mark; the answer "
                        "covers the candidate-key task."],
        "blocks": [
            sub("a", 4, "Why file-based systems are still used.", [
                "Low cost and simplicity — a small clinic can keep a local "
                "file without a DBMS licence or server.",
                "Legacy and familiarity — existing staff and procedures already "
                "work with the files, and migration would disrupt service.",
                "Local control and offline operation are also valid reasons.",
            ]),
            sub("b", 4, "Are relationships optional in an ERD?", [
                "The statement is false as a general rule: relationships "
                "represent the business associations between entities and are "
                "essential for a complete model.",
                "Some entities may be standalone (for example a lookup table "
                "with no current relationship), but most entities participate "
                "in at least one relationship.",
                "Illustration: CUSTOMER places ORDER and ORDER contains "
                "PRODUCT; removing those relationships loses the business "
                "meaning.",
            ]),
            sub("c", 6, "Candidate keys and primary key in the customer table.",
                [
                    "Candidate keys: Customer No, Customer IC, e-mail, and "
                    "the combination (First Name, Last Name).",
                    "Primary key: Customer No, because it is short, unique, "
                    "stable and independent of personal details.",
                    "Customer IC and e-mail are also unique but are longer or "
                    "more likely to change; the name combination is weaker "
                    "because names can repeat.",
                ]),
        ],
        "marking": [
            "a) 2 marks for each of two reasons (4).",
            "b) 2 marks for the explanation and 2 marks for the illustration "
            "(4).",
            "c) 1 mark for each candidate key (4) and 2 marks for the "
            "primary-key choice/reason (6).",
        ],
    },
    "ICT450-2024-JAN-Q1": {
        "confidence": "high",
        "assumptions": ["The three tables are Customers, Orders and Products; "
                        "an order can contain many products."],
        "blocks": [
            sub("a", 4, "Meaning of data and database.", [
                "Data are raw facts, such as a customer name or an order "
                "amount, that have not yet been processed into meaning.",
                "A database is an organised collection of logically related "
                "data stored and managed as a single repository.",
            ]),
            sub("b", 4, "Data inconsistency and an example.", [
                "Data inconsistency exists when the same fact has different "
                "values in different places.",
                "Example: a customer's phone number is updated in the "
                "Customers table but the old number remains in an Orders "
                "table.",
            ]),
            sub("c", 6, "Zinnirah's problem and the ERD solution.", [
                "The three tables are not linked by keys, so joins become "
                "complex and the same customer/product data is duplicated.",
                "The solution is an ERD with CUSTOMER, ORDER, PRODUCT and "
                "ORDER_LINE, where ORDER_LINE resolves the many-to-many "
                "order-product relationship.",
            ], blocks=[erd("ERD for the ZY Stationary database.",
                           CUSTOMER_ORDER_ERD)]),
            sub("d", 6, "Three types of SDLC maintenance.", [
                "Corrective maintenance — fixing errors found after delivery.",
                "Adaptive maintenance — changing the system for a new "
                "environment, platform or business rule.",
                "Perfective maintenance — improving performance or adding "
                "enhancements requested by users.",
            ]),
        ],
        "marking": [
            "a) 2 marks each for data and database (4).",
            "b) 2 marks for the definition and 2 for the example (4).",
            "c) 2 marks for the problem and 4 marks for the ERD (6).",
            "d) 2 marks for each maintenance type (6).",
        ],
    },
    "ICT450-2024-JUL-Q1": {
        "confidence": "high",
        "assumptions": ["Table 1's blank Menu Code and missing/invalid Price "
                        "are treated as data-entry and domain problems."],
        "blocks": [
            sub("a", 4, "Two DBMS functions for integrity and consistency.", [
                "Integrity enforcement — the DBMS applies primary-key, "
                "foreign-key, domain and check constraints.",
                "Concurrency control — transactions are isolated so "
                "simultaneous users do not overwrite each other.",
                "Backup and recovery also protect consistency after failure.",
            ]),
            sub("b", 4, "Four database application areas.", [
                "Banking and finance.",
                "Airline and hotel reservations.",
                "University student records.",
                "E-commerce and online retail.",
                "Healthcare and hospital records.",
            ]),
            sub("c", 6, "Three problems in Gerai 17's table.", [
                "Missing Menu Code for Bihun Goreng — the row cannot be "
                "uniquely identified.",
                "Missing Price for Nasi Ayam — the total and average price "
                "cannot be calculated.",
                "Invalid Price “2.S0” for Laksa — the value is not numeric "
                "and violates the price domain.",
                "The table also mixes menu identity and price data without a "
                "clear key.",
            ]),
            sub("d", 6, "Centralized versus decentralized design.", [
                "Control: centralized design keeps data and administration at "
                "one site; decentralized design distributes control.",
                "Location: centralized data is stored centrally; "
                "decentralized data is stored at multiple sites.",
                "Cost/failure: centralization has lower duplication but a "
                "single point of failure; decentralization improves local "
                "availability but increases coordination cost.",
            ]),
        ],
        "marking": [
            "a) 2 marks for each DBMS function (4).",
            "b) 1 mark for each of four applications (4).",
            "c) 2 marks for each of three problems with justification (6).",
            "d) 2 marks for each of three differences (6).",
        ],
    },
    "ICT450-2025-FEB-Q1": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 4, "Four data items for an online store.", [
                "Customer name, address, phone and e-mail.",
                "Product ID, name, description and price.",
                "Order ID, order date, quantity and total.",
                "Payment method and delivery status.",
            ]),
            sub("b", 4, "Two differences between a database and a spreadsheet.",
                [
                    "A database enforces relationships, keys and constraints; "
                    "a spreadsheet stores independent cells and formulas.",
                    "A database supports multi-user concurrency, security and "
                    "recovery; a spreadsheet is mainly single-user and has "
                    "limited integrity controls.",
                ]),
            sub("c", 6, "Insert, update and delete rules of referential "
                "integrity.", [
                "Insert rule: a child row cannot be inserted unless its "
                "foreign-key value matches an existing parent key or is NULL.",
                "Update rule: a parent key cannot be changed if dependent "
                "child rows would be orphaned, unless the change cascades.",
                "Delete rule: a parent row cannot be deleted while dependent "
                "child rows exist, unless the delete cascades or sets NULL.",
                "Example: an order cannot reference a customer that does not "
                "exist.",
            ]),
            sub("d", 6, "Three differences between centralized and "
                "decentralized design.", [
                "Data location: one site versus multiple sites.",
                "Control and administration: central versus local.",
                "Availability and cost: centralized is simpler but has a "
                "single point of failure; decentralized is more resilient but "
                "harder to coordinate.",
            ]),
        ],
        "marking": [
            "a) 1 mark for each of four data items (4).",
            "b) 2 marks for each difference (4).",
            "c) 2 marks for each referential-integrity rule with example (6).",
            "d) 2 marks for each difference (6).",
        ],
    },
    "ICT450-2025-JUL-Q1": {
        "confidence": "medium",
        "assumptions": ["The printed question total is 14 and sub-part (c) "
                        "has no printed mark; the answer covers the key "
                        "definitions and examples."],
        "blocks": [
            sub("a", 4, "Four database applications.", [
                "Banking and financial systems.",
                "Airline reservation systems.",
                "University student information systems.",
                "E-commerce and inventory systems.",
            ]),
            sub("b", 4, "Centralized versus distributed databases.", [
                "A centralized database stores all data at one location; a "
                "distributed database stores fragments at multiple locations.",
                "Centralized control is simpler; distributed processing "
                "improves local access and resilience but adds coordination "
                "and synchronization complexity.",
            ]),
            sub("c", 0, "Candidate, primary and secondary keys with examples.",
                [
                    "Candidate key: any minimal attribute set that uniquely "
                    "identifies a row; examples: AgentID or Passport Number.",
                    "Primary key: the candidate key chosen for the table; "
                    "example: AgentID.",
                    "Secondary key: a non-primary attribute used for lookup; "
                    "example: Agent LastName or AreaCode.",
                ]),
            sub("d", 6, "Three factors in DBMS software selection.", [
                "Cost — licence, training, hardware and maintenance costs.",
                "Features and tools — data model support, SQL, security, "
                "backup, reporting and development tools.",
                "Portability and hardware requirements — platform support and "
                "the ability to move the system later.",
                "Vendor support and performance are also valid factors.",
            ]),
        ],
        "marking": [
            "a) 1 mark for each of four applications (4).",
            "b) 2 marks for each difference (4).",
            "c) 2 marks for each key definition with an example (6; no mark "
            "was printed for this sub-part in the extraction).",
            "d) 2 marks for each of three factors (6).",
        ],
    },
}
