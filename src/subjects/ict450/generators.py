"""Deterministic Stage-6 generators for ICT450.

Consumes the Stage-5 planner and produces five 20-mark structured questions
with model answers and marking points. The question patterns are derived from
the ICT200/ICT450 topic map; they are original text, not copied past papers.
No LLM is used.

    uv run python -m src.subjects.ict450.generators --seed 1
    uv run python -m src.subjects.ict450.generators --validate
"""
from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path

from src import config
from src.subjects.ict450.planner import build_plan

SUBJECT = "ICT450"
TRACKING = config.TRACKING_DIR / "ict450"
SAMPLE_PATH = TRACKING / "generator_sample_seed_01.json"
VALIDATION_PATH = TRACKING / "generator_validation.json"

ORGANISATIONS = {
    "database_concept": ["Harmony Tuition Centre", "Cedar Community College",
                         "Nusantara Learning Hub"],
    "data_model": ["Nusantara Medical Clinic", "Harmony Specialist Hospital",
                   "Aurora Health Centre"],
    "database_design": ["Delta Clinic", "Greenfield Medical Centre",
                        "Sri Murni Health Clinic"],
    "erd": ["Sri Murni Library", "Cedar Community Library",
            "Harmony Resource Centre"],
    "normalization": ["Aurora Retail", "Greenfield Logistics", "Delta Hotel"],
    "relational": ["Cedar Community College", "Nusantara University",
                   "Harmony Institute"],
    "sql": ["Cedar Community College", "Nusantara University",
            "Harmony Institute"],
}


def _subpart(part, marks, text, answer, points):
    return {
        "part": part,
        "marks": marks,
        "text": text,
        "answer": answer,
        "marking_points": points,
    }


