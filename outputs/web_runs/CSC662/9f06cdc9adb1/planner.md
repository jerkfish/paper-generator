# Planner slot table - revised

- mode: **realistic**; style: **modern**; seed: 2488
- computed marks: **2**; clean-modern distribution: [0, 0, 0, 0, 0, 2, 6, 6, 12, 14] (mean 4.0)
- clean modern papers: 10

## Measurements used

- Part A pairs: 72 across 8 papers; same topic 55/72 (76.4%); dependent (b) 7/72 (9.7%).
- Part A command-word rows/marks: Explain 56, State 31, Justify 1, Describe 16, Other 7, Discuss 14, List 12, Analyse 3, Propose 3, Compare 3.
- Part B command-word rows/marks: State 7, Explain 13, Discuss 3, Other 11, Propose 5, Describe 2, Analyse 2.
- Part B scenario stems: 7/19; same-topic pairs: 11/19; dependent b: 2/19. Part B topics are sampled by their measured marks weights.

## Slots

| Slot | Q | Marks | Kind | Topic | Command | Computed type | Target size / key | Exact style n | Used style n | Style mode | Low conf. | Dependent | Notes |
|---|---|---:|---|---|---|---|---|---:|---:|---|---|---|---|
| A1a | A1 | 2 | computed | classical ciphers | compute | Caesar | 11-15 letters; shift 7 |  |  |  |  |  | computed slot |
| A1b | A1 | 6 | theory | classical ciphers | Compare |  |  | 0 | 5 | topic+marks (any command) | yes |  | style n=0; widened to topic+marks (any command); low style confidence |
| A2a | A2 | 2 | theory | risk/management (ethics) | Explain |  |  | 8 | 5 | exact |  |  | style n=8 |
| A2b | A2 | 6 | theory | risk/management (ethics) | Discuss |  |  | 4 | 4 | exact |  |  | style n=4 |
| A3a | A3 | 2 | theory | network security | State |  |  | 2 | 5 | topic+marks (any command) | yes |  | style n=2; widened to topic+marks (any command); low style confidence |
| A3b | A3 | 6 | theory | network security | Discuss |  |  | 1 | 5 | topic+marks (any command) | yes |  | style n=1; widened to topic+marks (any command); low style confidence |
| A4a | A4 | 2 | theory | attacks/malware | State |  |  | 6 | 5 | exact |  |  | style n=6 |
| A4b | A4 | 6 | theory | attacks/malware | State |  |  | 5 | 5 | exact |  |  | style n=5 |
| A5a | A5 | 2 | theory | trusted computing/blockchain | Explain |  |  | 8 | 5 | exact |  |  | style n=8 |
| A5b | A5 | 6 | theory | trusted computing/blockchain | Explain |  |  | 3 | 3 | exact |  |  | style n=3 |
| A6a | A6 | 2 | theory | software/OS security | List |  |  | 3 | 3 | exact |  | yes | style n=3; dependent pair |
| A6b | A6 | 6 | theory | software/OS security | Discuss |  |  | 0 | 5 | topic+marks (any command) | yes | yes | style n=0; widened to topic+marks (any command); low style confidence; dependent pair |
| A7a | A7 | 2 | theory | attacks/malware | Explain |  |  | 28 | 5 | exact |  |  | style n=28 |
| A7b | A7 | 6 | theory | attacks/malware | Describe |  |  | 12 | 5 | exact |  |  | style n=12 |
| A8a | A8 | 2 | theory | attacks/malware | Explain |  |  | 28 | 5 | exact |  |  | style n=28 |
| A8b | A8 | 6 | theory | attacks/malware | Explain |  |  | 12 | 5 | exact |  |  | style n=12 |
| A9a | A9 | 2 | theory | authentication/biometrics | List |  |  | 5 | 5 | exact |  |  | style n=5 |
| A9b | A9 | 6 | theory | authentication/biometrics | Describe |  |  | 6 | 5 | exact |  |  | style n=6 |
| A10a | A10 | 2 | theory | access control models | State |  |  | 4 | 4 | exact |  |  | style n=4 |
| A10b | A10 | 6 | theory | access control models | Explain |  |  | 4 | 4 | exact |  |  | style n=4 |
| B1a | B1 | 5 | theory | risk/management (ethics) | Discuss |  |  | 0 | 5 | topic+marks (any command) | yes |  | style n=0; widened to topic+marks (any command); low style confidence |
| B1b | B1 | 5 | theory | risk/management (ethics) | Explain |  |  | 2 | 5 | topic+marks (any command) | yes |  | style n=2; widened to topic+marks (any command); low style confidence |
| B2a | B2 | 5 | theory | authentication/biometrics | Explain |  |  | 1 | 5 | topic+marks (any command) | yes |  | style n=1; widened to topic+marks (any command); low style confidence |
| B2b | B2 | 5 | theory | authentication/biometrics | State |  |  | 1 | 5 | topic+marks (any command) | yes |  | style n=1; widened to topic+marks (any command); low style confidence |

