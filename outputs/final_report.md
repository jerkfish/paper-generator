# CSC662 mock paper 02 - planner revision, theory module and report

Generated locally from the 35 past papers and the read-only CSC662 lecture decks. No original paper or deck was modified.

## Deliverables

- `outputs/mock_paper_02.docx` / `.pdf` - realistic-mode paper, 4 pages.
- `outputs/mock_scheme_02.docx` / `.pdf` - marking scheme, 13 pages.
- `outputs/planner_revised_realistic.json` / `.md` - revised slot table.
- `outputs/theory_drafts_realistic.json` / `.md` - verified theory questions and sources.
- `outputs/vigenere_tableau.png` - 26 x 26 tableau printed after Q2(b).
- `outputs/final_report.md` / `.pdf` - this report (7 pages in the PDF render).

## 1. Measurements (reported before the planner was changed)

- Clean modern papers: **10**; papers with explicit Part A/B labels used for pair/part measures: **8** (CSC662-2019-06, CSC662-2019-12, CSC662-2022-02, CSC662-2023-02, CSC662-2024-07, CSC662-2025-02, CSC662-2025-07, CSC662-2026-02).
- Coverage caveat: 2018-01 and 2018-06 use a numeric-question layout with no A/B labels and are excluded from the pair/part measures; 2025-07 has incomplete/noisy A/B extraction. 2026-02 marks are noisy in places but its valid pairs are included.

### (a) Part A (a)/(b) relationship

- Pairs measured: **72**.
- Same topic: **55/72 (76.4%)**.
- (b) explicitly refers to (a) / the above / the scenario: **7/72 (9.7%)**.

Dependency regex: `your answer in (a)`, `answer in (a)`, `the above`, `based on the above`, `scenario above`, `given scenario`, `this scenario`, `same scenario`, `in part (a)`, `using your answer`.

### (b) Command-word distribution by part

| Label | Part A rows | Part A marks | Part B rows | Part B marks |
|---|---:|---:|---:|---:|
| State | 31 | 110 | 7 | 35 |
| List | 12 | 28 | 0 | 0 |
| Explain | 56 | 198 | 13 | 54 |
| Describe | 16 | 84 | 2 | 8 |
| Discuss | 17 | 90 | 5 | 27 |
| Compare | 3 | 18 | 0 | 0 |
| Justify | 4 | 24 | 5 | 28 |
| Other | 7 | 30 | 11 | 44 |

Raw phrasing mapped to the seven labels: define -> Describe; what is -> Explain; identify/give/name -> State; why/how -> Explain; propose/suggest/support -> Justify; differentiate -> Compare. `Other` means no mapped command word and is never used as a generated slot label.

### (c) Topic distribution in Part B

| Topic | Rows | Marks |
|---|---:|---:|
| risk/management | 9 | 39 |
| attacks/malware | 8 | 36 |
| access control models | 8 | 35 |
| authentication/biometrics | 5 | 23 |
| software/OS security | 3 | 15 |
| trusted computing/blockchain | 2 | 10 |
| general cryptography | 2 | 10 |
| hashing/signatures | 2 | 10 |
| network security | 1 | 6 |
| block ciphers | 1 | 5 |
| public-key | 1 | 5 |
| other | 1 | 2 |

Part B topic and task mix is used separately from Part A: the two Part B questions take the two largest measured Part B topic shares (risk/management 39 marks, attacks/malware 36), and the four Part B slots take the measured Part B 5-mark command mix (Explain 2, State 1, Discuss 1 in this seed).

## 2. Revised planner table (realistic mode, seed 9)

- 24 slots, 100 marks: Part A 80, Part B 20; computed marks **6** (clean-modern mean 4.0).
- Question topics: `A1:network security -> A2:classical ciphers -> A3:trusted computing/blockchain -> A4:authentication/biometrics -> A5:software/OS security -> A6:attacks/malware -> A7:access control models -> A8:attacks/malware -> A9:authentication/biometrics -> A10:access control models -> B1:risk/management (ethics) -> B2:attacks/malware`.
- One topic per question: **yes**; no more than two consecutive questions with the same topic: **PASS**.
- Dependent pair(s): **A3** (1 of 9 Part A theory pairs = 11.1%, close to the measured 9.7%).