QUESTION_BANK = {
    "database_concept": {
        "generator_id": "ict450.database_concept",
        "source": "ICT200/ICT450 KB Topic 1 Database Concept",
        "stem": (
            "{org} currently keeps student records in separate spreadsheet "
            "files. The manager is considering a database management system "
            "(DBMS)."),
        "subparts": [
            _subpart("a", 6,
                     "Define database, DBMS and database system.",
                     "A database is an organised collection of related data. A DBMS is software that creates, stores, manages and controls access to a database. A database system is the database, DBMS, application programs, people, procedures and hardware working together.",
                     ["database definition (2)", "DBMS definition (2)",
                      "database system definition (2)"]),
            _subpart("b", 8,
                     "State FOUR limitations of the file-based approach that a DBMS addresses.",
                     "The limitations include data redundancy, data inconsistency, difficult data sharing, weak concurrency control, limited security, program-data dependence, and difficult backup/recovery.",
                     ["four limitations x 2 marks each"]),
            _subpart("c", 6,
                     "Explain THREE functions of a DBMS that address those limitations.",
                     "A DBMS provides controlled data sharing, integrity enforcement, security and authorisation, concurrency control, backup and recovery, and a data dictionary.",
                     ["three functions x 2 marks each"]),
        ],
    },
    "data_model": {
        "generator_id": "ict450.data_model",
        "source": "ICT200/ICT450 KB Topic 2 Data Model",
        "stem": (
            "{org} is selecting a data model for a new patient-record "
            "system. The system must support many related tables and ad-hoc "
            "queries."),
        "subparts": [
            _subpart("a", 4,
                     "Define data model and schema.",
                     "A data model is a collection of concepts used to describe the structure of a database. A schema is the description of the database structure, including tables, attributes and relationships.",
                     ["data model definition (2)", "schema definition (2)"]),
            _subpart("b", 9,
                     "Compare the hierarchical, network and relational data models.",
                     "Hierarchical: tree structure, one parent per child. Network: graph structure, many-to-many links through sets. Relational: tables, rows and columns with keys; supports flexible querying and many-to-many relationships through junction tables.",
                     ["hierarchical structure/limitation (3)",
                      "network structure/limitation (3)",
                      "relational structure/advantage (3)"]),
            _subpart("c", 4,
                     "Explain TWO advantages of the relational model for this hospital scenario.",
                     "The relational model provides flexible ad-hoc querying, simple tabular representation, data independence, and many-to-many relationships through foreign keys.",
                     ["two advantages x 2 marks"]),
            _subpart("d", 3,
                     "State the THREE levels of data abstraction.",
                     "External (view) level, conceptual level and internal (physical) level.",
                     ["one mark per level"]),
        ],
    },
    "relational": {
        "generator_id": "ict450.relational_model",
        "source": "ICT200/ICT450 KB Topic 3 Relational Data Model",
        "stem": (
            "The relation schema ENROL(StudentID, CourseID, StudentName, "
            "CourseName, Lecturer, Grade) records student enrolment. Assume "
            "StudentID and CourseID together uniquely identify a row."),
        "subparts": [
            _subpart("a", 4,
                     "Identify the primary key and TWO candidate keys.",
                     "Primary key: (StudentID, CourseID). Candidate keys: (StudentID, CourseID); StudentID alone is not a candidate key because a student enrols in many courses, and CourseID alone is not a candidate key because a course has many students.",
                     ["primary key (2)", "candidate-key explanation (2)"]),
            _subpart("b", 6,
                     "Explain entity integrity and referential integrity with one example each.",
                     "Entity integrity: a primary-key attribute cannot be null. Referential integrity: a foreign-key value must match an existing primary-key value or be null. Example: ENROL.StudentID must exist in STUDENT.StudentID.",
                     ["entity integrity definition/example (3)",
                      "referential integrity definition/example (3)"]),
            _subpart("c", 4,
                     "Define tuple, attribute, degree and cardinality.",
                     "Tuple = a row; attribute = a column; degree = number of attributes; cardinality = number of tuples.",
                     ["one mark each"]),
            _subpart("d", 6,
                     "Explain TWO update anomalies that can occur in this schema.",
                     "StudentName repeats for every enrolment, so a name change may be missed in some rows (update anomaly). Deleting the last enrolment for a course may lose course data (delete anomaly). Inserting a new course before any student enrols is difficult (insert anomaly).",
                     ["two anomalies explained x 3 marks"]),
        ],
    },
    "erd": {
        "generator_id": "ict450.erd",
        "source": "ICT200/ICT450 KB Topic 4 ERD",
        "stem": (
            "{org} lends books to members. Each book has one publisher; a "
            "publisher can publish many books. A member can borrow many books "
            "over time, and each loan records the loan date and due date."),
        "subparts": [
            _subpart("a", 8,
                     "Identify the entities, relationships and cardinalities.",
                     "Entities: MEMBER, BOOK, PUBLISHER, LOAN. Relationships: PUBLISHER publishes BOOK (1:M); MEMBER borrows BOOK through LOAN (M:N resolved by LOAN); LOAN has loan date and due date.",
                     ["entities (2)", "relationships (3)", "cardinalities (3)"]),
            _subpart("b", 6,
                     "Draw an entity-relationship diagram for the scenario.",
                     "A correct ERD shows MEMBER, BOOK, PUBLISHER and LOAN, with 1:M from PUBLISHER to BOOK, 1:M from MEMBER to LOAN, and 1:M from BOOK to LOAN. LOAN is the associative entity for the M:N borrowing relationship.",
                     ["four entities (2)", "three relationships/cardinalities (3)",
                      "associative LOAN entity (1)"]),
            _subpart("c", 6,
                     "Map the ERD to a relational schema and mark primary and foreign keys.",
                     "PUBLISHER(PublisherID PK, PublisherName); BOOK(BookID PK, Title, PublisherID FK); MEMBER(MemberID PK, MemberName); LOAN(LoanID PK, MemberID FK, BookID FK, LoanDate, DueDate).",
                     ["four relations (4)", "PK/FK marks (2)"]),
        ],
    },
    "normalization": {
        "generator_id": "ict450.normalization",
        "source": "ICT200/ICT450 KB Topic 5 Normalization",
        "stem": (
            "The relation ORDER(OrderID, CustomerID, CustomerName, ProductID, "
            "ProductName, Quantity, UnitPrice) has these functional "
            "dependencies: OrderID → CustomerID, CustomerName; CustomerID → "
            "CustomerName; ProductID → ProductName; (OrderID, ProductID) → "
            "Quantity, UnitPrice."),
        "subparts": [
            _subpart("a", 4,
                     "Identify the candidate key and all functional dependencies.",
                     "Candidate key: (OrderID, ProductID). FDs: OrderID → CustomerID, CustomerName; CustomerID → CustomerName; ProductID → ProductName; (OrderID, ProductID) → Quantity, UnitPrice.",
                     ["candidate key (2)", "FD list (2)"]),
            _subpart("b", 6,
                     "Explain 1NF, 2NF and 3NF.",
                     "1NF: all attributes are atomic. 2NF: 1NF and every non-key attribute is fully functionally dependent on the whole candidate key. 3NF: 2NF and no non-key attribute is transitively dependent on the key.",
                     ["1NF (2)", "2NF (2)", "3NF (2)"]),
            _subpart("c", 4,
                     "Identify the partial and transitive dependencies.",
                     "Partial: OrderID → CustomerID/CustomerName and ProductID → ProductName depend on part of the key. Transitive: OrderID → CustomerID → CustomerName.",
                     ["partial dependencies (2)",
                      "transitive dependency (2)"]),
            _subpart("d", 6,
                     "Decompose the relation into 3NF relations.",
                     "CUSTOMER(CustomerID PK, CustomerName); PRODUCT(ProductID PK, ProductName); ORDER_HEADER(OrderID PK, CustomerID FK); ORDER_LINE(OrderID PK, ProductID PK, Quantity, UnitPrice, FKs to ORDER_HEADER and PRODUCT).",
                     ["CUSTOMER (1.5)", "PRODUCT (1.5)",
                      "ORDER_HEADER (1.5)", "ORDER_LINE (1.5)"]),
        ],
    },
    "database_design": {
        "generator_id": "ict450.database_design",
        "source": "ICT200/ICT450 KB Topic 6 Database Design",
        "stem": (
            "{org} is planning a database for patients, doctors, appointments "
            "and prescriptions. The project will follow the database life "
            "cycle."),
        "subparts": [
            _subpart("a", 8,
                     "List FOUR phases of the database life cycle and state one activity in each.",
                     "Database initial study, database design, implementation and loading, testing and evaluation, operation, maintenance and evolution. Activities include requirements analysis, conceptual/logical design, creating storage structures, loading data, testing, and tuning.",
                     ["four phases x 2 marks (phase + activity)"]),
            _subpart("b", 4,
                     "Differentiate the SDLC and the DBLC.",
                     "SDLC covers the whole information-system life cycle; DBLC focuses on the database component within that system and runs through its own design, implementation, testing, operation and maintenance phases.",
                     ["SDLC scope (2)", "DBLC scope (2)"]),
            _subpart("c", 4,
                     "Compare top-down and bottom-up database design.",
                     "Top-down starts from the overall data model and breaks it into components. Bottom-up starts from individual data elements and combines them into a model.",
                     ["top-down (2)", "bottom-up (2)"]),
            _subpart("d", 4,
                     "Explain centralized and decentralized design.",
                     "Centralized design is controlled by one design team or location. Decentralized design distributes design work across teams or locations and requires reconciliation.",
                     ["centralized (2)", "decentralized (2)"]),
        ],
    },
    "sql": {
        "generator_id": "ict450.sql",
        "source": "ICT200/ICT450 KB Topic 7 SQL",
        "stem": (
            "The schema is STUDENT(StudentID, StudentName, Programme), "
            "COURSE(CourseID, CourseTitle, Credit) and ENROL(StudentID, "
            "CourseID, Grade). StudentID and CourseID are foreign keys in "
            "ENROL."),
        "subparts": [
            _subpart("a", 5,
                     "Write a CREATE TABLE statement for ENROL with a composite primary key and two foreign keys.",
                     "CREATE TABLE ENROL (StudentID INT, CourseID INT, Grade CHAR(2), PRIMARY KEY (StudentID, CourseID), FOREIGN KEY (StudentID) REFERENCES STUDENT(StudentID), FOREIGN KEY (CourseID) REFERENCES COURSE(CourseID));",
                     ["columns (1)", "composite PK (2)",
                      "two FKs (2)"]),
            _subpart("b", 3,
                     "Write an INSERT statement for one enrolment.",
                     "INSERT INTO ENROL (StudentID, CourseID, Grade) VALUES (1001, 'CSC429', 'A');",
                     ["INSERT syntax (2)", "values match columns (1)"]),
            _subpart("c", 6,
                     "List the names of students who scored A in Database Design.",
                     "SELECT s.StudentName FROM STUDENT s JOIN ENROL e ON s.StudentID = e.StudentID JOIN COURSE c ON e.CourseID = c.CourseID WHERE c.CourseTitle = 'Database Design' AND e.Grade = 'A';",
                     ["three-table join (3)", "two WHERE conditions (2)",
                      "selected column (1)"]),
            _subpart("d", 6,
                     "Count students in each programme, showing only programmes with more than 10 students.",
                     "SELECT Programme, COUNT(*) FROM STUDENT GROUP BY Programme HAVING COUNT(*) > 10;",
                     ["GROUP BY (2)", "COUNT (2)", "HAVING condition (2)"]),
        ],
    },
}

