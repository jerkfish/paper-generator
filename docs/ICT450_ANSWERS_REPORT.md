# ICT450 — V4 answer report (seed 1–3 pilot)

Date: **2026-11-11**

Scope: start V4 by building complete reference answers for the 15 distinct
questions used by seeds 1–3, then render marking schemes for those seeds.

Status: the owner **approved these V4 model answers on 2026-11-11**. The
seed 1–3 schemes are attached to the local Library cache, and the 45 remaining
questions are still open.

## Coverage

| Item | Value |
|---|---:|
| Approved questions in bank | 60 |
| Questions answered | **15** |
| Questions still to answer | **45** |
| Provenance | `model_unofficial` for all 15 |
| Confidence high / medium | 10 / 5 |
| Answer mark totals reconciled | 15/15 |
| ERD answer diagrams | 3 |
| LLM calls / cost | 0 / **$0.00** |

No official ICT450 marking scheme or published answer set was supplied. Every
answer is therefore a model answer, labelled `model_unofficial` and not an
official UTM scheme. The answer text is grounded in the approved question text,
the supplied asset data (invoice, report, order form and tables) and the
attached **ICT200/ICT450 knowledge base**.

## Knowledge-base basis

The answer content was checked against these course documents in the attached
knowledge base (id `39367590-f20f-4383-8adf-721753d49e1c`):

- `TOPIC 1 DATABASE CONCEPT (1).pdf` — database environment, file-system
  limitations, data versus information.
- `TOPIC 2 DATA MODEL (1).pdf` — data-model building blocks, big data,
  Hadoop/HDFS/MapReduce, NoSQL, network-model disadvantages.
- `TOPIC 3 RELATIONAL DATA MODELstu.pdf` — relational-table characteristics,
  keys, data dictionary, Crow's Foot basics.
- `TOPIC 4 ERD_stu (2).pdf` — entities, attributes, relationships,
  cardinalities and ERD development.
- `TOPIC 5 NORMALIZATION (1).pdf` — 1NF, 2NF, 3NF and dependency diagrams.
- `TOPIC 6 DATABASE DESIGN (1).pdf` — SDLC/DBLC, initial-study activities,
  designer's view, implementation and loading.
- `TOPIC 7 SQL.pdf` — SQL statements and database structure.

Corrections made after reading the knowledge base: the four initial-study
activities now follow the course list (analyse company, define
problems/constraints, define objectives, define scope/boundaries); DBLC has the
six course phases; data-dictionary features use the course definition; network
model disadvantages use "cumbersome / no ad hoc query / structural change";
designer views are data structure, access and activities; big-data technologies
are Hadoop/HDFS, MapReduce and NoSQL; file-system limitations use the course
list.

## Seed coverage

| Seed | Q1 concepts | Q2 design theory | Q3 normalization | Q4 SQL | Q5 ERD |
|---|---|---|---|---|---|
| 1 | `2018-DEC-Q1` | `2018-JUN-Q2` | `2019-DEC-Q4` | `2019-JUN-Q3` | `2022-FEB-Q5` |
| 2 | `2023-JUL-Q1` | `2023-FEB-Q2` | `2024-JAN-Q3` | `2024-JUL-Q4` | `2025-FEB-Q5` |
| 3 | `2026-FEB-Q1` | `2025-JUL-Q2` | `2018-DEC-Q4` | `2019-DEC-Q3` | `2018-JUN-Q5` |

## Presentation

- **SQL answers** are set in Consolas with a shaded code block; the DDL, DML,
  joins, aggregates and subqueries are kept as executable statements.
- **Normalization answers** use HTML-style relation blocks and bordered tables
  for 1NF, 2NF and 3NF sample data; the wide order-form tables were split into
  header and item-line tables so they remain readable on A4.
- **ERD answers** are generated as HTML/SVG diagrams with Crow's Foot
  cardinalities, primary/foreign-key markers and relationship labels, then
  rendered to high-resolution PNG for the scheme.
- **Marking points** follow the extracted sub-part marks; every answer
  reconciles to the question's 20 marks.

## Assumptions recorded

- `2019-DEC-Q3`: the printed schema has no customer identifier in `ACCOUNT` or
  `LOAN`. The answer assumes `ACCOUNT.custIC` and `LOAN.custIC` as foreign keys
  to `CUSTOMER`; without such a link the customer-level queries cannot be
  written. This is stated in the answer and in the scheme.
- `2024-JAN-Q3`: project code `ST01` appears twice with different locations, so
  the assignment key is `(EmployeeID, ProjectCode, Location)`. The 3NF split
  treats `ProjectCode` as the project identifier and location as part of the
  assignment.
- ERD answers: the volunteer answer uses `ASSIGNMENT` for project
  participation; the art answer shows many-to-many relationships directly and
  lists the program subtype attributes; the dental answer uses
  `PATIENT_TREATMENT` for tooth/diagnosis and treatment subtypes. These
  assumptions are printed with each ERD answer.

## Marking schemes

| Seed | Pages | Images | Right/bottom overflow | Forbidden tokens | QA |
|---|---:|---:|---|---|---|
| 1 | 8 | 4 | none | none | clean |
| 2 | 9 | 4 | none | none | clean |
| 3 | 8 | 4 | none | none | clean |

Each scheme starts from the approved clean scheme template, patches the notes,
clears the template body and renders every question from the V4 answer bank
with the marking guide, provenance, knowledge-base basis and assumptions. The
DOCX and PDF files are copied into the seed library cache and registered in
`meta.json` and `library_manifest.json`.

## Evidence

- `data/tracking/ict450/v2/bank/answers.json`
- `data/tracking/ict450/v2/bank/answers_report.json`
- `data/tracking/ict450/v2/bank/answers/media/` — three ERD PNGs
- `data/tracking/ict450/v2/bank/review/answers.html` — visual review sheet
- `outputs/review/ICT450/answers_v1/answers.html` — review copy with the
  three ERD PNGs beside it
- `outputs/review/ICT450/schemes_v1/seed_01_scheme.docx` / `.pdf`
- `outputs/review/ICT450/schemes_v1/seed_02_scheme.docx` / `.pdf`
- `outputs/review/ICT450/schemes_v1/seed_03_scheme.docx` / `.pdf`
- `outputs/review/ICT450/schemes_v1/seed_*_qa.json`

## Remaining work

V4 is **in progress**: the seed 1–3 pilot is complete, but 45 approved
questions still need answers before V4 can be marked done. After that, the
remaining Library schemes can be built and the library cache can carry paper
and scheme files. Gate C and publication remain untouched.
