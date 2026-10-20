# Final realistic-mode evaluation

## Setup

This is the primary evaluation requested in the final pass: **one model for all 20 seeds**, the hardened theory pipeline, and no quota rotation.

- Model: **DeepSeek V4.1 Flash** (`deepseek-flash`, DeepSeek-V4.1-Flash-1017).
- Seeds: **1-20**; theory slots: **464**; accepted **457**; placeholders **7** (1.5%).
- Estimated cost: **$1.0315**, **$0.0023** per accepted question.
- Official DeepSeek list price used: **$0.30/1M input, $1.20/1M output** (peak cache-miss rates; off-peak is half). The run took place in the peak window (01:00-04:00 UTC on a weekday), so peak rates apply. Cache-hit discounts are not counted, so this is a conservative estimate from token usage, not an invoice.
- Calls: **1358**; tokens: **2632459**.
- Source overlap: **0** keys; allowed-deck violations: **0**.
- Max near-copy against the 35 past papers: **0.764** (threshold 0.80).
- Raw per-seed payloads: `outputs/eval_final_deepseek/seed_XX_theory.json` (and `.md` reports).

## Per-seed results

| Seed | Computed | Accepted | Placeholders | Attempts avg | Attempts max | Entailment calls | Point regen calls | Max near-copy | Cost |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 24 | 0 | 1.92 | 4 | 33 | 3 | 0.66 | $0.0584 |
| 2 | 0 | 23 | 1 | 1.75 | 4 | 35 | 1 | 0.55 | $0.0547 |
| 3 | 0 | 24 | 0 | 2.00 | 3 | 28 | 2 | 0.62 | $0.0569 |
| 4 | 0 | 24 | 0 | 1.67 | 3 | 36 | 1 | 0.61 | $0.0502 |
| 5 | 14 | 21 | 0 | 1.67 | 4 | 28 | 0 | 0.61 | $0.0441 |
| 6 | 14 | 19 | 2 | 2.00 | 4 | 24 | 1 | 0.65 | $0.0518 |
| 7 | 2 | 23 | 0 | 1.58 | 3 | 42 | 1 | 0.71 | $0.0481 |
| 8 | 0 | 24 | 0 | 1.50 | 3 | 30 | 2 | 0.57 | $0.0478 |
| 9 | 6 | 23 | 0 | 1.58 | 2 | 35 | 1 | 0.66 | $0.0442 |
| 10 | 14 | 19 | 2 | 2.00 | 4 | 16 | 0 | 0.58 | $0.0484 |
| 11 | 6 | 23 | 0 | 1.50 | 2 | 36 | 2 | 0.68 | $0.0459 |
| 12 | 6 | 23 | 0 | 2.00 | 4 | 38 | 2 | 0.61 | $0.0555 |
| 13 | 0 | 22 | 2 | 1.67 | 4 | 34 | 2 | 0.56 | $0.0488 |
| 14 | 0 | 24 | 0 | 2.00 | 3 | 43 | 4 | 0.67 | $0.0587 |
| 15 | 0 | 24 | 0 | 1.92 | 3 | 35 | 2 | 0.61 | $0.0560 |
| 16 | 2 | 23 | 0 | 1.92 | 3 | 30 | 1 | 0.76 | $0.0520 |
| 17 | 12 | 22 | 0 | 1.92 | 3 | 37 | 1 | 0.57 | $0.0527 |
| 18 | 0 | 24 | 0 | 1.92 | 4 | 34 | 2 | 0.63 | $0.0559 |
| 19 | 0 | 24 | 0 | 1.58 | 2 | 34 | 1 | 0.54 | $0.0511 |
| 20 | 0 | 24 | 0 | 1.67 | 3 | 31 | 2 | 0.64 | $0.0502 |
| **Total** |  | **457** | **7** | **1.79** | **4** | **659** | **31** | **0.76** | **$1.0315** |

Placeholder rate overall: **7/464 (1.5%)**. Draft attempts: **667** across **240** groups (**2.78** draft calls per group); per-slot max attempts mean **1.79**, max **4** (limit 4 = initial + 3 retries). The old >4 values came from summing attempts across (a)/(b) and point retries.

## Marking-point gates

- First gate: **stemmed content-token overlap** (Snowball English stemmer) at threshold **0.50**.
- First-pass high stem-overlap points: **1251/1896** (66.0%); these passed without an entailment call.
- Low stem-overlap points that triggered the gate: **645** (34.0% of accepted points); after point handling, **628** still have low stem overlap (**17** rewrites moved above the threshold).

| Entailment verdict (initial check) | Count | Share of checked |
|---|---:|---:|
| yes | 327 | 50.7% |
| partly | 287 | 44.5% |
| no | 31 | 4.8% |

