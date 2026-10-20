# Theory module report

- model: **deepseek-flash**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **24** (supported by lecture slides, not lecturer-marked); placeholders: **0**
- source overlap: **0** keys; target 0
- low stem-overlap points: **29** of 100; initial entailment {'yes': 19, 'partly': 10, 'no': 2}; final accepted entailment {'partly': 10, 'yes': 19}; verbatim-copy rejections: **11**; short quotes: **8**; repaired quotes: **1**
- tokens: 116287 prompt + 12801 completion = 129088 across 65 calls
- estimated cost: **$0.0502** (model deepseek-flash; input $0.3/M, output $1.2/M; official list-price estimate, not an invoice)
- cost per accepted question: **$0.0021**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | attacks/malware | Explain | 062 - Intrusion Detection System, slide 2 | exact |
| A10b | 6 | attacks/malware | State | 011 - Introduction to Computer Security, slide 28; 011 - Introduction to Computer Security, slide 9; 051 - Software Security, slide 6; 061 - Network Security, slide 26 | exact |
| A1a | 2 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 5 | exact |
| A1b | 6 | risk/management (ethics) | Describe | 071 - Ethics and Computer Security, slide 12 | topic+marks (any command); LOW |
| A2a | 2 | network security | List | 062 - Intrusion Detection System, slide 7 | exact |
| A2b | 6 | network security | Explain | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A3a | 2 | access control models | Explain | 024 - Formal Security Model, slide 21; 024 - Formal Security Model, slide 24 | exact |
| A3b | 6 | access control models | Describe | 023 - Access Control and Authorization, slide 10; 023 - Access Control and Authorization, slide 8 | topic+marks (any command); LOW |
| A4a | 2 | trusted computing/blockchain | List | 073 - Trusted Computing, slide 8 | topic+marks (any command); LOW |
| A4b | 6 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A5a | 2 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 8 | exact |
| A5b | 6 | risk/management (ethics) | Compare | 071 - Ethics and Computer Security, slide 11; 071 - Ethics and Computer Security, slide 6 | topic+marks (any command); LOW |
| A6a | 2 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 5 | exact |
| A6b | 6 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 7 | exact |
| A7a | 2 | attacks/malware | State | 051 - Software Security, slide 12 | exact |
| A7b | 6 | attacks/malware | Explain | 051 - Software Security, slide 10; 051 - Software Security, slide 13; 051 - Software Security, slide 7; 051 - Software Security, slide 9 | exact |
| A8a | 2 | attacks/malware | Explain | 011 - Introduction to Computer Security, slide 10 | exact |
| A8b | 6 | attacks/malware | Discuss | 052 - Web Security, slide 13; 052 - Web Security, slide 15 | topic+marks (any command); LOW |
| A9a | 2 | access control models | Explain | 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 4 | exact |
| A9b | 6 | access control models | Discuss | 024 - Formal Security Model, slide 25; 024 - Formal Security Model, slide 26; 024 - Formal Security Model, slide 27; 024 - Formal Security Model, slide 5 | topic+marks (any command); LOW |
| B1a | 5 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 12; 022 - Identification and Authentication, slide 8 | topic+marks (any command); LOW |
| B1b | 5 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 16; 022 - Identification and Authentication, slide 18; 022 - Identification and Authentication, slide 24 | topic+marks (any command); LOW |
| B2a | 5 | software/OS security | Discuss | 051 - Software Security, slide 21; 051 - Software Security, slide 30 | topic+marks (any command); LOW |
| B2b | 5 | software/OS security | State | 041 - Windows Security, slide 11; 041 - Windows Security, slide 21; 041 - Windows Security, slide 6 | topic+marks (any command); LOW |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s7 |
| A10 | A10a, A10b | 1 | accepted | no | 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11; 052 - Web Security s14 |
| A2 | A2a, A2b | 2 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 062 - Intrusion Detection System s32 |
| A3 | A3a, A3b | 2 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| A4 | A4a, A4b | 1 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A5 | A5a, A5b | 2 | accepted | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s6 |
| A6 | A6a, A6b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s24 |
| A7 | A7a, A7b | 1 | accepted | no | 011 - Introduction to Computer Security s28; 011 - Introduction to Computer Security s10; 051 - Software Security s12 |
| A8 | A8a, A8b | 1 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A9 | A9a, A9b | 2 | accepted | no | 024 - Formal Security Model s5; 023 - Access Control and Authorization s18; 023 - Access Control and Authorization s7 |
| B1 | B1a, B1b | 1 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s9; 022 - Identification and Authentication s12 |
| B2 | B2a, B2b | 3 | accepted | no | 051 - Software Security s30; 051 - Software Security s21; 051 - Software Security s3 |

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