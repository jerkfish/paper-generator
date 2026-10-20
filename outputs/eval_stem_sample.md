# Realistic-mode evaluation - seeds 1-20

Each seed runs the revised realistic planner and the full theory module (BM25 retrieval, configured model, up to 3 retries, source overlap/topic/quote checks, stemmed-overlap + entailment gates). Model and price settings are those in `src/config.py`; costs are estimates, not invoices.

- Model used: **deepseek-flash** (one model for all seeds).
- Seeds completed: **8/20**; failed: 
- Theory slots: 185; accepted **181**; placeholders **4**; placeholder rate **2.2%**.
- Source overlap: **0** keys across 0/20 papers; **0** slots involved; target 0.
- Max near-copy similarity against the 35 past papers: **0.79** (threshold 0.80).
- Calls: 484; tokens: 897524; estimated total cost: **$0.3478**; cost per accepted question: **$0.0019**.
- Scenario questions generated: **16** Part B slots.
- Low stem-overlap marking points remaining: **246**.

## Computed-marks distribution vs fingerprint

| Computed marks | Fingerprint count | Eval count |
|---:|---:|---:|
| 0 | 5 | 5 |
| 2 | 1 | 1 |
| 6 | 2 | 0 |
| 12 | 1 | 0 |
| 14 | 1 | 2 |

Fingerprint distribution: `[0, 0, 0, 0, 0, 2, 6, 6, 12, 14]`; eval mean **3.75** marks/paper (fingerprint mean 4.0).

## Per-seed results

| Seed | Model | Computed | Placeholders | Attempts avg | Attempts max | Overlap keys | Overlap rate | Max near-copy | Part B scenarios | Point retries | Low overlap | Cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | deepseek-flash | 0 | 1 | 1.42 | 4 | 0 | 0.0% | 0.79 | 2 | 28 | 27.7% | $0.0452 |
| 2 | deepseek-flash | 0 | 1 | 1.50 | 4 | 0 | 0.0% | 0.74 | 2 | 29 | 28.7% | $0.0476 |
| 3 | deepseek-flash | 0 | 0 | 1.50 | 2 | 0 | 0.0% | 0.78 | 0 | 39 | 33.0% | $0.0490 |
| 4 | deepseek-flash | 0 | 0 | 1.50 | 4 | 0 | 0.0% | 0.74 | 2 | 39 | 39.0% | $0.0445 |
| 5 | deepseek-flash | 14 | 2 | 1.67 | 4 | 0 | 0.0% | 0.74 | 0 | 21 | 27.6% | $0.0416 |
| 6 | deepseek-flash | 14 | 0 | 1.08 | 2 | 0 | 0.0% | 0.79 | 4 | 24 | 27.9% | $0.0339 |
| 7 | deepseek-flash | 2 | 0 | 1.25 | 2 | 0 | 0.0% | 0.78 | 4 | 29 | 29.6% | $0.0384 |
| 8 | deepseek-flash | 0 | 0 | 1.50 | 2 | 0 | 0.0% | 0.78 | 2 | 49 | 47.0% | $0.0476 |

Attempts are per question group (12 groups per paper); a group contains one slot or an (a)/(b) pair.

## Topic mix: planned vs actual (marks summed over 20 seeds)

| Topic | Planned marks | Planned % | Actual marks | Actual % |
|---|---:|---:|---:|---:|
| access control models | 118 | 15.8% | 102 | 13.6% |
| attacks/malware | 180 | 24.1% | 180 | 24.1% |
| authentication/biometrics | 136 | 18.2% | 136 | 18.2% |
| classical ciphers | 0 | 0.0% | 22 | 2.9% |
| network security | 66 | 8.8% | 66 | 8.8% |
| risk/management (ethics) | 118 | 15.8% | 118 | 15.8% |
| software/OS security | 64 | 8.6% | 58 | 7.8% |
| trusted computing/blockchain | 66 | 8.8% | 66 | 8.8% |

Actual topic mix is accepted marks by the planner's slot topic; the majority-deck mix is retained only as a JSON diagnostic.

## Placeholder slots by seed

- seed 1: A1b
- seed 2: A9b
- seed 5: B2a, B2b

## Top 10 accepted/past question pairs by fuzzy similarity