Only **no** points are regenerated (up to two point-level rewrites each); **yes** and **partly** points are kept and recorded. Point regeneration calls: **31**; entailment calls: **659** (including checks on low-overlap rewrites).
Final accepted verdicts: **yes 331**, **partly 297**, **no 0**; a 'no' point that was successfully rewritten is replaced, so the final 'no' count is lower than the initial count.

Verbatim-copy rejections (point copied from its quote): **103** across the 20 seeds.

### Ten remaining low-stem-overlap points

| # | Seed / slot | Stem overlap | Entailment | Point | Quote |
|---:|---|---:|---|---|---|
| 1 | 1 / A10a | 0.25 | yes | An IDS can confirm whether an attack succeeded or failed by examining host-based IDS log entries. | Verifies success or failure of attack by reviewing HIDS log entries |
| 2 | 1 / A2a | 0.12 | yes | Trojans disguise themselves as useful or benign programs so users accept them. | They usually masquerade as helpful or harmless programs |
| 3 | 1 / A2b | 0.36 | partly | A virus can spread by infecting the boot sector of a disk, as illustrated by Elk Cloner spreading through boot sector infection. | A program spread via boot sector infection |
| 4 | 1 / A2b | 0.25 | partly | A worm can propagate across a network by exploiting a remote execution feature of a service, as the Morris worm did with sendmail. | Used a debugging feature of sendmail (remote execution) |
| 5 | 1 / A2b | 0.40 | partly | An executable COM virus appends its virus body to a program and redirects the program entry point to the virus code. | Append a virus body to a program |
| 6 | 1 / A2b | 0.44 | partly | A rootkit hides malicious processes and software so that the attacker keeps privileged remote access, and it is hard to detect because it hides from the very tools used to find it. | Rootkits are a type of malware that mask malicious processes and software in the infected systems to ensure privileged remote access. |
| 7 | 1 / A3a | 0.29 | partly | A disclosure threat involves unauthorized access to information (through snooping, sniffing or wiretapping) and is countered by confidentiality services, so it harms confidentiality. | Disclosure - unauthorized access to information |
| 8 | 1 / A3a | 0.42 | partly | A disruption threat interrupts or prevents correct operation of the system and is countered by integrity services, so it harms availability of correct operation. | Disruption - interruption or prevention of correct operation |
| 9 | 1 / A3b | 0.38 | yes | The worm obtained the list of the user's heroes by issuing a GET request on a user profile. | Get the list of user's heros by using a GET on a user proﬁle |
| 10 | 1 / A4a | 0.25 | yes | A sensor can be positioned on the DMZ. | On the DMZ |

## Placeholder breakdown

### By Part A / Part B

| Part | Slots | Placeholders | Rate |
|---|---:|---:|---:|
| Part A | 384 | 5 | 1.3% |
| Part B | 80 | 2 | 2.5% |

### By scenario / non-scenario

A slot counts as scenario only when its Part B group was sampled for a scenario; Part A is always non-scenario.

| Group type | Slots | Placeholders | Rate |
|---|---:|---:|---:|
| scenario | 32 | 0 | 0.0% |
| non-scenario | 432 | 7 | 1.6% |

### By topic

| Topic | Slots | Placeholders | Rate |
|---|---:|---:|---:|
| access control models | 68 | 1 | 1.5% |
| attacks/malware | 114 | 2 | 1.8% |
| authentication/biometrics | 80 | 0 | 0.0% |
| classical ciphers | 12 | 1 | 8.3% |
| network security | 40 | 0 | 0.0% |
| risk/management (ethics) | 70 | 2 | 2.9% |
| software/OS security | 40 | 1 | 2.5% |
| trusted computing/blockchain | 40 | 0 | 0.0% |

Part B scenario sampling: **16/40** Part B groups sampled a scenario; **32** scenario-bearing questions were accepted. Sampling rate used: 7/19 = 36.8% (the measured lower bound).

## Diversity across the 20 papers

- Theory questions generated: **457**; distinct question texts: **408** (89.3%); duplicate instances: **49**.
- Duplicate pairs are counted between different seeds only. The **same-angle rate** is the assessment-level duplicate rate: two questions test the same sub-angle even if their wording differs. The **wording rate** counts exact text, semantic duplicates (sequence >= 0.65 and Jaccard >= 0.45), or near-copy >= 0.70.