| Slot | Marks | Kind | Topic | Command | Computed type | Target size / key | Style exact / mode | Low conf. | Dependent | Notes |
|---|---:|---|---|---|---|---|---|---|---|---|
| A1a | 2 | theory | network security | Explain |  |  | 17 / exact |  |  | style n=17 |
| A1b | 6 | theory | network security | Explain |  |  | 3 / exact |  |  | style n=3 |
| A2a | 2 | theory | classical ciphers | List |  |  | 0 / topic+marks (any command) | yes |  | style n=0; widened to topic+marks (any command); low style confidence |
| A2b | 6 | computed | classical ciphers | compute | Vigenere | 13-18 letters; keyword 6-8 letters |  |  |  | computed slot; print the 26 x 26 Vigenere tableau in the question |
| A3a | 2 | theory | trusted computing/blockchain | State |  |  | 4 / exact |  | yes | style n=4; dependent pair |
| A3b | 6 | theory | trusted computing/blockchain | Justify |  |  | 0 / topic+marks (any command) | yes | yes | style n=0; widened to topic+marks (any command); low style confidence; dependent pair |
| A4a | 2 | theory | authentication/biometrics | Explain |  |  | 11 / exact |  |  | style n=11 |
| A4b | 6 | theory | authentication/biometrics | Discuss |  |  | 5 / exact |  |  | style n=5 |
| A5a | 2 | theory | software/OS security | State |  |  | 2 / topic+marks (any command) | yes |  | style n=2; widened to topic+marks (any command); low style confidence |
| A5b | 6 | theory | software/OS security | Describe |  |  | 2 / topic+marks (any command) | yes |  | style n=2; widened to topic+marks (any command); low style confidence |
| A6a | 2 | theory | attacks/malware | List |  |  | 0 / topic+marks (any command) | yes |  | style n=0; widened to topic+marks (any command); low style confidence |
| A6b | 6 | theory | attacks/malware | Describe |  |  | 12 / exact |  |  | style n=12 |
| A7a | 2 | theory | access control models | Explain |  |  | 5 / exact |  |  | style n=5 |
| A7b | 6 | theory | access control models | State |  |  | 1 / topic+marks (any command) | yes |  | style n=1; widened to topic+marks (any command); low style confidence |
| A8a | 2 | theory | attacks/malware | State |  |  | 6 / exact |  |  | style n=6 |
| A8b | 6 | theory | attacks/malware | State |  |  | 5 / exact |  |  | style n=5 |
| A9a | 2 | theory | authentication/biometrics | Explain |  |  | 11 / exact |  |  | style n=11 |
| A9b | 6 | theory | authentication/biometrics | Discuss |  |  | 5 / exact |  |  | style n=5 |
| A10a | 2 | theory | access control models | Explain |  |  | 5 / exact |  |  | style n=5 |
| A10b | 6 | theory | access control models | Explain |  |  | 4 / exact |  |  | style n=4 |
| B1a | 5 | theory | risk/management (ethics) | Explain |  |  | 2 / topic+marks (any command) | yes |  | style n=2; widened to topic+marks (any command); low style confidence |
| B1b | 5 | theory | risk/management (ethics) | State |  |  | 2 / topic+marks (any command) | yes |  | style n=2; widened to topic+marks (any command); low style confidence |
| B2a | 5 | theory | attacks/malware | Explain |  |  | 1 / topic+marks (any command) | yes |  | style n=1; widened to topic+marks (any command); low style confidence |
| B2b | 5 | theory | attacks/malware | Discuss |  |  | 0 / topic+marks (any command) | yes |  | style n=0; widened to topic+marks (any command); low style confidence |

### Topic allocation vs modern share

| Topic | Modern weight | Target marks | Assigned theory marks |
|---|---:|---:|---:|
| attacks/malware | 0.290 | 27 | 26 |
| authentication/biometrics | 0.189 | 17 | 16 |
| access control models | 0.147 | 14 | 16 |
| trusted computing/blockchain | 0.096 | 9 | 8 |
| software/OS security | 0.058 | 5 | 8 |
| network security | 0.068 | 6 | 8 |
| risk/management (ethics) | 0.152 | 14 | 10 |

