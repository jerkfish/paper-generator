# Theory module report

- model: **qwen3.8-max**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **22** (supported by lecture slides, not lecturer-marked); placeholders: **1**
- source overlap: **0** keys; target 0
- low term-overlap points: **25**; short quotes: **3**; repaired quotes: **0**
- tokens: 83947 prompt + 11919 completion = 95866 across 28 calls
- estimated cost: **$0.0044** (input $0.022/M, output $0.216/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0002**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | network security | State | 062 - Intrusion Detection System, slide 5; 062 - Intrusion Detection System, slide 7 | topic+marks (any command); LOW |
| A10b | 6 | network security | Discuss | 061 - Network Security, slide 26; 061 - Network Security, slide 4 | topic+marks (any command); LOW |
| A1a | 2 | attacks/malware | List | 051 - Software Security, slide 12; 051 - Software Security, slide 13 | topic+marks (any command); LOW |
| A1b | 6 | attacks/malware | State | 051 - Software Security, slide 10; 051 - Software Security, slide 6; 051 - Software Security, slide 7; 051 - Software Security, slide 9; 052 - Web Security, slide 15 | exact |
| A2a | 2 | classical ciphers | Explain | 031 - Classical Cryptography, slide 4 | exact |
| A3a | 2 | authentication/biometrics | State | 072 - Biometrics and Authentication, slide 5 | exact |
| A3b | 6 | authentication/biometrics | Discuss | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 7; 072 - Biometrics and Authentication, slide 9 | exact |
| A4a | 2 | attacks/malware | Explain | 011 - Introduction to Computer Security, slide 10 | exact |
| A4b | 6 | attacks/malware | Discuss | 051 - Software Security, slide 2; 052 - Web Security, slide 13; 052 - Web Security, slide 14; 052 - Web Security, slide 16 | topic+marks (any command); LOW |
| A5a | 2 | access control models | Explain | 024 - Formal Security Model, slide 27; 024 - Formal Security Model, slide 5 | exact |
| A5b | 6 | access control models | Describe | 023 - Access Control and Authorization, slide 10; 023 - Access Control and Authorization, slide 7; 023 - Access Control and Authorization, slide 8; 041 - Windows Security, slide 16; 041 - Windows Security, slide 18 | topic+marks (any command); LOW |
| A6a | 2 | attacks/malware | State | 011 - Introduction to Computer Security, slide 16; 062 - Intrusion Detection System, slide 17 | exact |
| A6b | 6 | attacks/malware | Describe | 011 - Introduction to Computer Security, slide 19; 011 - Introduction to Computer Security, slide 9; 061 - Network Security, slide 3; 062 - Intrusion Detection System, slide 14; 062 - Intrusion Detection System, slide 29 | exact |
| A7a | 2 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 6; 073 - Trusted Computing, slide 8 | exact |
| A7b | 6 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | topic+marks (any command); LOW |
| A8a | 2 | authentication/biometrics | List | 022 - Identification and Authentication, slide 12 | exact |
| A8b | 6 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 16; 022 - Identification and Authentication, slide 19; 022 - Identification and Authentication, slide 24; 041 - Windows Security, slide 2 | exact |
| A9a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 5 | exact |
| A9b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 11; 071 - Ethics and Computer Security, slide 12; 071 - Ethics and Computer Security, slide 6; 071 - Ethics and Computer Security, slide 7 | exact |
| B1a | 5 | risk/management (ethics) | Discuss | 071 - Ethics and Computer Security, slide 3; 071 - Ethics and Computer Security, slide 9 | topic+marks (any command); LOW |
| B2a | 5 | software/OS security | State | 051 - Software Security, slide 21; 051 - Software Security, slide 30 | topic+marks (any command); LOW |
| B2b | 5 | software/OS security | Explain | 041 - Windows Security, slide 21; 041 - Windows Security, slide 4; 041 - Windows Security, slide 6; 051 - Software Security, slide 25 | exact |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| B1b | 5 | risk/management (ethics) | Explain | 7 | B1b point 5: quote is a slide title/short heading, not a supporting passage |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 051 - Software Security s12 |
| A10 | A10a, A10b | 2 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 062 - Intrusion Detection System s32 |
| A2 | A2a | 1 | accepted | no | 031 - Classical Cryptography s4; 031 - Classical Cryptography s25; 031 - Classical Cryptography s14 |
| A3 | A3a, A3b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s18 |
| A4 | A4a, A4b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A5 | A5a, A5b | 2 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| A6 | A6a, A6b | 2 | accepted | no | 011 - Introduction to Computer Security s28; 062 - Intrusion Detection System s14; 062 - Intrusion Detection System s21 |
| A7 | A7a, A7b | 2 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A8 | A8a, A8b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s24; 022 - Identification and Authentication s8 |
| A9 | A9a, A9b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6 |
| B1 | B1a, B1b | 7 | placeholder | no | 071 - Ethics and Computer Security s9; 071 - Ethics and Computer Security s1; 071 - Ethics and Computer Security s3 |
| B2 | B2a, B2b | 2 | accepted | no | 051 - Software Security s30; 051 - Software Security s21; 041 - Windows Security s21 |

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