TOPIC_SOURCE = {
    "database_concept": "Topic 1 Database Concept",
    "data_model": "Topic 2 Data Model",
    "relational": "Topic 3 Relational Data Model",
    "erd": "Topic 4 ERD",
    "normalization": "Topic 5 Normalization",
    "database_design": "Topic 6 Database Design",
    "sql": "Topic 7 SQL",
}


def _build_question(slot: dict, index: int, seed: int) -> dict:
    template = QUESTION_BANK.get(slot["topic"])
    if template is None:
        raise ValueError(f"no ICT450 generator for topic {slot['topic']}")
    rng = random.Random(seed * 1009 + index)
    organisation = rng.choice(ORGANISATIONS[slot["topic"]])
    subparts = copy.deepcopy(template["subparts"])
    for subpart in subparts:
        subpart["text"] = subpart["text"].format(org=organisation)
    marks = sum(subpart["marks"] for subpart in subparts)
    if marks != slot["marks"]:
        raise ValueError(
            f"{slot['slot']} subpart marks {marks} != slot marks {slot['marks']}")
    return {
        "slot": slot["slot"],
        "question": slot["question"],
        "topic": slot["topic"],
        "topic_label": slot["topic_label"],
        "marks": slot["marks"],
        "generator_id": template["generator_id"],
        "source": template["source"],
        "stem": template["stem"].format(org=organisation),
        "subparts": subparts,
        "answer": "\n\n".join(
            f"{subpart['part']}. {subpart['answer']}"
            for subpart in subparts),
        "marking_points": [
            {"part": subpart["part"], "marks": subpart["marks"],
             "points": subpart["marking_points"]}
            for subpart in subparts
        ],
    }