The planner renormalised the seven theory topics after adding `risk/management (ethics)` (modern risk marks = 119; source deck 071 Ethics). Planned-vs-target differences are reported rather than hidden: risk is 10 vs 14 target, software/OS 8 vs 5, network 8 vs 6, access control 16 vs 14. A 2-mark theory slot paired with the computed Vigenere question is on `classical ciphers` (one-topic-per-question rule) and sits outside the seven-topic target.

Coverage note: 173 of 955 modern non-compute marks (18.1%) fall in topics outside the seven (other, general cryptography, classical ciphers, public-key, hashing/signatures, block ciphers) and were not reallocated. The ethics deck contributes 16 text chunks from 18 slides (slides 1,3-9,11-18), 6,387 characters.

## 3. Three real 6-mark examples per command label used at 6 marks

The labels used at 6 marks in this paper are State, Explain, Describe, Discuss and Justify. These are real past questions whose marks column is 6; noisy OCR/header text was skipped for the display.

### State

- **CSC662-2009-04 Q1d**: Determine whether the P-box with the following tables is a straight P-box, a compression P-box or an expansion P-box. State one reason for each table.  i)  ii)  iii)  112 3 44  15 3 6 78  2 14 3 56
- **CSC662-2010-10 Q11b**: Assuming that high > low, identify program fragments that are desired (allowed) or  undesired (prevented) in information security flows for reading operation.
- **CSC662-2014-06 Q15a**: State THREE (3) purposes of today's implementation of steganography.

### Explain

- **CSC662-2007-10 Q1a**: Explain how three goals of computer security relate with each other in building a secure system.
- **CSC662-2008-10 Q2b**: Recently, there are many types of malware infection had been reported to the security organization. Explain the characteristics of THREE (3) types of malware that you know.
- **CSC662-2009-04 Q2b**: A company is said as having a secured computer system. In your own words explain what it is meant by the term a secured computer system.

### Describe

- **CSC662-2006-10 Q1a**: Describe the difference between vulnerability, threat and control, by using one example.
- **CSC662-2007-04 Q1a**: Define the following terms: i) Firewall ii) Integrity iii) Vulnerability
- **CSC662-2007-04 Q2b**: Describe the term malicious code and explain TWO (2) examples of them.

### Discuss

- **CSC662-2010-04 Q11**: Discuss THREE (3) approaches that can be used to create good passwords.  (6 marks)
- **CSC662-2010-10 Q3b**: Discuss THREE (3) important characteristics of 'economically feasible" security.
- **CSC662-2012-06 Q15**: Software security is a system-wide issue that involves both building in security mechanisms and designing the system to be robust. Discuss the following software security mechanism: a) Data execution protection b) Address space layout randomization c) Canary

### Justify

- **CSC662-2016-12 Q11ii**: Suggest ONE (1) unique type of biometric methods for each of the situation below and give a reason. ii. iii. Entry and exit points in a nuclear research center.
- **CSC662-2025-07 QA1b**: Propose how a biometric authentication system can be integrated into the hospital's access control process. Discuss THREE (3) factors that must be considered to ensure its effecliveness and security.
- **CSC662-2025-07 QB4b**: Propose THREE (3) different methods the developer could use to prevent such code injection attacks.

## 4. Theory module

### Pipeline

- Deck ingestion: python-pptx, read-only from the KB folder `C:/Users/Ahmad/Desktop/CSC662`; 25 decks, 496 slide chunks; every chunk keeps deck + slide number.
- Retrieval: BM25 (k1=1.5, b=0.75), top 10 chunks, max 4 per deck; topic-specific deck allow-lists (ethics restricted to deck 071). Fallback to all decks is recorded if fewer than 3 hits.
- Generation: Qwen cheap model via the existing OpenAI-compatible client with `enable_thinking=False`; Pydantic JSON schema; one call per question pair, with up to 3 retries after the initial attempt.
- Verification: quote must be a verbatim contiguous substring of the cited retrieved chunk (whitespace-normalised); ellipses rejected; exactly one marking point per mark; command word present; dependent (b) must refer back to (a); non-dependent siblings must use different angles; cross-generated duplicates rejected; fuzzy near-copy against all 35 papers rejected at SequenceMatcher >= 0.80.
- Every accepted theory answer is labelled `sourced`; each point carries deck + slide + chunk id.

