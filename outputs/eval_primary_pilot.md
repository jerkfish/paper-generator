# Realistic-mode evaluation - seeds 1-20

Each seed runs the revised realistic planner and the full theory module (BM25 retrieval, cheap Qwen model, up to 3 retries, source overlap/topic/quote checks). Model and price settings are those in `src/config.py`; costs are estimates, not invoices.

- Models used: **deepseek-v4.1-flash-1017** (free-tier quotas rotated; per-seed model in the table).
- Seeds completed: **1/20**; failed: 
- Theory slots: 24; accepted **24**; placeholders **0**; placeholder rate **0.0%**.
- Source overlap: **0** keys across 0/20 papers; **0** slots involved; target 0.
- Max near-copy similarity against the 35 past papers: **0.70** (threshold 0.80).
- Calls: 77; tokens: 205215; estimated total cost: **$0.0734**; cost per accepted question: **$0.0031**.
- Scenario questions generated: **2** Part B slots.
- Low term-overlap marking points flagged: **15**.

## Computed-marks distribution vs fingerprint

| Computed marks | Fingerprint count | Eval count |
|---:|---:|---:|
| 0 | 5 | 1 |
| 2 | 1 | 0 |
| 6 | 2 | 0 |
| 12 | 1 | 0 |
| 14 | 1 | 0 |

Fingerprint distribution: `[0, 0, 0, 0, 0, 2, 6, 6, 12, 14]`; eval mean **0.00** marks/paper (fingerprint mean 4.0).

## Per-seed results

| Seed | Model | Computed | Placeholders | Attempts avg | Attempts max | Overlap keys | Overlap rate | Max near-copy | Part B scenarios | Cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | deepseek-v4.1-flash-1017 | 0 | 0 | 1.33 | 2 | 0 | 0.0% | 0.70 | 2 | $0.0734 |

Attempts are per question group (12 groups per paper); a group contains one slot or an (a)/(b) pair.

## Topic mix: planned vs actual (marks summed over 20 seeds)

| Topic | Planned marks | Planned % | Actual marks | Actual % |
|---|---:|---:|---:|---:|
| access control models | 18 | 18.0% | 18 | 18.0% |
| attacks/malware | 24 | 24.0% | 24 | 24.0% |
| authentication/biometrics | 16 | 16.0% | 16 | 16.0% |
| network security | 8 | 8.0% | 8 | 8.0% |
| risk/management (ethics) | 18 | 18.0% | 18 | 18.0% |
| software/OS security | 8 | 8.0% | 8 | 8.0% |
| trusted computing/blockchain | 8 | 8.0% | 8 | 8.0% |

Actual topic mix is inferred from the cited decks (majority deck topic per accepted question; ties fall back to the slot topic).

## Placeholder slots by seed

- none

## Top 10 accepted/past question pairs by fuzzy similarity

| # | Seed / slot | Ratio | Generated question | Nearest real past question |
|---:|---|---:|---|---|
| 1 | 1 / A8a | 0.696 | Explain the difference between morals, ethics and laws as they apply to professional conduct in computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| 2 | 1 / A6b | 0.685 | Describe the two primary system components of the Next Generation Secure Computing Base (NGSCB) and the role of each component in the trusted platform. | CSC662-2023-07 QA8b: List and explain the two primary system components of Next Generation Secure Computing Base(NGSCB). (6 marks) |
| 3 | 1 / A1a | 0.581 | State TWO (2) reasons why software is insecure, with particular reference to buffer overflows. | CSC662-2025-02 QA1a: State TWO (2) reasons why physical security is needed. |
| 4 | 1 / A10a | 0.529 | State two ways in which an intrusion detection system supports the detection and defence of a system against attacks. | CSC662-2018-06 Q14a: How do intrusion detection system (IDS) and intrusion detection and prevention systems (IDPS) differ between one another? |
| 5 | 1 / A7a | 0.529 | List the stages involved in the biometric authentication process, distinguishing between the identification stage and the authentication stage. | CSC662-2019-12 QA3a: What is the difference between identification and authentication? |
| 6 | 1 / A9a | 0.521 | Explain two password security controls that can be applied to password files and user accounts to reduce the risk of password-based attacks. | CSC662-2010-10 Q15b: Explain TWO (2) methods that can be used to defend against the attacks. |
| 7 | 1 / A4a | 0.520 | State TWO (2) typical locations where IDS sensors are placed in a network-based IDS architecture. | CSC662-2017-07 Q5c: Elaborate TWO (2) types of Intrusion Detection System (IDS) are Network-based (NIDS) and Host-Based (HIDS). |
| 8 | 1 / A3a | 0.493 | Explain how spyware and adware differ in the harm they cause, referring to the impact on confidentiality, integrity and availability. | CSC662-2013-01 Q7: Describe with example how the computer security objectives of confidentiality, integrity and availability relate to database management system. |
| 9 | 1 / A4b | 0.492 | Explain THREE (3) preventive network security mechanisms that an organization can deploy to protect its network, describing the protective role of each mechanism. | CSC662-2011-04 Q11: Describe THREE (3) reasons why organization, which has a network, will faces more security issues than any organization without networking. |
| 10 | 1 / A2a | 0.478 | Explain two characteristics of Trojan horses as a type of malware, including how they present themselves and what harm they can cause. | CSC662-2008-10 Q2a: Explain THREE (3) characteristics of a good password. Give ONE (1) example of good password that you think is secure. |