| Topic | Questions | Distinct | Distinct rate | Angles used | Cross-seed pairs | Same-angle pairs | Same-angle rate | Top-2 angle share | Wording dup rate | Flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| access control models | 67 | 57 | 85.1% | 3/3 | 2125 | 775 | 36.5% | 76.1% | 3.4% |  |
| attacks/malware | 112 | 101 | 90.2% | 6/6 | 5951 | 1062 | 17.8% | 44.6% | 2.6% |  |
| authentication/biometrics | 80 | 73 | 91.2% | 4/4 | 3040 | 898 | 29.5% | 68.8% | 7.9% |  |
| classical ciphers | 11 | 11 | 100.0% | 3/3 | 53 | 24 | 45.3% | 90.9% | 3.8% | LOW |
| network security | 40 | 33 | 82.5% | 3/3 | 760 | 343 | 45.1% | 95.0% | 11.7% | LOW |
| risk/management (ethics) | 68 | 60 | 88.2% | 4/4 | 2188 | 1008 | 46.1% | 91.2% | 3.7% | LOW |
| software/OS security | 39 | 35 | 89.7% | 2/3 | 722 | 361 | 50.0% | 100.0% | 3.3% | LOW |
| trusted computing/blockchain | 40 | 38 | 95.0% | 2/3 | 760 | 400 | 52.6% | 100.0% | 7.1% | LOW |

Low-diversity topics flagged: **classical ciphers, network security, risk/management (ethics), software/OS security, trusted computing/blockchain**.
Ethics (deck 071) is flagged: 91.2% of its questions fall into its two dominant sub-angles; distribution: professional code of ethics and conduct (41), morals, ethics and laws (21), privacy and organizational responsibility (4), ethical impacts of technology (2).

### Unused slides per topic

Counted over the union of the 20 papers: slides in the topic's allowed decks that were never cited by an accepted question of that topic.

| Topic | Slides in allowed decks | Used | Unused | Unused rate |
|---|---:|---:|---:|---:|
| access control models | 121 | 13 | 108 | 89.3% |
| attacks/malware | 210 | 30 | 180 | 85.7% |
| authentication/biometrics | 109 | 17 | 92 | 84.4% |
| classical ciphers | 30 | 7 | 23 | 76.7% |
| network security | 80 | 7 | 73 | 91.2% |
| risk/management (ethics) | 16 | 10 | 6 | 37.5% |
| software/OS security | 100 | 11 | 89 | 89.0% |
| trusted computing/blockchain | 71 | 6 | 65 | 91.5% |

## Top 10 accepted/past-question pairs

| # | Seed / slot | Ratio | Generated question | Nearest real past question |
|---:|---|---:|---|---|
| 1 | 16 / A10a | 0.764 | List the TWO (2) stages of the biometric authentication process. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 2 | 7 / A4a | 0.707 | List the TWO (2) stages that make up the biometric authentication process. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 3 | 11 / A3a | 0.683 | State the two stages of the biometric authentication process. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 4 | 7 / A6a | 0.674 | Explain the difference between morals, ethics and laws as three forms of guidance for conduct in computer security work. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| 5 | 14 / A1a | 0.667 | Explain the difference between morals, ethics and laws as forms of guidance for professional conduct in computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| 6 | 1 / A6b | 0.662 | Describe the two primary system components of the Next Generation Secure Computing Base (NGSCB) and, for each component, state its role in the trusted platform. | CSC662-2023-07 QA8b: List and explain the two primary system components of Next Generation Secure Computing Base(NGSCB). (6 marks) |
| 7 | 9 / A5a | 0.660 | Explain the difference between morals, ethics and laws as sources of guidance for professional conduct in computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| 8 | 6 / A5a | 0.648 | List the TWO (2) stages that make up the authentication process in a biometric system. | CSC662-2022-02 QA5a: List TWO (2) distinct phases in the authentication process. |
| 9 | 6 / A3b | 0.647 | State SIX (6) facts about the two primary system components of the Next Generation Secure Computing Base (NGSCB), covering the Nexus and the Nexus Computing Agent (NCA). | CSC662-2023-07 QA8b: List and explain the two primary system components of Next Generation Secure Computing Base(NGSCB). (6 marks) |
| 10 | 1 / A8a | 0.646 | Explain the difference between morals, ethics and laws as three forms of guidance for professional conduct in computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |

## Stem-length follow-up

This 20-seed run predates the mark-aware stem-length check. A fresh 8-seed sample with the check (`outputs/eval_stem_sample/`, seeds 1-8) reduced the median stem length from **19 to 12** words for 2-mark questions, **31 to 26.5** for 5-mark questions, and **31 to 21** for 6-mark questions; all generated stems were inside the clean-modern 90th percentile (18/54/43 words). That sample accepted 181/185 slots with 4 placeholders (2.2%). Details: `stem_length_report.md`.

## Prior-figure corrections

- The previous **26/474** placeholder projection was wrong: rejecting 10 near-copy questions does not add slots. With 464 total theory slots the corrected figure is **26/464 = 5.6%**.
- The appendix sentence about quota-affected seeds was corrected: the affected clusters are qwen3.6-flash seeds 14 and 16, and qwen3.6-plus seeds 13, 15 and 19.

## Appendix

`eval_multi_model_appendix.md` is the earlier multi-model run, clearly labelled **pre-hardening** and kept only for comparison.

## Human evaluation

`human_eval.xlsx` contains 20 generated and 10 real past questions, shuffled with no labels; the hidden `key` sheet records origin.