def generate(seed: int, style: str = "modern") -> dict:
    plan = build_plan(seed, style=style)
    questions = [
        _build_question(slot, index, int(seed))
        for index, slot in enumerate(plan["slots"], start=1)
    ]
    total = sum(question["marks"] for question in questions)
    if total != 100:
        raise ValueError(f"generated paper marks {total} != 100")
    return {
        "subject": SUBJECT,
        "schema_version": 1,
        "generated_by": "src.subjects.ict450.generators",
        "seed": int(seed),
        "style": style,
        "question_count": len(questions),
        "total_marks": total,
        "questions": questions,
        "plan": plan,
        "notes": (
            "Five deterministic 20-mark structured questions. Each subpart "
            "has a model answer and marking points. No LLM was used."),
    }


def validate(seeds: list[int] | None = None) -> dict:
    seeds = seeds or list(range(1, 21))
    results = []
    for seed in seeds:
        try:
            paper = generate(seed)
            marks_ok = all(
                sum(subpart["marks"] for subpart in question["subparts"])
                == question["marks"]
                for question in paper["questions"])
            answers_ok = all(
                question["answer"].strip()
                and all(point["points"] for point in question["marking_points"])
                for question in paper["questions"])
            passed = (paper["total_marks"] == 100
                      and paper["question_count"] == 5
                      and marks_ok and answers_ok)
            results.append({
                "seed": seed, "passed": passed,
                "questions": paper["question_count"],
                "marks": paper["total_marks"],
                "topics": [question["topic"] for question in paper["questions"]],
            })
        except Exception as error:
            results.append({"seed": seed, "passed": False,
                            "error": f"{type(error).__name__}: {error}"})
    report = {
        "schema_version": 1,
        "subject": SUBJECT,
        "seeds": seeds,
        "passed": sum(1 for row in results if row["passed"]),
        "failed": sum(1 for row in results if not row["passed"]),
        "results": results,
    }
    VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", default="")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate(), indent=2))
        return
    paper = generate(args.seed)
    path = Path(args.out) if args.out else (
        TRACKING / f"generator_sample_seed_{args.seed:02d}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(paper, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(json.dumps({
        "path": str(path),
        "seed": paper["seed"],
        "questions": paper["question_count"],
        "marks": paper["total_marks"],
        "topics": [question["topic"] for question in paper["questions"]],
    }, indent=2))


if __name__ == "__main__":
    main()