### Results and cost

- Model: **qwen3.7-flash**; attempt limit: 4 (initial + up to 3 retries).
- Slots filled: **24/24** (23 theory sourced, 1 computed); accepted theory questions: **23** / 23 theory slots; placeholders left: **0**.
- Rejected slots in the final artifact: **0**; intermediate rejected attempts are listed below with reasons.
- Theory marks covered: **94**; marking points: **94**; every point has a verified quote.
- Calls: **60**; tokens: 122486 prompt + 36446 completion = 158932.
- Estimated cost: **$0.0106**; cost per accepted question: **$0.0005**.
- Cost basis: public qwen-flash list prices (input $0.022/M, output $0.216/M) used as a configurable estimate; this is not an invoice.

### Rejections and retries

The final pass made 28 group attempts for 12 question groups; 2 groups were accepted on the first attempt. Rejection categories in the retained attempt logs:

- point count != marks: 12
- quote too short: 9
- question length: 2
- quote not verbatim: 1

### Rejected attempts (examples from the retained logs)

| Question | Slots | Attempt | Rejected because |
|---|---|---:|---|
| A1 | A1a, A1b | 1 | A1b: 4 marking points for 6 marks (need exactly 6); A1b point 2: quote too short to verify |
| A1 | A1a, A1b | 2 | A1a: 4 marking points for 2 marks (need exactly 2); A1a point 2: quote too short to verify |
| A1 | A1a, A1b | 3 | A1b: 4 marking points for 6 marks (need exactly 6) |
| A10 | A10a, A10b | 1 | A10a point 2: quote is not verbatim in 023 - Access Control and Authorization slide 4 |
| A3 | A3a, A3b | 1 | A3b point 6: quote too short to verify |
| A3 | A3a, A3b | 2 | A3b: 3 marking points for 6 marks (need exactly 6) |
| A4 | A4a, A4b | 1 | A4b point 1: quote too short to verify |
| A4 | A4a, A4b | 2 | A4b point 4: quote too short to verify; A4b point 5: quote too short to verify |
| A4 | A4a, A4b | 3 | A4b point 5: quote too short to verify; A4b point 6: quote too short to verify |
| A5 | A5a, A5b | 1 | A5b: 3 marking points for 6 marks (need exactly 6) |
| A6 | A6a, A6b | 1 | A6b: 3 marking points for 6 marks (need exactly 6) |
| A6 | A6a, A6b | 2 | A6a: 4 marking points for 2 marks (need exactly 2) |
| A7 | A7a, A7b | 1 | A7b: 3 marking points for 6 marks (need exactly 6) |
| A8 | A8a, A8b | 1 | A8a: question too short (5 words); A8b: question too short (7 words) |
| B1 | B1a, B1b | 1 | B1a: 3 marking points for 5 marks (need exactly 5); B1b: 3 marking points for 5 marks (need exactly 5) |
| B2 | B2a, B2b | 1 | B2a: 2 marking points for 5 marks (need exactly 5); B2b: 2 marking points for 5 marks (need exactly 5) |

The first exploratory pass and the placeholder retries also rejected near-copies, ellipsis quotes, 10-character schema failures and duplicate sibling angles; those were fixed by the chunk-id cleanup, quote-length rule, sibling/duplicate checks and per-slot angle hints. No placeholder remains in the final paper.

### Attempts per question group

| Question | Slots | Attempts | Result | Top retrieval |
|---|---|---:|---|---|
| A1 | A1a, A1b | 4 | accepted | 061 - Network Security s4; 062 - Intrusion Detection System s8 |
| A10 | A10a, A10b | 2 | accepted | 024 - Formal Security Model s5; 023 - Access Control and Authorization s18 |
| A2 | A2a | 1 | accepted | 031 - Classical Cryptography s25; 031 - Classical Cryptography s26 |
| A3 | A3a, A3b | 3 | accepted | 073 - Trusted Computing s8; 073 - Trusted Computing s6 |
| A4 | A4a, A4b | 4 | accepted | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8 |
| A5 | A5a, A5b | 2 | accepted | 051 - Software Security s22; 051 - Software Security s23 |
| A6 | A6a, A6b | 3 | accepted | 011 - Introduction to Computer Security s10; 022 - Identification and Authentication s11 |
| A7 | A7a, A7b | 2 | accepted | 024 - Formal Security Model s5; 023 - Access Control and Authorization s18 |
| A8 | A8a, A8b | 2 | accepted | 011 - Introduction to Computer Security s10; 022 - Identification and Authentication s11 |
| A9 | A9a, A9b | 1 | accepted | 022 - Identification and Authentication s16; 022 - Identification and Authentication s19 |
| B1 | B1a, B1b | 2 | accepted | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s6 |
| B2 | B2a, B2b | 2 | accepted | 011 - Introduction to Computer Security s10; 022 - Identification and Authentication s11 |

