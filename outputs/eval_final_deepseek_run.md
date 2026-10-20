# Realistic-mode evaluation - seeds 1-20

Each seed runs the revised realistic planner and the full theory module (BM25 retrieval, configured model, up to 3 retries, source overlap/topic/quote checks, stemmed-overlap + entailment gates). Model and price settings are those in `src/config.py`; costs are estimates, not invoices.

- Model used: **deepseek-flash** (one model for all seeds).
- Seeds completed: **20/20**
- Theory slots: 464; accepted **457**; placeholders **7**; placeholder rate **1.5%**.
- Source overlap: **0** keys across 0/20 papers; **0** slots involved; target 0.
- Max near-copy similarity against the 35 past papers: **0.76** (threshold 0.80).
- Calls: 1358; tokens: 2632459; estimated total cost: **$1.0315**; cost per accepted question: **$0.0023**.
- Scenario questions generated: **32** Part B slots.
- Low stem-overlap marking points remaining: **628**.

## Computed-marks distribution vs fingerprint

| Computed marks | Fingerprint count | Eval count |
|---:|---:|---:|
| 0 | 5 | 11 |
| 2 | 1 | 2 |
| 6 | 2 | 3 |
| 12 | 1 | 1 |
| 14 | 1 | 3 |

Fingerprint distribution: `[0, 0, 0, 0, 0, 2, 6, 6, 12, 14]`; eval mean **3.80** marks/paper (fingerprint mean 4.0).

## Per-seed results

| Seed | Model | Computed | Placeholders | Attempts avg | Attempts max | Overlap keys | Overlap rate | Max near-copy | Part B scenarios | Point retries | Low overlap | Cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | deepseek-flash | 0 | 0 | 1.92 | 4 | 0 | 0.0% | 0.66 | 2 | 36 | 30.0% | $0.0584 |
| 2 | deepseek-flash | 0 | 1 | 1.75 | 4 | 0 | 0.0% | 0.55 | 2 | 36 | 34.7% | $0.0547 |
| 3 | deepseek-flash | 0 | 0 | 2.00 | 3 | 0 | 0.0% | 0.62 | 0 | 30 | 26.0% | $0.0569 |
| 4 | deepseek-flash | 0 | 0 | 1.67 | 3 | 0 | 0.0% | 0.61 | 2 | 37 | 35.0% | $0.0502 |
| 5 | deepseek-flash | 14 | 0 | 1.67 | 4 | 0 | 0.0% | 0.61 | 2 | 28 | 32.6% | $0.0441 |
| 6 | deepseek-flash | 14 | 2 | 2.00 | 4 | 0 | 0.0% | 0.65 | 4 | 25 | 29.5% | $0.0518 |
| 7 | deepseek-flash | 2 | 0 | 1.58 | 3 | 0 | 0.0% | 0.71 | 4 | 43 | 41.8% | $0.0481 |
| 8 | deepseek-flash | 0 | 0 | 1.50 | 3 | 0 | 0.0% | 0.57 | 2 | 32 | 28.0% | $0.0478 |
| 9 | deepseek-flash | 6 | 0 | 1.58 | 2 | 0 | 0.0% | 0.66 | 0 | 36 | 36.2% | $0.0442 |
| 10 | deepseek-flash | 14 | 2 | 2.00 | 4 | 0 | 0.0% | 0.58 | 2 | 16 | 20.5% | $0.0484 |
| 11 | deepseek-flash | 6 | 0 | 1.50 | 2 | 0 | 0.0% | 0.68 | 0 | 38 | 36.2% | $0.0459 |
| 12 | deepseek-flash | 6 | 0 | 2.00 | 4 | 0 | 0.0% | 0.61 | 4 | 40 | 38.3% | $0.0555 |
| 13 | deepseek-flash | 0 | 2 | 1.67 | 4 | 0 | 0.0% | 0.56 | 0 | 36 | 35.6% | $0.0488 |
| 14 | deepseek-flash | 0 | 0 | 2.00 | 3 | 0 | 0.0% | 0.67 | 4 | 47 | 39.0% | $0.0587 |
| 15 | deepseek-flash | 0 | 0 | 1.92 | 3 | 0 | 0.0% | 0.61 | 0 | 37 | 33.0% | $0.0560 |
| 16 | deepseek-flash | 2 | 0 | 1.92 | 3 | 0 | 0.0% | 0.76 | 0 | 31 | 29.6% | $0.0520 |
| 17 | deepseek-flash | 12 | 0 | 1.92 | 3 | 0 | 0.0% | 0.57 | 2 | 38 | 40.9% | $0.0527 |
| 18 | deepseek-flash | 0 | 0 | 1.92 | 4 | 0 | 0.0% | 0.63 | 0 | 36 | 32.0% | $0.0559 |
| 19 | deepseek-flash | 0 | 0 | 1.58 | 2 | 0 | 0.0% | 0.54 | 0 | 35 | 33.0% | $0.0511 |
| 20 | deepseek-flash | 0 | 0 | 1.67 | 3 | 0 | 0.0% | 0.64 | 2 | 33 | 29.0% | $0.0502 |

Attempts are per question group (12 groups per paper); a group contains one slot or an (a)/(b) pair.

## Topic mix: planned vs actual (marks summed over 20 seeds)

| Topic | Planned marks | Planned % | Actual marks | Actual % |
|---|---:|---:|---:|---:|
| access control models | 282 | 15.0% | 280 | 14.8% |
| attacks/malware | 466 | 24.8% | 462 | 24.4% |
| authentication/biometrics | 340 | 18.1% | 340 | 17.9% |
| classical ciphers | 0 | 0.0% | 38 | 2.0% |
| network security | 162 | 8.6% | 162 | 8.5% |
| risk/management (ethics) | 296 | 15.7% | 286 | 15.1% |
| software/OS security | 164 | 8.7% | 158 | 8.3% |
| trusted computing/blockchain | 170 | 9.0% | 170 | 9.0% |

