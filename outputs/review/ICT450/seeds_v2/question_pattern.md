# ICT450 — question-turn pattern across past papers

Date: **2026-11-11**
Source: 12 ICT450 papers in the approved bank (60 questions), plus the V1
dossiers. Every question was read and classified; the machine-readable table is
`data/tracking/ict450/v2/question_pattern.json`.

## Finding

The papers follow a stable five-slot progression:

| Slot | Role | What the question asks |
|---|---|---|
| **Q1** | Concepts / fundamentals | Data vs information, database vs file system or spreadsheet, DBMS functions, database environment, data-model overview |
| **Q2** | Design theory | DBLC/SDLC, conceptual/logical/physical design, business rules, data-model families (hierarchical/network/relational), constraints and integrity, backup/recovery, indexing, security, mobile databases |
| **Q3** | Normalization | A redundant table/form/invoice/receipt/report: identify the normal form, keys and dependencies, then normalize to 3NF |
| **Q4** | SQL | A relational schema: DDL/DML, joins, aggregates and subqueries |
| **Q5** | ERD design | A business-rule scenario: construct the ERD with entities, attributes, relationships and cardinality; then explain reports from it |

In short: **concepts → design theory → normalization → SQL → ERD**.

## Per-paper order

| Paper | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| 2018-DEC | Concepts | Design theory | SQL | Normalization | ERD |
| 2018-JUN | Concepts | Design theory | Normalization | SQL | ERD |
| 2019-DEC | Concepts | Design theory | SQL | Normalization | ERD |
| 2019-JUN | Concepts | Design theory | SQL | Normalization | ERD |
| 2022-FEB | Concepts | Design theory | Normalization | SQL | ERD |
| 2023-FEB | Concepts | Design theory | Normalization | SQL | ERD |
| 2023-JUL | Concepts | Design theory | Normalization | SQL | ERD |
| 2024-JAN | Concepts | Design theory | Normalization | SQL | ERD |
| 2024-JUL | Concepts | Design theory | Normalization | SQL | ERD |
| 2025-FEB | Concepts | Design theory | Normalization | SQL | ERD |
| 2025-JUL | Concepts | Design theory | Normalization | SQL | ERD |
| 2026-FEB | Concepts | Design theory | Normalization | SQL | ERD |

### Counts

- Q1 concepts: **12/12**
- Q2 design theory: **12/12**
- Q5 ERD: **12/12**
- Q3/Q4 contain exactly one normalization question and one SQL question:
  **12/12**
- Q3 = normalization and Q4 = SQL in **9/12** (75%); the three older papers
  `2018-DEC`, `2019-DEC` and `2019-JUN` swap them.

## Repeated internal structure

- **Q3 normalization** in modern papers is almost always **3 + 6 + 11 = 20
  marks**: normal form/problems (3), keys and dependencies (6), normalize to
  3NF (11). Older papers vary (3+7+10, 2+2+16, 3+3+14).
- **Q5 ERD** is almost always **16 + 4 = 20 marks**: construct the ERD (16)
  and explain reports/information from it (4).
- **Q4 SQL** is 20 marks spread over 5–8 tasks: create table, insert/update,
  SELECT, joins, aggregates, subqueries.
- **Q1/Q2** are theory questions with 3–5 subparts, no ERD/SQL task.

## What is wrong with the current seeds

The current seeds were selected by a generic 20-mark slot planner. They do not
follow the pattern:

| Seed | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| 1 | ERD | Design theory | ERD | Design theory | Normalization |
| 2 | ERD | Normalization | SQL | ERD | SQL |
| 3 | Design theory | SQL | Concepts | ERD | Normalization |

The slots are therefore out of order. Q5-type ERD questions appear as Q1/Q3/Q4,
normalization appears as Q5, and SQL appears as Q2/Q5.

## Proposed correction

Build each seed by **slot category**, not by mark count alone:

1. **Q1** — concepts/fundamentals question.
2. **Q2** — design-theory question.
3. **Q3** — normalization question (prefer the modern 3+6+11 structure).
4. **Q4** — SQL question.
5. **Q5** — ERD question (prefer 16+4).

For the three older papers that swap Q3/Q4, re-slot their normalization
question to Q3 and their SQL question to Q4; the question text is independent
of its original paper position.

Other constraints:

- one question per slot class, no repeats inside a seed;
- five distinct source papers per seed;
- approved-only questions;
- the four 14/16-mark questions remain excluded (owner instruction to ignore
  the mark slots).

The category table is already saved at
`data/tracking/ict450/v2/question_pattern.json`. The assembler should read it
and map each seed slot to its category before selecting questions.

## Gate B

Gate B should not be approved yet. The three existing seeds have the wrong
question arrangement. After this pattern is accepted, rebuild seeds 1–3 with
the Q1–Q5 category order above, regenerate the DOCX/PDF, and review again.
