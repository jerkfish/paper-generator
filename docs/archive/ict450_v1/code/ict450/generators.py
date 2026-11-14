"""Deterministic Stage-6 generators for ICT450.

Consumes the Stage-5 planner and produces five 20-mark structured questions
with model answers and marking points.  Question text follows the real
ICT450 layout: lettered subparts, optional roman-numbered sub-subparts, and
one repurposed past-paper table, figure or diagram per question.  The wording
is original; the visual assets come from the MinerU caches.

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
from src.subjects.ict450.assets import question_assets
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


def _subpart(part, marks, text, answer, points, *, asset=False,
             children=None):
    return {
        "part": part,
        "marks": marks,
        "text": text,
        "answer": answer,
        "marking_points": points,
        "asset": asset,
        "children": children or [],
    }


QUESTION_BANK = {
    "database_concept": {
        "generator_id": "ict450.database_concept",
        "source": "ICT200/ICT450 KB Topic 1 Database Concept",
        "subparts": [
            _subpart("a", 6,
                     "Define database, DBMS and database system.",
                     "A database is an organised collection of related data. "
                     "A DBMS is software that creates, stores, manages and "
                     "controls access to a database. A database system is the "
                     "database, DBMS, application programs, people, "
                     "procedures and hardware working together.",
                     ["database definition (2)", "DBMS definition (2)",
                      "database system definition (2)"]),
            _subpart("b", 8,
                     "State FOUR limitations of the file-based approach that "
                     "a DBMS addresses.",
                     "The limitations include data redundancy, data "
                     "inconsistency, difficult data sharing, weak concurrency "
                     "control, limited security, program-data dependence, and "
                     "difficult backup and recovery.",
                     ["four limitations x 2 marks each"]),
            _subpart(
                "c", 6,
                "{org} still keeps its customer records in a spreadsheet "
                "program. Table 1 shows a sample of the data. Study Table 1 "
                "and answer the following.",
                "",
                [],
                asset=True,
                children=[
                    _subpart(
                        "i", 3,
                        "Identify TWO candidate keys and ONE primary key "
                        "from Table 1. Give ONE reason for your chosen "
                        "primary key.",
                        "Candidate keys: Customer No, Customer IC and e-mail "
                        "(any TWO). Primary key: Customer No, because it is "
                        "unique for every row and does not change.",
                        ["two candidate keys (2)",
                         "primary key with reason (1)"]),
                    _subpart(
                        "ii", 3,
                        "Explain why the spreadsheet in Table 1 is not a "
                        "substitute for a database.",
                        "A spreadsheet stores unrelated copies of data, so "
                        "the same customer can be repeated and updated "
                        "inconsistently. It lacks integrity constraints, "
                        "concurrency control, access control and recovery "
                        "facilities that a DBMS provides.",
                        ["redundancy and inconsistency (1)",
                         "missing integrity constraints (1)",
                         "missing concurrency, security or recovery (1)"]),
                ]),
        ],
    },
    "data_model": {
        "generator_id": "ict450.data_model",
        "source": "ICT200/ICT450 KB Topic 2 Data Model",
        "subparts": [
            _subpart("a", 4,
                     "Define data model and schema.",
                     "A data model is a collection of concepts used to "
                     "describe the structure of a database. A schema is the "
                     "description of the database structure, including "
                     "tables, attributes and relationships.",
                     ["data model definition (2)", "schema definition (2)"]),
            _subpart("b", 9,
                     "Compare the hierarchical, network and relational data "
                     "models.",
                     "Hierarchical: tree structure with one parent per "
                     "child. Network: graph structure with many-to-many "
                     "links through sets. Relational: tables, rows and "
                     "columns with keys; supports flexible querying and "
                     "many-to-many relationships through junction tables.",
                     ["hierarchical structure/limitation (3)",
                      "network structure/limitation (3)",
                      "relational structure/advantage (3)"]),
            _subpart(
                "c", 7,
                "{org} stores book and publisher data in a relational "
                "database. Table 1 shows the BOOKS table and Table 2 shows "
                "the PUBLISHERS table. Study both tables and answer the "
                "following.",
                "",
                [],
                asset=True,
                children=[
                    _subpart(
                        "i", 4,
                        "Identify the relationship and cardinality between "
                        "the two tables. Justify your answer using the data.",
                        "PUBLISHERS is the parent table and BOOKS is the "
                        "child table. One publisher can publish many books, "
                        "while each book has at most one publisher. This is "
                        "a one-to-many (1:M) relationship; the PublisherID "
                        "value in BOOKS matches one PublisherID in "
                        "PUBLISHERS.",
                        ["relationship identified (2)",
                         "1:M cardinality (1)", "data justification (1)"]),
                    _subpart(
                        "ii", 3,
                        "Explain how the relational model represents this "
                        "relationship using keys.",
                        "PublisherID is the primary key of PUBLISHERS and a "
                        "foreign key in BOOKS. Each BOOKS row stores the "
                        "PublisherID of its publisher, and the foreign key "
                        "enforces referential integrity.",
                        ["primary and foreign key roles (2)",
                         "referential integrity (1)"]),
                ]),
        ],
    },
    "relational": {
        "generator_id": "ict450.relational_model",
        "source": "ICT200/ICT450 KB Topic 3 Relational Data Model",
        "subparts": [
            _subpart(
                "a", 4,
                "{org} keeps its student and course records in the tables "
                "shown below. Table 1 shows the STUDENT table and Table 2 "
                "shows the COURSE table. Identify the primary key of each "
                "table and TWO candidate keys in the STUDENT table.",
                "STUDENT: primary key Student_ID; candidate keys Student_IC, "
                "Student_ID and EMAIL. COURSE: primary key COURSE_ID.",
                ["STUDENT primary key (1)", "two candidate keys (2)",
                 "COURSE primary key (1)"],
                asset=True),
            _subpart("b", 6,
                     "Explain entity integrity and referential integrity. "
                     "Give ONE example from Table 1 and Table 2.",
                     "Entity integrity: a primary-key column cannot contain "
                     "a null or duplicate value. Referential integrity: a "
                     "foreign-key value must match an existing primary-key "
                     "value or be null. Example: every COURSE_ID in STUDENT "
                     "must exist in COURSE, and STUDENT_ID must be unique "
                     "and not null.",
                     ["entity integrity definition (2)",
                      "referential integrity definition (2)",
                      "example from the tables (2)"]),
            _subpart("c", 4,
                     "Define tuple, attribute, degree and cardinality.",
                     "Tuple = a row; attribute = a column; degree = number "
                     "of attributes; cardinality = number of tuples.",
                     ["one mark each"]),
            _subpart("d", 6,
                     "Explain TWO update anomalies that can occur in the "
                     "STUDENT table if course details are stored together "
                     "with student details.",
                     "If COURSE_NAME is repeated for every student, changing "
                     "a course name in one row but not the others causes an "
                     "update anomaly. Deleting the last student for a course "
                     "loses the course data (delete anomaly), and adding a "
                     "new course before any student enrols is difficult "
                     "(insert anomaly).",
                     ["two anomalies explained x 3 marks"]),
        ],
    },
    "erd": {
        "generator_id": "ict450.erd",
        "source": "ICT200/ICT450 KB Topic 4 ERD",
        "subparts": [
            _subpart(
                "a", 8,
                "Figure 1 shows part of an ERD for a supplier and product "
                "database. Identify the entities, their attributes, the "
                "relationship between them and the cardinalities shown.",
                "Entities: VENDOR with VEND_CODE, VEND_CONTACT, "
                "VEND_AREACODE and VEND_PHONE; PRODUCT with PROD_CODE, "
                "PROD_DESCRIPT, PROD_PRICE, PROD_ON_HAND and VEND_CODE. "
                "Relationship: VENDOR supplies PRODUCT. Cardinality: one "
                "VENDOR supplies many PRODUCTs (1:M).",
                ["entities (2)", "attributes (2)", "relationship (2)",
                 "cardinality (2)"],
                asset=True),
            _subpart("b", 6,
                     "Explain the referential integrity constraint shown in "
                     "Figure 1. Give ONE example of an operation that would "
                     "violate it.",
                     "PRODUCT.VEND_CODE is a foreign key that must match an "
                     "existing VENDOR.VEND_CODE or be null. Inserting a "
                     "PRODUCT with a VEND_CODE that does not exist in "
                     "VENDOR violates referential integrity; deleting a "
                     "VENDOR that still has PRODUCTs also violates it unless "
                     "the products are deleted or reassigned.",
                     ["foreign-key constraint (3)",
                      "violation example (3)"]),
            _subpart("c", 6,
                     "Map the ERD in Figure 1 to a relational schema. Mark "
                     "the primary key and foreign key.",
                     "VENDOR(VEND_CODE PK, VEND_CONTACT, VEND_AREACODE, "
                     "VEND_PHONE); PRODUCT(PROD_CODE PK, PROD_DESCRIPT, "
                     "PROD_PRICE, PROD_ON_HAND, VEND_CODE FK REFERENCES "
                     "VENDOR(VEND_CODE)).",
                     ["VENDOR relation and primary key (3)",
                      "PRODUCT relation, primary key and foreign key (3)"]),
        ],
    },
    "normalization": {
        "generator_id": "ict450.normalization",
        "source": "ICT200/ICT450 KB Topic 5 Normalization",
        "subparts": [
            _subpart(
                "a", 4,
                "The spreadsheet in Table 1 shows course and student "
                "records for a college. Study Table 1 and identify the "
                "candidate key and all functional dependencies.",
                "Relation: COURSE_RECORD(CourseCode, CourseName, TutorID, "
                "TutorName, StudentID, StudentName, DOB, Gender, "
                "LastAttendance). Candidate key: (CourseCode, StudentID). "
                "FDs: CourseCode -> CourseName, TutorID, TutorName; "
                "StudentID -> StudentName, DOB, Gender; (CourseCode, "
                "StudentID) -> LastAttendance.",
                ["candidate key (2)", "functional dependencies (2)"],
                asset=True),
            _subpart("b", 6,
                     "Explain 1NF, 2NF and 3NF.",
                     "1NF: all attributes are atomic. 2NF: 1NF and every "
                     "non-key attribute is fully functionally dependent on "
                     "the whole candidate key. 3NF: 2NF and no non-key "
                     "attribute is transitively dependent on the key.",
                     ["1NF (2)", "2NF (2)", "3NF (2)"]),
            _subpart("c", 4,
                     "Identify the partial and transitive dependencies in "
                     "Table 1.",
                     "Partial: CourseCode -> CourseName, TutorID, TutorName "
                     "depends on part of the key; StudentID -> StudentName, "
                     "DOB, Gender depends on part of the key. Transitive: "
                     "CourseCode -> TutorID -> TutorName.",
                     ["partial dependencies (2)",
                      "transitive dependency (2)"]),
            _subpart("d", 6,
                     "Decompose Table 1 into 3NF relations. Show the "
                     "primary and foreign keys.",
                     "COURSE(CourseCode PK, CourseName, TutorID FK); "
                     "TUTOR(TutorID PK, TutorName); STUDENT(StudentID PK, "
                     "StudentName, DOB, Gender); ATTENDANCE(CourseCode PK, "
                     "StudentID PK, LastAttendance, FKs to COURSE and "
                     "STUDENT).",
                     ["four relations (4)", "primary and foreign keys (2)"]),
        ],
    },
    "database_design": {
        "generator_id": "ict450.database_design",
        "source": "ICT200/ICT450 KB Topic 6 Database Design",
        "subparts": [
            _subpart(
                "a", 8,
                "Figure 1 shows the database design process. Explain FOUR "
                "activities carried out during the database design phase.",
                "Conceptual design: identify entities, attributes and "
                "relationships and build a conceptual model. Logical "
                "design: map the conceptual model to a relational schema, "
                "choose keys and normalize. Physical design: choose storage "
                "structures, indexes, file organisation and access paths. "
                "Implementation: create the database objects and load the "
                "data.",
                ["conceptual design (2)", "logical design (2)",
                 "physical design (2)", "implementation (2)"],
                asset=True),
            _subpart("b", 4,
                     "Differentiate the SDLC and the DBLC.",
                     "SDLC covers the whole information-system life cycle; "
                     "DBLC focuses on the database component within that "
                     "system and runs through its own design, "
                     "implementation, testing, operation and maintenance "
                     "phases.",
                     ["SDLC scope (2)", "DBLC scope (2)"]),
            _subpart("c", 4,
                     "Compare top-down and bottom-up database design.",
                     "Top-down starts from the overall data model and "
                     "breaks it into components. Bottom-up starts from "
                     "individual data elements and combines them into a "
                     "model.",
                     ["top-down (2)", "bottom-up (2)"]),
            _subpart("d", 4,
                     "Explain centralized and decentralized design.",
                     "Centralized design is controlled by one design team "
                     "or location. Decentralized design distributes design "
                     "work across teams or locations and requires "
                     "reconciliation.",
                     ["centralized (2)", "decentralized (2)"]),
        ],
    },
    "sql": {
        "generator_id": "ict450.sql",
        "source": "ICT200/ICT450 KB Topic 7 SQL",
        "subparts": [
            _subpart(
                "a", 5,
                "Table 1 shows the relational schema for a loan management "
                "system used by {org}. Write a CREATE TABLE statement for "
                "APPLYLOAN. Include the composite primary key and the "
                "foreign keys to CLIENT and LOAN.",
                "CREATE TABLE APPLYLOAN (ClientNum INT, LoanID INT, "
                "LoanTotal DECIMAL(10,2), LoanRemainder DECIMAL(10,2), "
                "LoanDate DATE, PRIMARY KEY (ClientNum, LoanID), FOREIGN "
                "KEY (ClientNum) REFERENCES CLIENT(ClientNum), FOREIGN KEY "
                "(LoanID) REFERENCES LOAN(LoanID));",
                ["columns (2)", "composite primary key (1)",
                 "two foreign keys (2)"],
                asset=True),
            _subpart("b", 3,
                     "Write an INSERT statement to add a new application "
                     "for client C001 for loan L10 with a total of 50000, a "
                     "remainder of 50000 and the date 2026-01-15.",
                     "INSERT INTO APPLYLOAN (ClientNum, LoanID, LoanTotal, "
                     "LoanRemainder, LoanDate) VALUES ('C001', 'L10', "
                     "50000, 50000, '2026-01-15');",
                     ["INSERT syntax (2)", "values match columns (1)"]),
            _subpart("c", 6,
                     "List the client names and loan totals for "
                     "applications with a total loan above 40000. Use a "
                     "join between APPLYLOAN and CLIENT.",
                     "SELECT c.ClientName, a.LoanTotal FROM APPLYLOAN a "
                     "JOIN CLIENT c ON a.ClientNum = c.ClientNum WHERE "
                     "a.LoanTotal > 40000;",
                     ["join (2)", "condition (2)",
                      "selected columns (2)"]),
            _subpart("d", 6,
                     "For each loan type, show the number of applications "
                     "and the total loan amount. Include only loan types "
                     "with more than two applications.",
                     "SELECT l.LoanType, COUNT(*) AS Applications, "
                     "SUM(a.LoanTotal) AS TotalLoan FROM APPLYLOAN a JOIN "
                     "LOAN l ON a.LoanID = l.LoanID GROUP BY l.LoanType "
                     "HAVING COUNT(*) > 2;",
                     ["join (1)", "GROUP BY (1)", "COUNT and SUM (2)",
                      "HAVING (2)"]),
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


def _leaf_marks(subpart: dict) -> int:
    if subpart.get("children"):
        return sum(_leaf_marks(child) for child in subpart["children"])
    return subpart["marks"]


def _leaves(subparts: list[dict], prefix: str = ""):
    for subpart in subparts:
        label = f"{prefix}{subpart['part']}"
        if subpart.get("children"):
            yield from _leaves(subpart["children"], label + " ")
        else:
            yield label, subpart


def _build_question(slot: dict, index: int, seed: int) -> dict:
    template = QUESTION_BANK.get(slot["topic"])
    if template is None:
        raise ValueError(f"no ICT450 generator for topic {slot['topic']}")
    rng = random.Random(seed * 1009 + index)
    organisation = rng.choice(ORGANISATIONS[slot["topic"]])
    subparts = copy.deepcopy(template["subparts"])

    def prepare(parts):
        for subpart in parts:
            subpart["text"] = subpart["text"].format(org=organisation)
            prepare(subpart.get("children", []))

    prepare(subparts)
    marks = sum(_leaf_marks(subpart) for subpart in subparts)
    if marks != slot["marks"]:
        raise ValueError(
            f"{slot['slot']} subpart marks {marks} != slot marks {slot['marks']}")
    assets = question_assets(slot["topic"], seed)
    leaves = list(_leaves(subparts))
    return {
        "slot": slot["slot"],
        "question": slot["question"],
        "topic": slot["topic"],
        "topic_label": slot["topic_label"],
        "marks": slot["marks"],
        "generator_id": template["generator_id"],
        "source": template["source"],
        "assets": assets,
        "subparts": subparts,
        "answer": "\n\n".join(
            f"{label}) {leaf['answer']}" for label, leaf in leaves),
        "marking_points": [
            {"part": label, "marks": leaf["marks"],
             "points": leaf["marking_points"]}
            for label, leaf in leaves
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
            "Five deterministic 20-mark structured questions. Each question "
            "reuses a past-paper table, figure or diagram from the MinerU "
            "cache. No LLM was used."),
    }


def validate(seeds: list[int] | None = None) -> dict:
    seeds = seeds or list(range(1, 21))
    results = []
    for seed in seeds:
        try:
            paper = generate(seed)
            marks_ok = all(
                sum(_leaf_marks(subpart) for subpart in question["subparts"])
                == question["marks"]
                for question in paper["questions"])
            assets_ok = all(question["assets"]
                            for question in paper["questions"])
            answers_ok = all(
                question["answer"].strip()
                and all(point["points"] for point in question["marking_points"])
                for question in paper["questions"])
            passed = (paper["total_marks"] == 100
                      and paper["question_count"] == 5
                      and marks_ok and assets_ok and answers_ok)
            results.append({
                "seed": seed, "passed": passed,
                "questions": paper["question_count"],
                "marks": paper["total_marks"],
                "assets": sum(len(question["assets"])
                              for question in paper["questions"]),
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
        "assets": [len(question["assets"]) for question in paper["questions"]],
        "topics": [question["topic"] for question in paper["questions"]],
    }, indent=2))


if __name__ == "__main__":
    main()