| # | Seed / slot | Ratio | Generated question | Nearest real past question |
|---:|---|---:|---|---|
| 1 | 1 / A7a | 0.790 | List TWO (2) stages of the biometric authentication process. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 2 | 6 / A5a | 0.790 | List TWO (2) stages of the biometric authentication process. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 3 | 1 / A8a | 0.784 | Explain the difference between morals, ethics and laws. | CSC662-2007-04 Q1b: Explain the differences between worm and virus. |
| 4 | 3 / A1a | 0.784 | Explain the difference between morals, ethics and laws. | CSC662-2007-04 Q1b: Explain the differences between worm and virus. |
| 5 | 7 / A6a | 0.784 | Explain the difference between morals, ethics and laws. | CSC662-2007-04 Q1b: Explain the differences between worm and virus. |
| 6 | 8 / A2a | 0.784 | Explain the difference between morals, ethics and laws. | CSC662-2007-04 Q1b: Explain the differences between worm and virus. |
| 7 | 3 / A4a | 0.764 | List the TWO (2) stages of the biometric authentication process. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 8 | 2 / A3a | 0.741 | State TWO (2) differences between morals and laws. | CSC662-2011-04 Q9: Describe TWO (2) differences between copyright and patent. |
| 9 | 4 / A2a | 0.741 | State TWO (2) differences between morals and laws. | CSC662-2011-04 Q9: Describe TWO (2) differences between copyright and patent. |
| 10 | 5 / A9a | 0.741 | State TWO (2) differences between morals and laws. | CSC662-2011-04 Q9: Describe TWO (2) differences between copyright and patent. |

## Low-overlap points remaining after point retries

Each low-overlap point is regenerated up to **2 times**; if it is still below the threshold it remains flagged for human review.

| # | Seed / slot | Overlap | Point | Quote |
|---:|---|---:|---|---|
| 1 | 1 / A10a | 0.43 | State transition analysis cannot detect denial of service attacks. | They can't detect denail of service attacks. |
| 2 | 1 / A10b | 0.43 | An IDS countermeasure identifies and halts attacks that are currently in progress. | Identifies and stops attacks in progress |
| 3 | 1 / A10b | 0.33 | After an attack has ended, the IDS supports forensic analysis of what happened. | Conducts forensic analysis once attack is over |
| 4 | 1 / A2a | 0.00 | Trojans disguise themselves as useful or benign software so users install them willingly. | They usually masquerade as helpful or harmless programs |
| 5 | 1 / A2b | 0.23 | A virus can spread by infecting the boot sector of a disk, as demonstrated by early malware such as Elk Cloner. | A program spread via boot sector infection |
| 6 | 1 / A2b | 0.25 | A worm can propagate across a network by exploiting a remote execution feature of a service, as the Morris worm did with sendmail. | Used a debugging feature of sendmail (remote execution) |
| 7 | 1 / A2b | 0.27 | An executable COM virus appends its viral code to a program and redirects the program's entry point to the virus body. | Append a virus body to a program |
| 8 | 1 / A2b | 0.25 | An executable EXE virus overwrites the program header so that execution begins in the virus rather than the original code. | Over write a program header to switch the entry point to a virus |
| 9 | 1 / A2b | 0.43 | Spyware secretly collects user activity such as logins, passwords, visited sites and keystrokes, enabling identity theft. | They steal user logins and passwords, document sites visited, log keystrokes and even redirect browsers to unwanted sites. |
| 10 | 1 / A3a | 0.10 | Disclosure threats such as snooping, sniffing and wiretapping breach confidentiality, and confidentiality services are the countermeasure. | Disclosure - unauthorized access to information |

## Attempts and scenario sampling

- Limit: **4 attempts per slot** (1 initial + 3 retries). A group attempt count is the **maximum** across its slots, so it cannot exceed 4. Earlier reports summed attempts across (a) and (b), which is why values above 4 appeared; that was a counting bug, not a higher limit.
- Point-level low-overlap retries are separate: **258** extra calls across the evaluation (max 2 per low point).
- Part B scenario sampling rate used: **9** sampled questions across 16 Part B questions; measured rate 7/19 = 36.8% (lower bound). Generated scenario slots: 16.

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
