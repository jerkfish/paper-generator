# Theory module report

- model: **deepseek-flash**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **23** (supported by lecture slides, not lecturer-marked); placeholders: **0**
- source overlap: **0** keys; target 0
- low stem-overlap points: **36** of 94; initial entailment {'yes': 22, 'partly': 12, 'no': 2}; final accepted entailment {'yes': 23, 'partly': 13}; verbatim-copy rejections: **6**; short quotes: **8**; repaired quotes: **1**
- tokens: 122889 prompt + 15491 completion = 138380 across 79 calls
- estimated cost: **$0.0555** (model deepseek-flash; input $0.3/M, output $1.2/M; official list-price estimate, not an invoice)
- cost per accepted question: **$0.0024**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | software/OS security | Explain | 051 - Software Security, slide 21; 051 - Software Security, slide 23 | exact |
| A10b | 6 | software/OS security | Explain | 041 - Windows Security, slide 11; 041 - Windows Security, slide 21; 041 - Windows Security, slide 4; 041 - Windows Security, slide 6 | exact |
| A1a | 2 | risk/management (ethics) | List | 071 - Ethics and Computer Security, slide 5 | topic+marks (any command); LOW |
| A1b | 6 | risk/management (ethics) | Discuss | 071 - Ethics and Computer Security, slide 11; 071 - Ethics and Computer Security, slide 12 | exact |
| A2a | 2 | classical ciphers | Explain | 031 - Classical Cryptography, slide 4 | exact |
| A3a | 2 | access control models | Explain | 024 - Formal Security Model, slide 21; 024 - Formal Security Model, slide 27 | exact |
| A3b | 6 | access control models | Describe | 023 - Access Control and Authorization, slide 10; 023 - Access Control and Authorization, slide 7; 023 - Access Control and Authorization, slide 8 | topic+marks (any command); LOW |
| A4a | 2 | attacks/malware | Explain | 051 - Software Security, slide 12 | exact |
| A4b | 6 | attacks/malware | State | 051 - Software Security, slide 10; 051 - Software Security, slide 13; 051 - Software Security, slide 7; 051 - Software Security, slide 9 | exact |
| A5a | 2 | network security | State | 062 - Intrusion Detection System, slide 7 | topic+marks (any command); LOW |
| A5b | 6 | network security | Explain | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A6a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 6; 071 - Ethics and Computer Security, slide 8 | exact |
| A6b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 3; 071 - Ethics and Computer Security, slide 7 | exact |
| A7a | 2 | attacks/malware | List | 011 - Introduction to Computer Security, slide 10 | topic+marks (any command); LOW |
| A7b | 6 | attacks/malware | Describe | 052 - Web Security, slide 15; 052 - Web Security, slide 16 | exact |
| A8a | 2 | authentication/biometrics | State | 072 - Biometrics and Authentication, slide 5 | exact |
| A8b | 6 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 7 | exact |
| A9a | 2 | attacks/malware | State | 062 - Intrusion Detection System, slide 14 | exact |
| A9b | 6 | attacks/malware | State | 011 - Introduction to Computer Security, slide 28; 011 - Introduction to Computer Security, slide 9; 061 - Network Security, slide 26 | exact |
| B1a | 5 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 12; 022 - Identification and Authentication, slide 8 | topic+marks (any command); LOW |
| B1b | 5 | authentication/biometrics | Discuss | 022 - Identification and Authentication, slide 16; 022 - Identification and Authentication, slide 18; 022 - Identification and Authentication, slide 24 | topic+marks (any command); LOW |
| B2a | 5 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 6; 073 - Trusted Computing, slide 8 | topic+marks (any command); LOW |
| B2b | 5 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | topic+marks (any command); LOW |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s11 |
| A10 | A10a, A10b | 2 | accepted | no | 051 - Software Security s23; 051 - Software Security s30; 041 - Windows Security s21 |
| A2 | A2a | 2 | accepted | no | 031 - Classical Cryptography s4; 031 - Classical Cryptography s25; 031 - Classical Cryptography s14 |
| A3 | A3a, A3b | 2 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| A4 | A4a, A4b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A5 | A5a, A5b | 1 | accepted | no | 061 - Network Security s4; 061 - Network Security s3; 062 - Intrusion Detection System s8 |
| A6 | A6a, A6b | 4 | accepted | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6; 071 - Ethics and Computer Security s8 |
| A7 | A7a, A7b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 011 - Introduction to Computer Security s7 |
| A8 | A8a, A8b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s18 |
| A9 | A9a, A9b | 1 | accepted | no | 011 - Introduction to Computer Security s28; 051 - Software Security s6; 062 - Intrusion Detection System s14 |
| B1 | B1a, B1b | 1 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s9; 022 - Identification and Authentication s12 |
| B2 | B2a, B2b | 3 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s14; 073 - Trusted Computing s6 |

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