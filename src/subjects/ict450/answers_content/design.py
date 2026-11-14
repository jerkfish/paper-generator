"""Model answers for the design-theory questions used in seeds 1–3."""
from __future__ import annotations

from ._blocks import p, sub

ANSWERS = {
    "ICT450-2018-JUN-Q2": {
        "confidence": "high",
        "assumptions": [
            "The three backup levels are interpreted as full, differential "
            "and transaction-log backup, the standard DBLC recovery model.",
        ],
        "blocks": [
            sub("a", 8, "Database life cycle phases.", [
                "i) Implementation and loading: the physical database is "
                "created from the design — tables, keys, constraints, views, "
                "indexes and security are defined; existing data is converted "
                "and loaded; backup and recovery arrangements are put in place "
                "and the database is tested before release.",
                "ii) Three backup levels:",
                "Full backup — a complete copy of the whole database; it is "
                "the baseline for recovery but takes the most time and space.",
                "Differential backup — copies only data changed since the last "
                "full backup; recovery needs the last full backup plus the "
                "latest differential backup.",
                "Transaction-log backup — copies the transaction log, allowing "
                "point-in-time recovery and recovery of changes made after the "
                "last full or differential backup.",
                "Incremental backup may be accepted in place of differential "
                "backup: it copies changes since the last backup of any type.",
            ]),
            sub("b", 8, "Big data and three technologies for managing it.", [
                "Big data is data that is too large, fast-changing or varied "
                "for traditional relational systems to capture and process "
                "within an acceptable time. Its core characteristics are "
                "volume, velocity and variety; veracity and value are often "
                "added as extended characteristics.",
                "Hadoop and HDFS — Hadoop is a Java-based, open-source, "
                "fault-tolerant distributed framework; HDFS is its distributed "
                "file system for storing very large files across a cluster.",
                "MapReduce — an open-source programming API that processes "
                "large datasets in parallel and provides fast data-analytic "
                "services.",
                "NoSQL — a large-scale distributed database system that stores "
                "structured and unstructured data efficiently, with high "
                "scalability, availability and fault tolerance.",
            ]),
            sub("c", 4, "Structured versus unstructured data.", [
                "Structured data has a predefined schema and is stored in "
                "rows and columns with consistent data types; it is easy to "
                "query with SQL. Example: a student table containing StudID, "
                "Name and CGPA.",
                "Unstructured data has no predefined relational schema and "
                "cannot be stored naturally in rows and columns. Example: "
                "images, video, audio, free-text documents or social-media "
                "posts.",
            ]),
        ],
        "marking": [
            "a)(i) 2 marks for a correct description of implementation and "
            "loading.",
            "a)(ii) 2 marks for each of three backup levels correctly "
            "described (3 × 2 = 6).",
            "b) 2 marks for the definition of big data; 2 marks for each of "
            "three technologies (2 + 3 × 2 = 8).",
            "c) 2 marks for structured data with an example and 2 marks for "
            "unstructured data with an example (2 + 2 = 4).",
        ],
    },
    "ICT450-2023-FEB-Q2": {
        "confidence": "high",
        "assumptions": [
            "The staff table has StaffID as its primary key; Salary must be "
            "numeric and lie in the stated range 3000–10000; DepartmentID is "
            "numeric.",
        ],
        "blocks": [
            sub("a", 8, "Four activities in the database initial study.", [
                "Analyse the company situation — study the organisation's "
                "structure, mission, operations, data handling and business "
                "environment.",
                "Define the problems and constraints — identify weaknesses, "
                "missing or redundant data, security issues and limits such "
                "as budget, time or existing systems.",
                "Define the objectives — state what the database must achieve "
                "and check that the objectives match the end users' needs.",
                "Define the scope and boundaries — decide which business "
                "areas, entities, data types and users are inside the "
                "database, and what external systems or limits bound it.",
            ]),
            sub("b", 8, "Four limitations of mobile databases, with examples.",
                [
                    "Limited bandwidth and intermittent connectivity — a field "
                    "worker may lose the network while updating a delivery "
                    "record.",
                    "Limited storage, memory and battery — a smartphone may "
                    "not hold a full local copy of a large central database.",
                    "Security and privacy risks — a lost or stolen mobile "
                    "device may expose cached customer data unless it is "
                    "encrypted.",
                    "Synchronisation and consistency — offline edits from "
                    "several devices must be merged without overwriting newer "
                    "data.",
                    "Heterogeneous devices and operating systems increase "
                    "development and testing effort.",
                ]),
            sub("c", 4, "Rows that will fail insertion into the STAFF table.",
                [
                    "Row 3033 (Siti Ziana) will fail because Salary = 11000 "
                    "is outside the allowed range 3000–10000; this violates "
                    "the domain or check constraint on Salary.",
                    "Row 3034 (Ahmad Daniel) will fail because Salary = "
                    "“150a” is not numeric; this violates the data type of "
                    "the Salary column.",
                    "Rows 3035 and 3036 satisfy the stated data types and "
                    "range, and all StaffID values are unique.",
                ]),
        ],
        "marking": [
            "a) 2 marks for each of four initial-study activities explained "
            "(4 × 2 = 8).",
            "b) 2 marks for each of four mobile-database limitations with a "
            "relevant example (4 × 2 = 8).",
            "c) 2 marks for row 3033 with the range/domain reason; 2 marks "
            "for row 3034 with the data-type reason (2 + 2 = 4).",
        ],
    },
    "ICT450-2025-JUL-Q2": {
        "confidence": "high",
        "assumptions": [
            "The publishing table is read as ISBN, BookTitle, Authors, "
            "Publisher ID and Publisher Name.",
        ],
        "blocks": [
            sub("a", 4, "Two disadvantages of the network model.", [
                "It is cumbersome — the set and pointer structures make the "
                "database difficult to design, understand and use.",
                "It lacks ad hoc query capability, so programmers must write "
                "code for every report instead of issuing a query.",
                "A structural change in the database can produce havoc in all "
                "application programs, showing poor data independence.",
            ]),
            sub("b", 4, "Two reasons the books table violates relational-table "
                "characteristics.", [
                "The ISBN 978-981-4824-24-7 appears in two rows, so the "
                "declared primary key is not unique and entity integrity is "
                "violated.",
                "The Authors column stores several authors in one cell, such "
                "as “Ahmad Rostam, Rozaniza, Alizi Alias”; a relational table "
                "requires each cell to be atomic.",
                "Publisher Name is repeated for the same Publisher ID, which "
                "also creates redundancy, although that is a normalization "
                "issue rather than a table-characteristic violation.",
            ]),
            sub("c", 6, "Three views of data for the designer.", [
                "Data structure view — how the data is organised: entities, "
                "attributes, relationships and the resulting tables.",
                "Data access view — how users and programs retrieve and update "
                "the data: queries, access paths, indexes and security.",
                "Activities view — the business processes, transactions and "
                "reports that transform the stored data into information.",
                "The business view, by contrast, sees data as an information "
                "source rather than as structures and processes.",
            ]),
            sub("d", 6, "Three benefits of big data to companies.", [
                "Better decision-making — large and varied datasets reveal "
                "patterns, trends and customer behaviour that small samples "
                "cannot show.",
                "More personalised products and marketing — companies can "
                "tailor offers, recommendations and service levels to "
                "individual customers.",
                "Operational efficiency and cost reduction — analysing "
                "transactions, logs and supply-chain data can expose waste, "
                "bottlenecks and fraud.",
                "New revenue and innovation — data can support new services, "
                "predictive maintenance and data-driven business models.",
            ]),
        ],
        "marking": [
            "a) 2 marks for each of two disadvantages explained (2 × 2 = 4).",
            "b) 2 marks for each of two violations correctly linked to the "
            "table data (2 × 2 = 4).",
            "c) 2 marks for each of three designer views explained "
            "(3 × 2 = 6).",
            "d) 2 marks for each of three benefits explained (3 × 2 = 6).",
        ],
    },
}
