"""Model answers for the concepts questions used in seeds 1–3."""
from __future__ import annotations

from ._blocks import bullets, p, sub

ANSWERS = {
    "ICT450-2018-DEC-Q1": {
        "confidence": "high",
        "assumptions": [
            "The question asks for four components; five are listed so the "
            "answer remains complete if the marker expects a different set.",
        ],
        "blocks": [
            p("A database system environment is made up of the people, "
              "procedures, data, hardware and software that work together to "
              "manage and use a database."),
            sub("a", 8, "Four components of a database system environment.", [
                "Hardware — the physical devices on which the database runs, "
                "including servers, storage, network equipment and user "
                "terminals.",
                "Software — the DBMS, application programs, utilities and "
                "development tools that let users define, access and manage "
                "the data.",
                "People — the database administrator, designers, analysts, "
                "programmers and end users who use or manage the database.",
                "Data — the raw facts stored in the database, together with "
                "the metadata that describes their structure and meaning.",
                "Procedures — the written instructions and policies for using, "
                "backing up, securing and recovering the database.",
            ]),
            sub("b", 8, "Four characteristics of successful Internet-age "
                "databases.", [
                "Ubiquitous connectivity — users can reach the database from "
                "web browsers, mobile apps and data services at any time and "
                "from any location.",
                "Scalability and performance — the system can handle growing "
                "volumes of users, transactions and data without unacceptable "
                "response times.",
                "High availability and reliability — the database remains "
                "accessible through failures, with replication, backup and "
                "recovery facilities.",
                "Security and privacy — authentication, authorisation, "
                "encryption and auditing protect data that is exposed over "
                "public networks.",
                "Manageability — the database can be monitored, tuned and "
                "administered centrally with minimal disruption.",
            ]),
            sub("c", 4, "Two advantages and two disadvantages of an ERD.", [
                "Advantage: an ERD gives designers, programmers and users a "
                "clear visual model of the entities, attributes and "
                "relationships before implementation.",
                "Advantage: it is independent of any DBMS, so the same "
                "conceptual design can be reviewed and implemented on "
                "different platforms.",
                "Disadvantage: a large ERD can become crowded and difficult "
                "to read, especially when many relationships and weak "
                "entities are involved.",
                "Disadvantage: an ERD does not show every business rule, "
                "process or physical implementation detail, so it must be "
                "supported by other documentation.",
            ]),
        ],
        "marking": [
            "a) 2 marks for each of four components named and explained "
            "(4 × 2 = 8).",
            "b) 2 marks for each of four characteristics named and explained "
            "(4 × 2 = 8).",
            "c) 1 mark for each advantage and each disadvantage, correctly "
            "explained (4 × 1 = 4).",
        ],
    },
    "ICT450-2023-JUL-Q1": {
        "confidence": "high",
        "assumptions": [
            "Table 1 is treated as a single relation with the columns shown: "
            "StudID, Name, Name and Skill.",
            "A StudID is assumed to be a numeric identifier; the value "
            "2023455abc is therefore an inconsistent data-type entry.",
        ],
        "blocks": [
            sub("a", 4, "Two limitations of the file-based approach.", [
                "Extensive programming and program-data dependence — every "
                "file needs its own management program, and changing a file "
                "structure requires the programs to be rewritten.",
                "Complex and difficult system administration — each file has "
                "its own format, access rules and storage, so administration "
                "does not scale well.",
                "Inadequate security and redundant data — access controls are "
                "weak, and independent files tend to store the same data more "
                "than once, causing inconsistency.",
                "Difficult structural change and limited sharing — separate "
                "files create islands of information that are hard to change "
                "or share safely.",
            ]),
            sub("b", 4, "Two basic building blocks of a data model.", [
                "Entity — a distinguishable object, person, place or event "
                "about which data is kept, such as STUDENT or COURSE.",
                "Relationship — an association between entities, such as a "
                "STUDENT enrolling in a COURSE.",
                "Attribute — a property that describes an entity, such as "
                "StudID or StudentName.",
            ]),
            sub("c", 12, "The art and culture club table.", [
                "i) Three characteristics of a relational table violated by "
                "Table 1:",
                "The table has two columns with the same name, “Name”; every "
                "column in a relation must have a unique name.",
                "The Skill column stores several values in one cell, such as "
                "“Modern Dance, Singing”; each cell must contain a single "
                "atomic value.",
                "The StudID column mixes numeric values with the text value "
                "2023455abc; all entries in a column must use the same data "
                "type.",
                "There is no clearly declared primary key and the duplicate "
                "Name headings make the structure ambiguous.",
                "ii) Possible courses of action:",
                "Rename the two Name columns to FirstName and LastName.",
                "Move Skill into a separate SKILL table keyed by StudID and "
                "Skill, creating a one-to-many relationship with STUDENT.",
                "Standardise StudID as one data type, validate input and "
                "reject values such as 2023455abc.",
                "Declare StudID as the primary key and enforce entity "
                "integrity.",
            ]),
        ],
        "marking": [
            "a) 2 marks for each of two limitations named and explained "
            "(2 × 2 = 4).",
            "b) 2 marks for each of two building blocks named and explained "
            "(2 × 2 = 4).",
            "c)(i) 2 marks for each of three violations identified and "
            "explained (3 × 2 = 6).",
            "c)(ii) 2 marks for each of three suitable actions linked to the "
            "violations (3 × 2 = 6).",
        ],
    },
    "ICT450-2026-FEB-Q1": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 4, "Four examples of data in a student registration "
                "database system.", [
                "Student identification data — student number, name, date of "
                "birth, gender and contact details.",
                "Programme data — programme code, programme name, faculty and "
                "study level.",
                "Course registration data — course code, course name, "
                "semester, section and registration date.",
                "Academic record data — coursework marks, final examination "
                "marks and grades.",
                "Other valid examples: address, telephone number, "
                "scholarship status or adviser details.",
            ]),
            sub("b", 4, "Four limitations of the traditional computerized "
                "file system.", [
                "It requires extensive programming, and file layouts are "
                "embedded in programs, creating program-data dependence.",
                "System administration is complex and difficult because each "
                "file has its own format, access rules and storage.",
                "Changing existing file structures is difficult and can "
                "require rewriting the application programs.",
                "Security features are likely inadequate, with little central "
                "control over who can read or change each file.",
                "Independent files tend to contain redundant data, causing "
                "inconsistency and structural dependency.",
            ]),
            sub("c", 6, "Three important features of a data dictionary.", [
                "It gives a detailed description of all tables in the "
                "database, including every attribute name, characteristic, "
                "data type, size and constraint.",
                "It stores metadata — data about data — and is sometimes "
                "called the database designer's database because it records "
                "the design decisions about tables and their structures.",
                "It provides a central, consistent reference for designers, "
                "programmers and users, so definitions do not diverge and "
                "changes can be controlled.",
            ]),
            sub("d", 6, "Six phases of the Database Life Cycle (DBLC).", [
                "Database initial study.",
                "Database design.",
                "Implementation and loading.",
                "Testing and evaluation.",
                "Operation.",
                "Maintenance and evolution.",
            ]),
        ],
        "marking": [
            "a) 1 mark for each of four valid examples (4 × 1 = 4).",
            "b) 1 mark for each of four limitations stated correctly "
            "(4 × 1 = 4).",
            "c) 2 marks for each of three data-dictionary features explained "
            "(3 × 2 = 6).",
            "d) 1 mark for each of the six DBLC phases in the correct order "
            "(6 × 1 = 6).",
        ],
    },
}
