# Theory module report

- model: **deepseek-flash**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **19** (supported by lecture slides, not lecturer-marked); placeholders: **2**
- source overlap: **0** keys; target 0
- low stem-overlap points: **16** of 78; initial entailment {'yes': 10, 'partly': 6}; final accepted entailment {'yes': 10, 'partly': 6}; verbatim-copy rejections: **6**; short quotes: **7**; repaired quotes: **1**
- tokens: 111009 prompt + 12606 completion = 123615 across 49 calls
- estimated cost: **$0.0484** (model deepseek-flash; input $0.3/M, output $1.2/M; official list-price estimate, not an invoice)
- cost per accepted question: **$0.0025**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | attacks/malware | Explain | 051 - Software Security, slide 12 | exact |
| A10b | 6 | attacks/malware | Explain | 051 - Software Security, slide 10; 051 - Software Security, slide 7; 051 - Software Security, slide 9 | exact |
| A1b | 6 | classical ciphers | State | 031 - Classical Cryptography, slide 14; 031 - Classical Cryptography, slide 4 | topic+marks (any command); LOW |
| A2a | 2 | classical ciphers | List | 031 - Classical Cryptography, slide 25 | topic+marks (any command); LOW |
| A3a | 2 | authentication/biometrics | List | 072 - Biometrics and Authentication, slide 5 | exact |
| A3b | 6 | authentication/biometrics | Discuss | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 9 | exact |
| A4a | 2 | access control models | Explain | 024 - Formal Security Model, slide 21; 024 - Formal Security Model, slide 24 | exact |
| A5a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 5 | exact |
| A5b | 6 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 11; 071 - Ethics and Computer Security, slide 12 | topic+marks (any command); LOW |
| A6a | 2 | network security | State | 062 - Intrusion Detection System, slide 7 | topic+marks (any command); LOW |
| A6b | 6 | network security | Describe | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A7a | 2 | software/OS security | State | 051 - Software Security, slide 21; 051 - Software Security, slide 30 | topic+marks (any command); LOW |
| A8b | 6 | access control models | Discuss | 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 4; 024 - Formal Security Model, slide 25; 024 - Formal Security Model, slide 26; 024 - Formal Security Model, slide 27 | topic+marks (any command); LOW |
| A9a | 2 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 12 | exact |
| A9b | 6 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 16; 022 - Identification and Authentication, slide 19 | exact |
| B1a | 5 | attacks/malware | Explain | 011 - Introduction to Computer Security, slide 10; 051 - Software Security, slide 13 | topic+marks (any command); LOW |
| B1b | 5 | attacks/malware | Explain | 052 - Web Security, slide 15 | topic+marks (any command); LOW |
| B2a | 5 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 6; 073 - Trusted Computing, slide 8 | topic+marks (any command); LOW |
| B2b | 5 | trusted computing/blockchain | Discuss | 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | topic+marks (any command); LOW |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| A7b | 6 | software/OS security | Explain | 4 | A7b point 1: marking point is a verbatim copy of its quote; phrase the point as an answer requirement, not as copied slide text |
| A8a | 2 | access control models | State | 4 | A8a: sub-angle not followed; use one of ['acl', 'acm', 'capability', 'access control list', 'matrix'] |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1b | 2 | accepted | no | 031 - Classical Cryptography s25; 031 - Classical Cryptography s26; 031 - Classical Cryptography s14 |
| A10 | A10a, A10b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A2 | A2a | 2 | accepted | no | 031 - Classical Cryptography s24; 031 - Classical Cryptography s25; 031 - Classical Cryptography s26 |
| A3 | A3a, A3b | 1 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s24; 022 - Identification and Authentication s8 |
| A4 | A4a | 2 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| A5 | A5a, A5b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6 |
| A6 | A6a, A6b | 1 | accepted | no | 061 - Network Security s4; 061 - Network Security s3; 062 - Intrusion Detection System s8 |
| A7 | A7a, A7b | 4 | placeholder | no | 051 - Software Security s30; 051 - Software Security s3; 042 - Linux Security s26 |
| A8 | A8a, A8b | 4 | placeholder | no | 023 - Access Control and Authorization s7; 024 - Formal Security Model s5; 024 - Formal Security Model s25 |
| A9 | A9a, A9b | 1 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s12; 022 - Identification and Authentication s10 |
| B1 | B1a, B1b | 1 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 052 - Web Security s13 |
| B2 | B2a, B2b | 2 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s14; 073 - Trusted Computing s6 |

## Deck coverage

- 071 Ethics: {'071 - Ethics and Computer Security': {'slides_with_text': 16, 'chunks': 16, 'chars': 6387}}
- total decks with text: 25; total chunks: 496

## Verification rules applied

- quote must be a verbatim contiguous substring of the cited retrieved chunk (whitespace-normalised); ellipses and slide-title-only quotes rejected; near-paraphrases repaired only when an exact close line exists;
- exactly one marking point per mark;
- near-copy rejected at fuzzy similarity >= 0.80 against all 35 papers; cross-generated near-duplicates and source overlap rejected;
- cited decks must be in the slot topic's allowed deck map;
- first gate is stemmed content-token overlap (Snowball English stemmer); low-overlap points are checked by an LLM entailment verifier (yes/partly/no), and only 'no' triggers regeneration;
- a marking point that is a verbatim copy of its quote is rejected;
- command word and topic sub-angle must appear; dependent (b) must refer back to (a); Part B (a)/(b) share a generated scenario;
- no retrieval evidence => placeholder, never an unsupported answer.