## Low-overlap points remaining after point retries

Each low-overlap point is regenerated up to **2 times**; if it is still below the threshold it remains flagged for human review.

| # | Seed / slot | Overlap | Point | Quote |
|---:|---|---:|---|---|
| 1 | 1 / A1b | 0.44 | Windows subjects are processes and threads, and security credentials for a subject are stored in a token. | Windows subjects are processes and threads. |
| 2 | 1 / A1b | 0.46 | Windows Vista (2007) introduced security milestones such as no “admin-by-default”, firewall, and DEP. | Vista (2007): no "admin-by-default", ﬁrewall, DEP |
| 3 | 1 / A2b | 0.43 | A COM-file virus appends its virus body to the host program. | Append a virus body to a program |
| 4 | 1 / A3a | 0.33 | Spyware harms confidentiality by stealing user logins and passwords and logging keystrokes, compromising sensitive information. | They steal user logins and passwords, document sites visited, log keystrokes and even redirect browsers to unwanted sites. |
| 5 | 1 / A5b | 0.25 | The access control matrix suffers from poor scalability and poor handling of changes. | poor scalability |
| 6 | 1 / A5b | 0.29 | Access control structures must satisfy requirements including an ability to express control policies, verifiability of correctness, and scalability and manageability. | an ability to express control policies |
| 7 | 1 / A6b | 0.38 | Nexus authenticates trusted programs and provides the application interface to the TPM. | Authenticates trusted programs |
| 8 | 1 / A8b | 0.33 | The professional should respect privacy and honour confidentiality. | Respect privacy. |
| 9 | 1 / B2a | 0.33 | A professional code of ethics, such as the ACM code, sets out expectations of ethical and professional conduct that should shape how technology is developed and released. | Association of Computing Machinery ACM (founded 1947) has a code of ethics and professional conduct. |
| 10 | 1 / B2a | 0.29 | Technology professionals can draw on professional bodies such as AITP for education and information on relevant IT issues when judging the ethical impact of their work. | provides quality IT-related education, information on relevant IT issues, and forums for networking with experienced peers and other IT professionals. |

## Attempts and scenario sampling

- Limit: **4 attempts per slot** (1 initial + 3 retries). A group attempt count is the **maximum** across its slots, so it cannot exceed 4. Earlier reports summed attempts across (a) and (b), which is why values above 4 appeared; that was a counting bug, not a higher limit.
- Point-level low-overlap retries are separate: **49** extra calls across the evaluation (max 2 per low point).
- Part B scenario sampling rate used: **1** sampled questions across 2 Part B questions; measured rate 7/19 = 36.8% (lower bound). Generated scenario slots: 2.

## Topic/deck map

| Topic | Allowed decks |
|---|---|
| attacks/malware | 011, 022, 041, 042, 051, 052, 061, 062 |
| authentication/biometrics | 022, 023, 041, 042, 072 |
| access control models | 023, 024, 041, 042, 073 |
| trusted computing/blockchain | 038, 073, 074, 074B |
| software/OS security | 041, 042, 051, 052 |
| network security | 052, 061, 062 |
| risk/management (ethics) | 071 |
| classical ciphers | 031 |

Decks **051** and **052** are allowed for both `attacks/malware` and `software/OS security`. Actual topic mix is now accepted marks by the planner's slot topic, plus a pass/fail allowed-deck check; the old majority-deck mix is kept only as a diagnostic in the per-seed JSON.

## Near-copy threshold 0.70

- 0.70 run pending.

## Reading the metrics

- Computed marks are sampled from the clean-modern fingerprint; the eval count should approximate the fingerprint distribution.
- Placeholder rate counts theory slots left unresolved after the attempt limit.
- Source overlap is the number of (deck, slide) keys cited by more than one accepted question; target is 0. A non-zero value is only allowed when retrieval had fewer than three unused chunks and is listed in the per-seed theory JSON.
- Max near-copy is the maximum SequenceMatcher ratio of an accepted question against any of the 35 past papers; the verifier rejects at 0.80.
- Actual topic mix is inferred from cited decks, so it can differ from the planner's slot topics when a question cites a deck that serves more than one topic.
- Multiple Qwen models were used because the free-tier quota was exhausted during the 20-seed run; the per-seed model is shown. The cost column uses the configurable qwen-flash list-price estimate, not per-model invoices.