## Topic allocation

| Topic | Modern weight | Target marks | Assigned theory marks |
|---|---:|---:|---:|
| attacks/malware | 0.290 | 27 | 24 |
| authentication/biometrics | 0.189 | 17 | 18 |
| access control models | 0.147 | 14 | 8 |
| trusted computing/blockchain | 0.096 | 9 | 8 |
| software/OS security | 0.058 | 5 | 8 |
| network security | 0.068 | 6 | 8 |
| risk/management (ethics) | 0.152 | 14 | 18 |

Question topic sequence (A1..A10, B1, B2): A1:classical ciphers -> A2:risk/management (ethics) -> A3:network security -> A4:attacks/malware -> A5:trusted computing/blockchain -> A6:software/OS security -> A7:attacks/malware -> A8:attacks/malware -> A9:authentication/biometrics -> A10:access control models -> B1:risk/management (ethics) -> B2:authentication/biometrics
Max two consecutive same-topic questions: **PASS**.
Dependent question(s): A6.

## Part B measured task distribution (used for B slots)

| Command | Rows | Marks |
|---|---:|---:|
| State | 7 | 35 |
| List | 0 | 0 |
| Explain | 13 | 54 |
| Describe | 2 | 8 |
| Discuss | 3 | 16 |
| Compare | 0 | 0 |
| Justify | 0 | 0 |
| Propose | 5 | 28 |
| Analyse | 2 | 11 |

## Three real 6-mark examples per command label used at 6 marks

### Compare

- **CSC662-2015-06 Q15**: Differentiate between Morals, Ethics and Laws in computer security. (6 marks)
- **CSC662-2018-01 Q8a**: With the help of diagram, differentiate between Simple Security Property and Star Property. (6 marks)
- **CSC662-2018-12 QA7b**: Differentiate between steganography and cryptography in terms of: , capacity, type of message and type of application.

### Describe

- **CSC662-2006-10 Q1a**: Describe the difference between vulnerability, threat and control, by using one example.
- **CSC662-2007-04 Q1a**: Define the following terms:
i) Firewall
ii) Integrity
iii) Vulnerability
- **CSC662-2007-04 Q2b**: Describe the term malicious code and explain TWO (2) examples of them.

### Discuss

- **CSC662-2010-04 Q11**: Discuss THREE (3) approaches that can be used to create good passwords. 
(6 marks)
- **CSC662-2010-10 Q3b**: Discuss THREE (3) important characteristics of 'economically feasible" security.
- **CSC662-2012-06 Q15**: Software security is a system-wide issue that involves both building in security mechanisms and designing the system to be robust. Discuss the following software security mechanism:
a) Data execution protection
b) Address space layout randomization
c) Canary

### Explain

