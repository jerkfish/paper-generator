# Theory module report

- model: **qwen3.6-plus**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **22** (supported by lecture slides, not lecturer-marked); placeholders: **2**
- source overlap: **0** keys; target 0
- low term-overlap points: **44**; short quotes: **8**; repaired quotes: **0**
- tokens: 117353 prompt + 13655 completion = 131008 across 34 calls
- estimated cost: **$0.0055** (input $0.022/M, output $0.216/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0003**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | attacks/malware | State | 062 - Intrusion Detection System, slide 14; 062 - Intrusion Detection System, slide 29 | exact |
| A10b | 6 | attacks/malware | State | 011 - Introduction to Computer Security, slide 14; 011 - Introduction to Computer Security, slide 28; 011 - Introduction to Computer Security, slide 9; 051 - Software Security, slide 9; 052 - Web Security, slide 16; 052 - Web Security, slide 19 | exact |
| A1a | 2 | network security | Explain | 062 - Intrusion Detection System, slide 32; 062 - Intrusion Detection System, slide 7 | exact |
| A1b | 6 | network security | Describe | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A2a | 2 | software/OS security | List | 051 - Software Security, slide 23; 051 - Software Security, slide 30 | exact |
| A2b | 6 | software/OS security | State | 041 - Windows Security, slide 11; 041 - Windows Security, slide 2; 041 - Windows Security, slide 3; 041 - Windows Security, slide 6 | topic+marks (any command); LOW |
| A3a | 2 | attacks/malware | State | 051 - Software Security, slide 12 | exact |
| A3b | 6 | attacks/malware | Discuss | 051 - Software Security, slide 10; 051 - Software Security, slide 13; 051 - Software Security, slide 6; 051 - Software Security, slide 7 | topic+marks (any command); LOW |
| A4a | 2 | access control models | Explain | 024 - Formal Security Model, slide 24; 024 - Formal Security Model, slide 27 | exact |
| A4b | 6 | access control models | Explain | 023 - Access Control and Authorization, slide 10; 023 - Access Control and Authorization, slide 7; 023 - Access Control and Authorization, slide 8 | exact |
| A5a | 2 | access control models | List | 023 - Access Control and Authorization, slide 4 | topic+marks (any command); LOW |
| A5b | 6 | access control models | Discuss | 024 - Formal Security Model, slide 21; 024 - Formal Security Model, slide 25; 024 - Formal Security Model, slide 26; 024 - Formal Security Model, slide 5 | topic+marks (any command); LOW |
| A6a | 2 | attacks/malware | Explain | 011 - Introduction to Computer Security, slide 10 | exact |
| A6b | 6 | attacks/malware | Explain | 052 - Web Security, slide 15 | exact |
| A7a | 2 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 6; 073 - Trusted Computing, slide 8 | exact |
| A7b | 6 | trusted computing/blockchain | Describe | 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A8a | 2 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 5 | exact |
| A8b | 6 | risk/management (ethics) | Discuss | 071 - Ethics and Computer Security, slide 11; 071 - Ethics and Computer Security, slide 12 | exact |
| A9a | 2 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 5 | exact |
| A9b | 6 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 7 | exact |
| B1a | 5 | authentication/biometrics | State | 022 - Identification and Authentication, slide 10; 022 - Identification and Authentication, slide 12 | topic+marks (any command); LOW |
| B1b | 5 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 16; 022 - Identification and Authentication, slide 18; 022 - Identification and Authentication, slide 20; 022 - Identification and Authentication, slide 24; 022 - Identification and Authentication, slide 9 | topic+marks (any command); LOW |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| B2a | 5 | risk/management (ethics) | Explain | 4 | Part B scenario is not grounded in the evidence (term coverage 0.19) |
| B2b | 5 | risk/management (ethics) | Discuss | 0 | B2b: Part B scenario (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 2 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 061 - Network Security s3 |
| A10 | A10a, A10b | 2 | accepted | no | 011 - Introduction to Computer Security s28; 062 - Intrusion Detection System s14; 062 - Intrusion Detection System s21 |
| A2 | A2a, A2b | 2 | accepted | no | 051 - Software Security s30; 051 - Software Security s23; 051 - Software Security s22 |
| A3 | A3a, A3b | 2 | accepted | no | 011 - Introduction to Computer Security s28; 011 - Introduction to Computer Security s10; 051 - Software Security s12 |
| A4 | A4a, A4b | 4 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| A5 | A5a, A5b | 3 | accepted | no | 023 - Access Control and Authorization s18; 024 - Formal Security Model s5; 023 - Access Control and Authorization s4 |
| A6 | A6a, A6b | 6 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A7 | A7a, A7b | 2 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A8 | A8a, A8b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s7 |
| A9 | A9a, A9b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s24 |
| B1 | B1a, B1b | 3 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s12; 022 - Identification and Authentication s10 |
| B2 | B2a, B2b | 4 | placeholder | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6; 071 - Ethics and Computer Security s9 |

## Deck coverage

- 071 Ethics: {'071 - Ethics and Computer Security': {'slides_with_text': 16, 'chunks': 16, 'chars': 6387}}
- total decks with text: 25; total chunks: 496

## Verification rules applied

- quote must be a verbatim contiguous substring of the cited retrieved chunk (whitespace-normalised); ellipses and slide-title-only quotes rejected; near-paraphrases repaired only when an exact close line exists;
- exactly one marking point per mark;
- near-copy rejected at fuzzy similarity >= 0.80 against all 35 papers; cross-generated near-duplicates and source overlap rejected;
- cited decks must be in the slot topic's allowed deck map;
- quote must share a key term with its marking point; low overlap is flagged for human review;
- command word and topic sub-angle must appear; dependent (b) must refer back to (a); Part B (a)/(b) share a generated scenario;
- no retrieval evidence => placeholder, never an unsupported answer.