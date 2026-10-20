# Theory module report

- model: **qwen3.8-flash**; attempt limit: 4 (initial + up to 3 retries)
- accepted questions: **24**; placeholders: **0**
- tokens: 95121 prompt + 10846 completion = 105967 across 27 calls
- estimated cost: **$0.0044** (input $0.022/M, output $0.216/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0002**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 12 | exact |
| A10b | 6 | authentication/biometrics | Describe | 022 - Identification and Authentication, slide 16; 022 - Identification and Authentication, slide 18; 022 - Identification and Authentication, slide 24 | exact |
| A1a | 2 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 6 | exact |
| A1b | 6 | trusted computing/blockchain | Discuss | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A2a | 2 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 5 | exact |
| A2b | 6 | authentication/biometrics | State | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 6 | topic+marks (any command); LOW |
| A3a | 2 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 5 | exact |
| A3b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 12; 071 - Ethics and Computer Security, slide 6 | exact |
| A4a | 2 | attacks/malware | State | 051 - Software Security, slide 12 | exact |
| A4b | 6 | attacks/malware | State | 051 - Software Security, slide 13; 051 - Software Security, slide 7; 051 - Software Security, slide 9; 052 - Web Security, slide 15 | exact |
| A5a | 2 | software/OS security | Explain | 051 - Software Security, slide 23; 051 - Software Security, slide 30 | exact |
| A5b | 6 | software/OS security | Explain | 041 - Windows Security, slide 11; 041 - Windows Security, slide 2; 041 - Windows Security, slide 21; 041 - Windows Security, slide 6 | exact |
| A6a | 2 | attacks/malware | List | 011 - Introduction to Computer Security, slide 10 | topic+marks (any command); LOW |
| A6b | 6 | attacks/malware | Describe | 051 - Software Security, slide 2; 052 - Web Security, slide 13; 052 - Web Security, slide 14; 052 - Web Security, slide 16 | exact |
| A7a | 2 | network security | List | 062 - Intrusion Detection System, slide 7 | exact |
| A7b | 6 | network security | Explain | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A8a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 11 | exact |
| A8b | 6 | risk/management (ethics) | Compare | 071 - Ethics and Computer Security, slide 3; 071 - Ethics and Computer Security, slide 7 | topic+marks (any command); LOW |
| A9a | 2 | access control models | Explain | 024 - Formal Security Model, slide 27; 024 - Formal Security Model, slide 5 | exact |
| A9b | 6 | access control models | Discuss | 023 - Access Control and Authorization, slide 10; 023 - Access Control and Authorization, slide 8 | topic+marks (any command); LOW |
| B1a | 5 | attacks/malware | Discuss | 062 - Intrusion Detection System, slide 14; 062 - Intrusion Detection System, slide 17; 062 - Intrusion Detection System, slide 18; 062 - Intrusion Detection System, slide 2; 062 - Intrusion Detection System, slide 29 | topic+marks (any command); LOW |
| B1b | 5 | attacks/malware | Explain | 011 - Introduction to Computer Security, slide 13; 011 - Introduction to Computer Security, slide 14; 011 - Introduction to Computer Security, slide 9; 051 - Software Security, slide 11; 052 - Web Security, slide 19 | topic+marks (any command); LOW |
| B2a | 5 | access control models | State | 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 4; 023 - Access Control and Authorization, slide 7 | exact |
| B2b | 5 | access control models | Explain | 024 - Formal Security Model, slide 21; 024 - Formal Security Model, slide 24; 024 - Formal Security Model, slide 25; 024 - Formal Security Model, slide 26 | exact |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 2 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A10 | A10a, A10b | 3 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s12; 022 - Identification and Authentication s10 |
| A2 | A2a, A2b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s24 |
| A3 | A3a, A3b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s7 |
| A4 | A4a, A4b | 2 | accepted | no | 011 - Introduction to Computer Security s28; 011 - Introduction to Computer Security s10; 051 - Software Security s12 |
| A5 | A5a, A5b | 2 | accepted | no | 051 - Software Security s23; 051 - Software Security s30; 041 - Windows Security s21 |
| A6 | A6a, A6b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 011 - Introduction to Computer Security s7 |
| A7 | A7a, A7b | 2 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 062 - Intrusion Detection System s32 |
| A8 | A8a, A8b | 2 | accepted | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s8; 071 - Ethics and Computer Security s11 |
| A9 | A9a, A9b | 4 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| B1 | B1a, B1b | 2 | accepted | no | 011 - Introduction to Computer Security s28; 062 - Intrusion Detection System s29; 062 - Intrusion Detection System s14 |
| B2 | B2a, B2b | 2 | accepted | no | 024 - Formal Security Model s25; 024 - Formal Security Model s26; 023 - Access Control and Authorization s4 |

## Deck coverage

- 071 Ethics: {'071 - Ethics and Computer Security': {'slides_with_text': 16, 'chunks': 16, 'chars': 6387}}
- total decks with text: 25; total chunks: 496

## Verification rules applied

- quote must be a verbatim contiguous substring of the cited retrieved chunk (whitespace-normalised); ellipses rejected;
- exactly one marking point per mark;
- near-copy rejected at fuzzy similarity >= 0.80 against all 35 papers;
- command word must appear in the question; dependent (b) must refer back to (a);
- no retrieval evidence => placeholder, never an unsourced answer.