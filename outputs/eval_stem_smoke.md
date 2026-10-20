# Realistic-mode evaluation - seeds 1-20

Each seed runs the revised realistic planner and the full theory module (BM25 retrieval, configured model, up to 3 retries, source overlap/topic/quote checks, stemmed-overlap + entailment gates). Model and price settings are those in `src/config.py`; costs are estimates, not invoices.

- Model used: **deepseek-flash** (one model for all seeds).
- Seeds completed: **1/20**; failed: 
- Theory slots: 24; accepted **24**; placeholders **0**; placeholder rate **0.0%**.
- Source overlap: **0** keys across 0/20 papers; **0** slots involved; target 0.
- Max near-copy similarity against the 35 past papers: **0.79** (threshold 0.80).
- Calls: 69; tokens: 125219; estimated total cost: **$0.0479**; cost per accepted question: **$0.0020**.
- Scenario questions generated: **2** Part B slots.
- Low stem-overlap marking points remaining: **32**.

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
| 1 | deepseek-flash | 0 | 0 | 1.42 | 2 | 0 | 0.0% | 0.79 | 2 | 40 | 32.0% | $0.0479 |

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

Actual topic mix is accepted marks by the planner's slot topic; the majority-deck mix is retained only as a JSON diagnostic.

## Placeholder slots by seed

- none

## Top 10 accepted/past question pairs by fuzzy similarity

| # | Seed / slot | Ratio | Generated question | Nearest real past question |
|---:|---|---:|---|---|
| 1 | 1 / A7a | 0.790 | List TWO (2) stages of the biometric authentication process. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 2 | 1 / A1a | 0.621 | State two reasons why software insecurity arises, as described in the lecture. | CSC662-2025-02 QA1a: State TWO (2) reasons why physical security is needed. |
| 3 | 1 / A10a | 0.603 | State TWO (2) detection outcomes an intrusion detection system may produce. | CSC662-2023-02 QA6a: What can be detected by intrusion detection system? |
| 4 | 1 / A4b | 0.580 | Explain three preventive network security mechanisms, other than intrusion detection systems, and describe how each mechanism protects an organization's network. | CSC662-2025-02 QA6b: Explain 3 preventive network security mechanisms, including a firewall, a proxy server, and network segmentation, that can be implemented to enhance the company's security posture. In your answer, describe how each mechanism protects an organization's network. |
| 5 | 1 / A9a | 0.558 | Explain two password security controls used to protect password-based authentication. | CSC662-2008-04 Q2d: Explain TWO (2) types of errors occurred in biometric authentication. |
| 6 | 1 / A3a | 0.552 | Explain how spyware and rootkits each affect confidentiality, integrity and availability. | CSC662-2013-01 Q7: Describe with example how the computer security objectives of confidentiality, integrity and availability relate to database management system. |
| 7 | 1 / A8b | 0.546 | Refer to your answer in (a). Explain six ways the ACM code guides a computing professional's conduct and ethical practice. | CSC662-2022-02 QA3b: Using your answer in a), explain how UNIX grants access to any computing resources. |
| 8 | 1 / A6b | 0.530 | Describe six components and functions of the Next Generation Secure Computing Base (NGSCB), focusing on the Nexus and the Nexus Computing Agent. | CSC662-2023-07 QA8b: List and explain the two primary system components of Next Generation Secure Computing Base(NGSCB). (6 marks) |
| 9 | 1 / A6a | 0.512 | Explain how a chain of trust is established in trusted computing, referring to the TPM. | CSC662-2013-01 Q12: List FOUR (4) criteria's of trusted modes in the NGSCB Computing Environment. |
| 10 | 1 / A1b | 0.511 | Explain six Windows security mechanisms and features described in the lecture, and note why their complexity can itself be a security risk. | CSC662-2024-07 QA10b: Explain THREE (3) security mechanisms used by the cryptocurrency system handling this issue. |

## Low-overlap points remaining after point retries

Each low-overlap point is regenerated up to **2 times**; if it is still below the threshold it remains flagged for human review.

| # | Seed / slot | Overlap | Point | Quote |
|---:|---|---:|---|---|
| 1 | 1 / A10a | 0.00 | A correct identification of an intrusion or attack, reported as a true positive. | IDS correctly identify intrusions and attacks |
| 2 | 1 / A1b | 0.33 | Security credentials for a Windows subject are held in a token, which maps a principal to a subject and may carry extra security attributes. | Security credentials for a subject are stored in a token. |
| 3 | 1 / A1b | 0.42 | The registry is a hierarchical database of critical system information, including security-related hives such as SAM and Security. | A hierarchical database containing critical system information |
| 4 | 1 / A2a | 0.00 | Trojans disguise themselves as useful or benign software so users install them willingly. | They usually masquerade as helpful or harmless programs |
| 5 | 1 / A2b | 0.33 | A virus can infect a COM executable by appending its virus body to the host program. | Append a virus body to a program |
| 6 | 1 / A2b | 0.39 | The virus saves the host program's original entry point inside the virus body so it can regain control later. | Save an entry point to a program in a virus body |
| 7 | 1 / A2b | 0.36 | The Morris worm propagated across the Arpanet by exploiting a debugging feature of sendmail that allowed remote execution. | Used a debugging feature of sendmail (remote execution) |
| 8 | 1 / A3b | 0.22 | The worm harvested the victim's friends by issuing a GET request on a user profile. | Get the list of user's heros by using a GET on a user proﬁle |
| 9 | 1 / A3b | 0.30 | Any visitor to an infected profile had their own profile and friends list infected, enabling self-propagation. | Any user who visits an infected user's page will gets proﬁle infected with Javascript and his friends list infected with Samy |
| 10 | 1 / A3b | 0.20 | The outbreak ultimately infected roughly one million MySpace profiles, showing the scale of impact. | Eventually about 1,000,000 MySpace proﬁles were infected. |

## Attempts and scenario sampling

- Limit: **4 attempts per slot** (1 initial + 3 retries). A group attempt count is the **maximum** across its slots, so it cannot exceed 4. Earlier reports summed attempts across (a) and (b), which is why values above 4 appeared; that was a counting bug, not a higher limit.
- Point-level low-overlap retries are separate: **40** extra calls across the evaluation (max 2 per low point).
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
- Actual topic mix is accepted marks by the planner's slot topic; the allowed-deck check is reported separately.
- Multiple Qwen models were used because the free-tier quota was exhausted during the 20-seed run; the per-seed model is shown. The cost column uses the configurable qwen-flash list-price estimate, not per-model invoices.
