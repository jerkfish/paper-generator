"""Model answers for the remaining design-theory questions (V4 completion)."""
from __future__ import annotations

from ._blocks import p, sub

ANSWERS = {
    "ICT450-2018-DEC-Q2": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 8, "Business rules and three essentials.", [
                "A business rule is a precise statement that describes a "
                "policy, constraint or relationship in the organisation's "
                "operations and must be reflected in the database.",
                "Essential 1: the rule must be precise and unambiguous, so "
                "every reader derives the same entities, attributes and "
                "constraints.",
                "Essential 2: it must be documented and traceable to its "
                "source (policy, procedure, form or interview).",
                "Essential 3: it must be enforceable in the design through "
                "keys, cardinalities, domains or check constraints.",
            ]),
            sub("b", 2, "Importance of an index.", [
                "An index provides a fast access path to rows, speeding up "
                "searches, joins and sorting; a unique index also enforces "
                "uniqueness.",
            ]),
            sub("c", 4, "Four common sources of database failure.", [
                "Hardware failure (disk, memory, power).",
                "Software failure (DBMS or application bug).",
                "Human error (accidental deletion or bad update).",
                "Natural disaster, network failure or malicious attack.",
            ]),
            sub("d", 6, "Three backup levels.", [
                "Full backup — a complete copy of the database.",
                "Differential backup — changes since the last full backup.",
                "Transaction-log backup — the log of individual transactions, "
                "allowing point-in-time recovery.",
            ]),
        ],
        "marking": [
            "a) 2 marks for the definition and 2 marks for each of three "
            "essentials (2 + 6 = 8).",
            "b) 2 marks for the indexing benefit.",
            "c) 1 mark for each of four sources (4).",
            "d) 2 marks for each of three backup levels (6).",
        ],
    },
    "ICT450-2019-DEC-Q2": {
        "confidence": "high",
        "assumptions": ["Figure 2.0 is answered generically because the "
                        "asset is a figure crop; the examples use standard "
                        "entities."],
        "blocks": [
            sub("a", 8, "Entity and attribute concepts with examples.", [
                "An entity is a distinguishable object, person, place or "
                "event about which the database stores data.",
                "An attribute is a property that describes an entity; it has "
                "a domain and may be a key.",
                "Example 1: entity STUDENT with attributes StudentID, "
                "StudentName, Programme and GPA.",
                "Example 2: entity COURSE with attributes CourseCode, "
                "CourseName, CreditHour and Department.",
                "The business rules determine which entities and attributes "
                "are needed and how they are related.",
            ]),
            sub("b", 2, "Purpose of entity integrity.", [
                "Entity integrity requires every primary key to be unique and "
                "non-null, so each row can be identified without ambiguity.",
            ]),
            sub("c", 4, "Top-down versus bottom-up design.", [
                "Top-down starts with the overall business model and "
                "decomposes it into entities and attributes.",
                "Bottom-up starts with individual attributes and data "
                "elements and combines them into entities and relationships.",
                "Top-down suits a new, well-understood enterprise model; "
                "bottom-up suits existing files being integrated.",
            ]),
            sub("d", 6, "Three types of periodic maintenance.", [
                "Corrective maintenance — fixing errors discovered in "
                "operation.",
                "Adaptive maintenance — adapting to new hardware, software or "
                "business requirements.",
                "Perfective maintenance — improving performance, usability or "
                "adding enhancements.",
            ]),
        ],
        "marking": [
            "a) 4 marks for entity/attribute definitions and 4 marks for two "
            "examples (8).",
            "b) 2 marks for the entity-integrity purpose.",
            "c) 2 marks for each approach and 2 marks for the comparison (4).",
            "d) 2 marks for each maintenance type (6).",
        ],
    },
    "ICT450-2019-JUN-Q2": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 10, "Data model importance and ANSI/SPARC levels.", [
                "i) A data model is a communication tool and blueprint that "
                "organises data for users, designers and programmers.",
                "ii) External level — the user or application view; each user "
                "sees only the data and operations needed for their task.",
                "Conceptual level — a community view of the whole database: "
                "entities, attributes, relationships and constraints, "
                "independent of physical storage.",
                "Internal level — the physical view: file organisation, "
                "indexes, storage allocation and access paths.",
            ]),
            sub("b", 4, "Appropriate situations for centralized and "
                "decentralized design.", [
                "Centralized design suits a single-site organisation with "
                "tight control, uniform security and moderate data volume.",
                "Decentralized design suits multiple branches or regions "
                "where local access, autonomy and resilience matter more than "
                "central control.",
            ]),
            sub("c", 6, "DBLC stages in sequence.", [
                "Database initial study.",
                "Database design.",
                "Implementation and loading.",
                "Testing and evaluation.",
                "Operation.",
                "Maintenance and evolution.",
            ]),
        ],
        "marking": [
            "a)(i) 2 marks for importance; (ii) 8 marks for the three levels "
            "with illustration (2 + 8 = 10).",
            "b) 2 marks for each appropriate situation (4).",
            "c) 1 mark for each of six stages in order (6).",
        ],
    },
    "ICT450-2022-FEB-Q2": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 8, "Conceptual, logical and physical design.", [
                "Conceptual design — an abstract, software-independent model "
                "of entities, attributes and relationships derived from "
                "business rules.",
                "Logical design — maps the conceptual model to the chosen "
                "data model (usually relational tables, keys and "
                "constraints); it is software-dependent.",
                "Physical design — selects storage structures, indexes, file "
                "organisation and access paths; it is hardware- and "
                "software-dependent.",
            ]),
            sub("b", 8, "Four big-data characteristics with examples.", [
                "Volume — very large amounts of data; example: billions of "
                "daily e-commerce clicks.",
                "Velocity — data arrives and must be processed quickly; "
                "example: real-time payment fraud alerts.",
                "Variety — many formats; example: text, images, video and "
                "sensor data in one platform.",
                "Veracity — uncertainty in data quality; example: noisy "
                "social-media posts that need cleaning.",
                "Value is also accepted as an extended characteristic.",
            ]),
            sub("c", 4, "Two spreadsheet features different from a database.",
                [
                    "A spreadsheet has no enforced relationships, primary keys "
                    "or referential integrity; a database enforces them.",
                    "A spreadsheet has limited multi-user concurrency, "
                    "security and recovery; a database provides transaction "
                    "control and central access rights.",
                ]),
        ],
        "marking": [
            "a) 2 marks for each design stage and 2 marks for the "
            "software-dependence point (8).",
            "b) 2 marks for each of four characteristics with example (8).",
            "c) 2 marks for each difference (4).",
        ],
    },
    "ICT450-2023-JUL-Q2": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 8, "Four activities in the database design phase.", [
                "Create the conceptual design — identify entities, "
                "attributes, relationships and business rules.",
                "Select the DBMS software — choose a platform that fits the "
                "data model, cost and hardware.",
                "Create the logical design — map the conceptual model to "
                "tables, keys, domains and constraints.",
                "Create the physical design — choose storage, indexes, file "
                "organisation and access paths.",
            ]),
            sub("b", 8, "Mobile database suitability and three usage factors.",
                [
                    "Yes, a mobile database is suitable for a company with "
                    "branches in Malaysia and Indonesia because staff need "
                    "access away from the office.",
                    "Factor 1: ubiquitous connectivity — field staff can reach "
                    "the database from any branch or location.",
                    "Factor 2: synchronization — local device data can be "
                    "reconciled with the central database when connectivity "
                    "returns.",
                    "Factor 3: portability and location-aware services — "
                    "mobile devices support on-site inventory and customer "
                    "service.",
                ]),
            sub("c", 4, "Structured versus unstructured data.", [
                "Structured data has a predefined schema and is stored in "
                "rows and columns; example: a sales table.",
                "Unstructured data has no predefined relational schema; "
                "example: images, video, audio or free-text documents.",
            ]),
        ],
        "marking": [
            "a) 2 marks for each of four design activities (8).",
            "b) 2 marks for suitability and 2 marks for each of three factors "
            "(2 + 6 = 8).",
            "c) 2 marks for each data type with example (4).",
        ],
    },
    "ICT450-2024-JAN-Q2": {
        "confidence": "medium",
        "assumptions": ["The printed question total is 16 and sub-part (b) "
                        "has no printed mark; the answer covers the "
                        "integrity comparison."],
        "blocks": [
            sub("a", 4, "Two advantages of a conceptual model.", [
                "It gives business users and designers a common, "
                "DBMS-independent view of the data.",
                "It captures business rules and entities before physical "
                "implementation, reducing expensive design changes later.",
            ]),
            sub("b", 0, "Do Tables 1 and 2 violate entity and referential "
                "integrity?", [
                "Table 1: entity integrity is violated because ISBN "
                "978-981-4824-24-7 appears twice; the ISBN cannot uniquely "
                "identify a row. Referential integrity is violated because "
                "one row has no PublisherID.",
                "Table 2: entity integrity holds because PublisherID is "
                "unique and non-null; referential integrity holds because it "
                "has no foreign key.",
            ]),
            sub("c", 6, "Stages in the database design procedure flow.", [
                "Conceptual design — hardware/software independent.",
                "Logical design — software-dependent but hardware-independent.",
                "Physical design — hardware- and software-dependent.",
                "The flow moves from business requirements to a physical "
                "implementation.",
            ]),
            sub("d", 6, "Three factors increasing reliance on big data.", [
                "The volume of web, mobile and sensor data has grown beyond "
                "traditional systems.",
                "Storage and distributed processing are now cheaper and more "
                "scalable.",
                "Organisations need faster insight for personalisation, risk "
                "detection and decision-making.",
            ]),
        ],
        "marking": [
            "a) 2 marks for each advantage (4).",
            "b) 3 marks for each table's integrity explanation (6; no mark "
            "was printed for this sub-part in the extraction).",
            "c) 2 marks for each design stage (6).",
            "d) 2 marks for each factor (6).",
        ],
    },
    "ICT450-2024-JUL-Q2": {
        "confidence": "medium",
        "assumptions": ["The matching statements for the data-model table "
                        "were not present in the extracted asset; the answer "
                        "describes each model's matching statement."],
        "blocks": [
            sub("a", 4, "Match the data models with their statements.", [
                "Hierarchical — records are organised in a strict parent-child "
                "tree; each child has one parent.",
                "Network — records are linked through sets and pointers, "
                "allowing many-to-many relationships.",
                "Relational — data is represented as tables with rows, "
                "columns and keys, queried with SQL.",
                "Entity Relationship — a conceptual model of entities, "
                "attributes and relationships, usually drawn as an ERD.",
            ]),
            sub("b", 4, "Two business rules from the pet-shop schema.", [
                "A customer can make many purchases, but each purchase is made "
                "by exactly one customer.",
                "A purchase can contain many pets, and each pet belongs to one "
                "purchase through PurchaseID.",
                "A pet has one species, age and price recorded.",
            ]),
            sub("c", 6, "Three reasons for protecting data.", [
                "Privacy and legal compliance — personal and financial data "
                "must not be exposed.",
                "Data integrity and trust — unauthorised changes can corrupt "
                "records and decisions.",
                "Business continuity and competitive advantage — theft or "
                "tampering can cause financial and reputational loss.",
            ]),
            sub("d", 6, "Three multimedia data challenges.", [
                "Large storage size — images, audio and video consume much "
                "more space than structured records.",
                "Complex indexing and retrieval — content-based search needs "
                "metadata and specialised indexes.",
                "Format and metadata diversity — many codecs, dimensions and "
                "formats must be normalised and described.",
            ]),
        ],
        "marking": [
            "a) 1 mark for each correct data-model description (4).",
            "b) 2 marks for each business rule (4).",
            "c) 2 marks for each reason (6).",
            "d) 2 marks for each challenge (6).",
        ],
    },
    "ICT450-2025-FEB-Q2": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 4, "Two disadvantages of the hierarchical model.", [
                "It is rigid: each child has only one parent, so many-to-many "
                "relationships cannot be represented directly.",
                "Navigation is pointer-based and programs depend on the "
                "physical tree structure, making change difficult.",
            ]),
            sub("b", 4, "Four sources of business rules.", [
                "Company policies and procedures.",
                "Interviews with managers and end users.",
                "Existing forms, reports and documents.",
                "Government regulations and industry standards.",
            ]),
            sub("c", 6, "Three types of backup.", [
                "Full backup — complete copy of the database.",
                "Differential backup — changes since the last full backup.",
                "Transaction-log backup — the transaction log for point-in-time "
                "recovery.",
            ]),
            sub("d", 6, "Three mobile-database advantages in marketing.", [
                "Location-based promotions can be delivered to customers near "
                "a store.",
                "Sales staff can access customer and product data in real "
                "time during visits.",
                "Campaign performance and customer responses can be captured "
                "immediately for analysis.",
            ]),
        ],
        "marking": [
            "a) 2 marks for each disadvantage (4).",
            "b) 1 mark for each of four sources (4).",
            "c) 2 marks for each backup type (6).",
            "d) 2 marks for each advantage (6).",
        ],
    },
    "ICT450-2026-FEB-Q2": {
        "confidence": "high",
        "assumptions": [],
        "blocks": [
            sub("a", 4, "Two basic features of the relational model.", [
                "Data is organised as relations (tables) of rows and columns, "
                "with each column drawn from a domain.",
                "Keys and integrity constraints link tables and enforce "
                "uniqueness, entity integrity and referential integrity.",
            ]),
            sub("b", 4, "Two domain constraints.", [
                "Data-type and format constraint — a salary column must be "
                "numeric, and a phone number must follow a pattern.",
                "Range or check constraint — a salary must lie between 3000 "
                "and 10000; a grade must be one of A, B, C, D, E or F.",
            ]),
            sub("c", 6, "Three anomalies in a denormalized table.", [
                "Insertion anomaly — a new product cannot be added without "
                "inventing a customer order.",
                "Update anomaly — a customer address must be changed in every "
                "row where it appears.",
                "Deletion anomaly — deleting an order may also delete the only "
                "record of a product or customer.",
            ]),
            sub("d", 6, "Three mobile-database challenges with examples.", [
                "Intermittent connectivity — a field officer loses the network "
                "while updating a record.",
                "Limited device storage and battery — a phone cannot hold the "
                "whole central database.",
                "Security and synchronization — a lost device may expose data, "
                "and offline edits must be merged safely.",
            ]),
        ],
        "marking": [
            "a) 2 marks for each feature (4).",
            "b) 2 marks for each domain constraint with example (4).",
            "c) 2 marks for each anomaly with example (6).",
            "d) 2 marks for each challenge with example (6).",
        ],
    },
}