### Low style-confidence slots

Exact style examples n<3: **10 slots** - A2a, A3b, A5a, A5b, A6a, A7b, B1a, B1b, B2a, B2b. These were widened in the order exact -> same topic/any command -> same command/any topic; every accepted question still has at least 3 style examples after widening and is marked `low_style_confidence` in the JSON and scheme.

### Source coverage

- 022 - Identification and Authentication: 16 marking points
- 051 - Software Security: 15 marking points
- 023 - Access Control and Authorization: 14 marking points
- 071 - Ethics and Computer Security: 10 marking points
- 073 - Trusted Computing: 8 marking points
- 062 - Intrusion Detection System: 6 marking points
- 041 - Windows Security: 6 marking points
- 072 - Biometrics and Authentication: 5 marking points
- 052 - Web Security: 5 marking points
- 061 - Network Security: 2 marking points
- 031 - Classical Cryptography: 2 marking points
- 011 - Introduction to Computer Security: 2 marking points
- 024 - Formal Security Model: 2 marking points
- 042 - Linux Security: 1 marking points

Near-copy maximum against the 35 past papers: **0.69** (threshold 0.80).

## 5. Paper and scheme QA

- Paper PDF: **4 pages**; scheme PDF: **13 pages**.
- Paper marks audit: 24 mark lines summing to 100 (Part A 80 + Part B 20).
- Paper headings: PART A (80 MARKS) and PART B (20 MARKS).
- Vigenere computed question: ciphertext `UMRBVVNWVPREQE`, key `CIPHER`, answer `SECURE LOGIN NOW`; the 26 x 26 tableau is printed immediately after Q2(b), titled `Vigenere tableau (A = 0)`.
- Scheme: 23 sourced theory answers + 1 computed answer + 0 placeholders; each theory point shows its quote, deck, slide and chunk id; low-style slots are flagged.
- Template checks: crest media `word/media/image1.jpeg` retained; header `CS/MOCK OCT 2026/CSC662` and footer `CONFIDENTIAL` / `Hak Cipta Universiti Teknologi MARA` retained in both paper and scheme.
- Tests: 112 pytest tests pass (`uv run pytest -q`), including planner invariants, theory quote verification, near-copy detection and dependent/sibling checks.

## 6. Caveats / still unverified

- The 2018 papers have no A/B labels, and 2025-07/2026-02 contain noisy extraction; measured rates use the 8 papers with explicit A/B labels (72 Part A pairs).
- Low style confidence: 10 slots lack 3 exact (topic+command+marks) examples; widening is recorded per slot.
- Some marking points quote short slide headings (e.g. `Operating System Independence`) rather than full sentences; the quote is still verbatim, but a human marker may want a fuller sentence.
- A6(b) is a password-threat question under the attacks/malware topic; it is an attack-on-authentication angle, sourced from deck 022 rather than the malware slides. The paper does not print topic labels; the scheme shows the sources.
- Playfair and affine remain older-style only and are not used in realistic mode; OTP remains unverified against the inconsistent slide 17 and is not used here.
- Cost is an estimate from public qwen-flash prices, not an account invoice; token counts are from the provider usage fields.

## 7. Generated files

- `outputs/mock_paper_02.docx` / `.pdf`
- `outputs/mock_scheme_02.docx` / `.pdf`
- `outputs/planner_revised_realistic.json` / `.md`
- `outputs/planner_measurements.json` / `.md`
- `outputs/theory_drafts_realistic.json` / `.md`
- `outputs/vigenere_tableau.png`
- `outputs/final_report.md` / `.pdf`