Actual topic mix is accepted marks by the planner's slot topic; the majority-deck mix is retained only as a JSON diagnostic.

## Placeholder slots by seed

- seed 2: A6a
- seed 6: A1b, A9a
- seed 10: A7b, A8a
- seed 13: B2a, B2b

## Top 10 accepted/past question pairs by fuzzy similarity

| # | Seed / slot | Ratio | Generated question | Nearest real past question |
|---:|---|---:|---|---|
| 1 | 1 / A8a | 0.792 | Explain the difference between morals, ethics, and laws in the context of computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| 2 | 7 / A6a | 0.788 | Explain the differences between morals, ethics, and laws. | CSC662-2007-04 Q1b: Explain the differences between worm and virus. |
| 3 | 3 / A1a | 0.787 | Explain the differences between morals, ethics, and laws in the context of computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| 4 | 8 / A2a | 0.787 | Explain the differences between morals, ethics, and laws in the context of computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| 5 | 1 / A6b | 0.757 | Describe the two primary system components of the Next Generation Secure Computing Base (NGSCB) and the key functions of each. | CSC662-2023-07 QA8b: List and explain the two primary system components of Next Generation Secure Computing Base(NGSCB). (6 marks) |
| 6 | 8 / A4b | 0.727 | Describe the two primary system components of the Next Generation Secure Computing Base (NGSCB), including the functionality of each. | CSC662-2023-07 QA8b: List and explain the two primary system components of Next Generation Secure Computing Base(NGSCB). (6 marks) |
| 7 | 6 / A5a | 0.718 | List TWO (2) distinct stages in the biometric authentication process as described in the lecture. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 8 | 5 / A10b | 0.716 | Explain six preventive network security mechanisms, including a firewall, a proxy server, network segmentation, remote access VPN, IDS/IPS, and data loss prevention, and describe how each protects an organization's network. | CSC662-2025-02 QA6b: Explain 3 preventive network security mechanisms, including a firewall, a proxy server, and network segmentation, that can be implemented to enhance the company's security posture. In your answer, describe how each mechanism protects an organization's network. |
| 9 | 5 / A6a | 0.690 | List two types of malware and describe their characteristics. | CSC662-2006-10 Q3a: List SEVEN (7) types of malicious code and explain each of their characteristics. |
| 10 | 5 / A3a | 0.686 | Explain the stages involved in biometric identification and authentication. | CSC662-2019-12 QA3a: What is the difference between identification and authentication? |

## Low-overlap points remaining after point retries

Each low-overlap point is regenerated up to **2 times**; if it is still below the threshold it remains flagged for human review.

| # | Seed / slot | Overlap | Point | Quote |
|---:|---|---:|---|---|
| 1 | 1 / A2a | 0.44 | Spyware steal user logins and passwords and can result in identity theft. | They steal user logins and passwords, document sites visited, log keystrokes and even redirect browsers to unwanted sites. |
| 2 | 1 / A2b | 0.11 | Malware can propagate by appending its body to an executable and redirecting the entry point. | Append a virus body to a program |
| 3 | 1 / A2b | 0.33 | Malware can exploit remote execution features, as the Morris worm did with sendmail. | Used a debugging feature of sendmail (remote execution) |
| 4 | 1 / A2b | 0.17 | Web-based malware can propagate by injecting JavaScript into a user profile and infecting visitors. | Any user who visits an infected user's page will gets proﬁle infected with Javascript and his friends list infected with Samy |
| 5 | 1 / A3a | 0.39 | Malware can impact confidentiality by disclosing information to unauthorized parties, such as through snooping, sniffing, or wiretapping. | Disclosure - unauthorized access to information snooping, sniffing, wiretapping |
| 6 | 1 / A3a | 0.33 | Malware can impact integrity by altering data maliciously, as described in the CIA triad. | Integrity: data has not been (maliciously) altered |
| 7 | 1 / A3b | 0.33 | The attack was a form of script injection, a type of software threat. | Script injection (e.g. XSS) |
| 8 | 1 / A5b | 0.31 | ACM is a basic control structure with clarity of definition and easy verification, but poor scalability and poor handling of changes. | ACM is a basic control structure. |
| 9 | 1 / A6b | 0.20 | The two primary system components are Nexus and Nexus Computing Agent (NCA). | Two primary system components |
| 10 | 1 / A7b | 0.40 | Behavioural biometrics include voice recognition. | Behavioural: Voice, Typing pattern, Signature |

## Attempts and scenario sampling

- Limit: **4 attempts per slot** (1 initial + 3 retries). A group attempt count is the **maximum** across its slots, so it cannot exceed 4. Earlier reports summed attempts across (a) and (b), which is why values above 4 appeared; that was a counting bug, not a higher limit.
- Point-level low-overlap retries are separate: **690** extra calls across the evaluation (max 2 per low point).
- Part B scenario sampling rate used: **16** sampled questions across 40 Part B questions; measured rate 7/19 = 36.8% (lower bound). Generated scenario slots: 32.

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
- Actual topic mix is accepted marks by the planner's slot topic; the allowed-deck check is reported separately.
- Multiple Qwen models were used because the free-tier quota was exhausted during the 20-seed run; the per-seed model is shown. The cost column uses the configurable qwen-flash list-price estimate, not per-model invoices.
