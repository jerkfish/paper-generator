# Theory module report

- model: **qwen3.7-flash**; attempt limit: 4 (initial + up to 3 retries)
- accepted questions: **23**; placeholders: **0**
- tokens: 122486 prompt + 36446 completion = 158932 across 60 calls
- estimated cost: **$0.0106** (input $0.022/M, output $0.216/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0005**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | access control models | Explain | 023 - Access Control and Authorization, slide 4 | exact |
| A10b | 6 | access control models | Explain | 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 7 | exact |
| A1a | 2 | network security | Explain | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A1b | 6 | network security | Explain | 062 - Intrusion Detection System, slide 5; 062 - Intrusion Detection System, slide 8 | exact |
| A2a | 2 | classical ciphers | List | 031 - Classical Cryptography, slide 14 | topic+marks (any command); LOW |
| A3a | 2 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 6 | exact |
| A3b | 6 | trusted computing/blockchain | Justify | 073 - Trusted Computing, slide 6; 073 - Trusted Computing, slide 8 | topic+marks (any command); LOW |
| A4a | 2 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 16 | exact |
| A4b | 6 | authentication/biometrics | Discuss | 022 - Identification and Authentication, slide 24; 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 5; 072 - Biometrics and Authentication, slide 6 | exact |
| A5a | 2 | software/OS security | State | 051 - Software Security, slide 30 | topic+marks (any command); LOW |
| A5b | 6 | software/OS security | Describe | 041 - Windows Security, slide 2 | topic+marks (any command); LOW |
| A6a | 2 | attacks/malware | List | 011 - Introduction to Computer Security, slide 10 | topic+marks (any command); LOW |
| A6b | 6 | attacks/malware | Describe | 022 - Identification and Authentication, slide 11 | exact |
| A7a | 2 | access control models | Explain | 024 - Formal Security Model, slide 5 | exact |
| A7b | 6 | access control models | State | 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 4 | topic+marks (any command); LOW |
| A8a | 2 | attacks/malware | State | 051 - Software Security, slide 12 | exact |
| A8b | 6 | attacks/malware | State | 051 - Software Security, slide 12; 051 - Software Security, slide 2 | exact |
| A9a | 2 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 19; 022 - Identification and Authentication, slide 8 | exact |
| A9b | 6 | authentication/biometrics | Discuss | 022 - Identification and Authentication, slide 16; 022 - Identification and Authentication, slide 18; 042 - Linux Security, slide 8 | exact |
| B1a | 5 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 5; 071 - Ethics and Computer Security, slide 6 | topic+marks (any command); LOW |
| B1b | 5 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 6; 071 - Ethics and Computer Security, slide 7 | topic+marks (any command); LOW |
| B2a | 5 | attacks/malware | Explain | 051 - Software Security, slide 12 | topic+marks (any command); LOW |
| B2b | 5 | attacks/malware | Discuss | 052 - Web Security, slide 13; 052 - Web Security, slide 14 | topic+marks (any command); LOW |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 4 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 062 - Intrusion Detection System s7 |
| A10 | A10a, A10b | 2 | accepted | no | 024 - Formal Security Model s5; 023 - Access Control and Authorization s18; 023 - Access Control and Authorization s7 |
| A2 | A2a | 1 | accepted | no | 031 - Classical Cryptography s25; 031 - Classical Cryptography s26; 031 - Classical Cryptography s14 |
| A3 | A3a, A3b | 3 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s15 |
| A4 | A4a, A4b | 4 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s24 |
| A5 | A5a, A5b | 2 | accepted | no | 051 - Software Security s22; 051 - Software Security s23; 041 - Windows Security s2 |
| A6 | A6a, A6b | 3 | accepted | no | 011 - Introduction to Computer Security s10; 022 - Identification and Authentication s11; 051 - Software Security s12 |
| A7 | A7a, A7b | 2 | accepted | no | 024 - Formal Security Model s5; 023 - Access Control and Authorization s18; 023 - Access Control and Authorization s7 |
| A8 | A8a, A8b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 022 - Identification and Authentication s11; 051 - Software Security s12 |
| A9 | A9a, A9b | 1 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s19; 022 - Identification and Authentication s8 |
| B1 | B1a, B1b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s6; 071 - Ethics and Computer Security s7 |
| B2 | B2a, B2b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 022 - Identification and Authentication s11; 051 - Software Security s12 |

## Deck coverage

- 071 Ethics: {'071 - Ethics and Computer Security': {'slides_with_text': 16, 'chunks': 16, 'chars': 6387}}
- total decks with text: 25; total chunks: 496

## Verification rules applied

- quote must be a verbatim contiguous substring of the cited retrieved chunk (whitespace-normalised); ellipses rejected;
- exactly one marking point per mark;
- near-copy rejected at fuzzy similarity >= 0.80 against all 35 papers;
- command word must appear in the question; dependent (b) must refer back to (a);
- no retrieval evidence => placeholder, never an unsourced answer.