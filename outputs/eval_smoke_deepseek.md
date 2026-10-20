# Realistic-mode evaluation - seeds 1-20

Each seed runs the revised realistic planner and the full theory module (BM25 retrieval, cheap Qwen model, up to 3 retries, source overlap/topic/quote checks). Model and price settings are those in `src/config.py`; costs are estimates, not invoices.

- Models used: **deepseek-flash** (free-tier quotas rotated; per-seed model in the table).
- Seeds completed: **1/20**; failed: 
- Theory slots: 24; accepted **24**; placeholders **0**; placeholder rate **0.0%**.
- Source overlap: **0** keys across 0/20 papers; **0** slots involved; target 0.
- Max near-copy similarity against the 35 past papers: **0.66** (threshold 0.80).
- Calls: 78; tokens: 140196; estimated total cost: **$0.0547**; cost per accepted question: **$0.0023**.
- Scenario questions generated: **2** Part B slots.
- Low term-overlap marking points flagged: **42**.

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

| Seed | Model | Computed | Placeholders | Attempts avg | Attempts max | Overlap keys | Overlap rate | Max near-copy | Part B scenarios | Point retries | Low overlap | Cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | deepseek-flash | 0 | 0 | 1.58 | 2 | 0 | 0.0% | 0.66 | 2 | 44 | 42.0% | $0.0547 |

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
| 1 | 1 / A8a | 0.660 | Explain the difference between morals, ethics and laws as sources of guidance for professional conduct in computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| 2 | 1 / A6b | 0.610 | Describe the two primary system components of the Next Generation Secure Computing Base (NGSCB), explaining the role of each component and how they work together on the trusted platform. | CSC662-2023-07 QA8b: List and explain the two primary system components of Next Generation Secure Computing Base(NGSCB). (6 marks) |
| 3 | 1 / A4a | 0.533 | State TWO (2) typical locations where network-based IDS sensors are placed in a network. | CSC662-2017-07 Q5c: Elaborate TWO (2) types of Intrusion Detection System (IDS) are Network-based (NIDS) and Host-Based (HIDS). |
| 4 | 1 / A7a | 0.519 | A biometric system performs its work in two broad stages. List the TWO (2) stages of the biometric authentication process. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 5 | 1 / A3a | 0.495 | Explain how malware such as spyware and rootkits can impact each element of the CIA triad, referring to confidentiality, integrity and availability. | CSC662-2010-10 Q4b: Discuss with example security models that can be used to address the confidentiality, 
integrity and availability security policies. |
| 6 | 1 / A1a | 0.474 | State TWO (2) key points about software insecurity and buffer overflows as described in the Software Security lecture. | CSC662-2019-12 QA3b: Identify TWO (2) type of authentication device consists of a reader or scanner and software that encrypts and;
Explain how it works in the computer security perspective. |
| 7 | 1 / A9a | 0.470 | Explain TWO (2) password security controls that can be applied to password files and accounts, as described in the lecture. | CSC662-2008-04 Q2b: Explain TWO (2) reasons why password cracking is important for administrator. |
| 8 | 1 / A4b | 0.461 | Explain three preventive network security mechanisms that an organization can deploy to control and protect its network traffic, describing what each mechanism does. | CSC662-2011-04 Q11: Describe THREE (3) reasons why organization, which has a network, will faces more security issues than any organization without networking. |
| 9 | 1 / A8b | 0.458 | Refer to your answer in (a). Explain six requirements that a professional code of ethics and conduct, such as the ACM code, places on a computing professional's behaviour in security work. | CSC662-2022-02 QA3b: Using your answer in a), explain how UNIX grants access to any computing resources. |
| 10 | 1 / A10a | 0.452 | State TWO (2) detection outcomes that an intrusion detection system may produce when monitoring for attacks, and briefly indicate which outcome represents a failure to detect an attack. | CSC662-2017-07 Q5c: Elaborate TWO (2) types of Intrusion Detection System (IDS) are Network-based (NIDS) and Host-Based (HIDS). |

## Low-overlap points remaining after point retries

Each low-overlap point is regenerated up to **2 times**; if it is still below the threshold it remains flagged for human review.

| # | Seed / slot | Overlap | Point | Quote |
|---:|---|---:|---|---|
| 1 | 1 / A10a | 0.22 | A false negative occurs when the IDS fails to detect an attack that is present. | IDS missed an attack |
| 2 | 1 / A10b | 0.38 | Disclosure is unauthorised access to information, and confidentiality services counter this threat. | Disclosure - unauthorized access to information |
| 3 | 1 / A10b | 0.44 | Deception involves acceptance of false data, and integrity services counter this threat. | Deception - acceptance of false data |
| 4 | 1 / A10b | 0.44 | Usurpation is unauthorised control of part of a system, and availability services counter this threat. | Usurpation - unauthorized control of some part of a system |
| 5 | 1 / A10b | 0.46 | An attack is a deliberate act that exploits a vulnerability, whereas a threat is only a potential violation of security. | Attack: a deliberate act that exploits vulnerability |
| 6 | 1 / A1b | 0.40 | Discretionary access control in Windows permits detailed, fine-grained control over many different kinds of entities, both within the OS and in applications. | DACS enable ﬁne-grained access control of heterogeneous entities in Windows itself as well as applications. |
| 7 | 1 / A1b | 0.29 | The very complexity of these mechanisms is a weakness, since configuration mistakes and coding bugs can cause serious security breaches. | The complexity of Windows security mechanisms is also its enemy: misconﬁguration as well as implementation bugs may lead to severe security incidents. |
| 8 | 1 / A1b | 0.36 | Processes and threads act as the active subjects in Windows, and each subject's security credentials are held in a token. | Windows subjects are processes and threads. |
| 9 | 1 / A1b | 0.42 | Tokens carry security attributes and are passed down, possibly with restrictions, when new processes are created. | Tokens are inherited (possibly with restrictions) during creation of new processes. |
| 10 | 1 / A2a | 0.11 | Trojans disguise themselves as useful or benign programs so users accept them. | They usually masquerade as helpful or harmless programs |

## Attempts and scenario sampling

- Limit: **4 attempts per slot** (1 initial + 3 retries). A group attempt count is the **maximum** across its slots, so it cannot exceed 4. Earlier reports summed attempts across (a) and (b), which is why values above 4 appeared; that was a counting bug, not a higher limit.
- Point-level low-overlap retries are separate: **44** extra calls across the evaluation (max 2 per low point).
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