- **CSC662-2007-04 Q6b**: "It's time we became proactive about stopping computer crime. No matter how good we get at hardening systems; how many bucks we spend on defensive measures or in complying with legislation and initiatives; no matter how carefully we design, create, deploy and maintain secure operating systems, applications and infrastructure; others are spending even more money and time attacking them."
http:/Awww. crime-research, org
Briefly explain THREE (3) ways on how to stop computer crime.
- **CSC662-2007-10 Q1a**: Explain how three goals of computer security relate with each other in building a secure system.
- **CSC662-2008-10 Q2b**: Recently, there are many types of malware infection had been reported to the security organization. Explain the characteristics of THREE (3) types of malware that you know.

### State

- **CSC662-2009-04 Q1d**: Determine whether the P-box with the following tables is a straight P-box, a compression P-box or an expansion P-box. State one reason for each table. 
i) 
ii) 
iii) 
112 3 44 
15 3 6 78 
2 14 3 56
- **CSC662-2010-10 Q4a**: Identify which requirements or components that deal with confidentiality, integrity and 
availability concerns in proposed e-voting system.
- **CSC662-2010-10 Q11b**: Assuming that high > low, identify program fragments that are desired (allowed) or 
undesired (prevented) in information security flows for reading operation.

## Style widening and low-confidence slots

Slots with exact style n < 3: A1b, A3a, A3b, A6b, B1a, B1b, B2a, B2b.
Widening order: exact -> same topic/any command -> same command/any topic; all are recorded in the slot table.

## Coverage notes

- Seven theory topics cover 782/955 modern non-compute marks; 173 marks (18.1%) fall outside the seven topics and are reported, not reallocated: other 64, general cryptography 30, classical ciphers 29, public-key 25, hashing/signatures 18, block ciphers 7.
- risk/management (ethics) weight is the modern risk/management marks (119) renormalised with the other six topics; source deck: KB folder 'CSC662', deck 071 Ethics.
- A theory slot paired with a computed slot inherits the computed topic (classical ciphers or access control models) because (a) and (b) must share one topic; this mark is outside the seven-topic target and is shown separately.
- 2018-01 and 2018-06 have no A/B labels and are excluded from the pair/part measures; 2025-07 has incomplete A/B extraction.

## Calibration used for computed sizes

| Type | Marks | n | Length range | Key | Working steps | Note |
|---|---:|---:|---|---|---|---|
| caesar | 2 | 1 | not printed (word) | shift 4 | word length | n=1 at 2m; widened 2-6m gives n=4, lengths 11-24 |
| caesar | 6 | 2 | 11-38 | shift 7/18 | 11-38 mappings | n=2 at 6m; widened 4-6m gives n=3, lengths 11-38 |
| vigenere | 6 | 1 | 13 | table/keyword | 13 table lookups | n=1 at 6m; widened 3-10m gives n=3, lengths 13-18 |
| columnar_3x4 | 2-6 | 3 | 21-30 | 4-5 columns / keyword | columns + rows | slide 3x4 demo is 12 cells; real examples are 21-30 letters |
| columnar_keyword | 6 | 1 | 21-30 | keyword (4-6 letters) | columns + rows | n=1 at 6m; widened 2-6m gives n=3 |
| rail_fence | 6 | 3 | 21-34 | 3-4 rails | zigzag rows + read | n=3 at 6m (2012, 2013, 2018) |
| otp | 6 | 1 | 12-13 | 12 key numbers/letters | 12 modular additions | n=1 at 6m; widened 5-6m gives n=2; still thin, keep lengths 12-13. 26-letter alphabet is verified against DEC 2019; slide 17 is inconsistent |
| acm | 6 | 1 | 4 users x 3 objects | matrix only | 12 matrix cells | 6m = matrix only; 9m = matrix + ACL + CL (2015-06, 2016-12) |
| playfair | 6 | 1 | 10 | key REDFOX (6) | 5 pairs | older style only; no current lecture slide |
| affine | 6 | 1 | 13 | key (17,20) | 13 inverse operations | older style only; no current lecture slide |

ACM rule: 6 marks = matrix only; about 9 marks = matrix + ACL + CL. Playfair and affine are never used in realistic mode. Vigenere questions print the 26 x 26 tableau (2006-10 Q2d, 2017-07 Q10 style).