# Theory module report

- model: **deepseek-flash**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **19** (supported by lecture slides, not lecturer-marked); placeholders: **2**
- source overlap: **0** keys; target 0
- low stem-overlap points: **21** of 76; initial entailment {'yes': 13, 'partly': 8}; final accepted entailment {'yes': 13, 'partly': 8}; verbatim-copy rejections: **5**; short quotes: **6**; repaired quotes: **0**
- tokens: 98997 prompt + 9946 completion = 108943 across 49 calls
- estimated cost: **$0.0416** (model deepseek-flash; input $0.3/M, output $1.2/M; official list-price estimate, not an invoice)
- cost per accepted question: **$0.0022**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | network security | State | 062 - Intrusion Detection System, slide 7 | topic+marks (any command); LOW |
| A10b | 6 | network security | Explain | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A1b | 6 | classical ciphers | Explain | 031 - Classical Cryptography, slide 14; 031 - Classical Cryptography, slide 4 | topic+marks (any command); LOW |
| A2a | 2 | classical ciphers | Explain | 031 - Classical Cryptography, slide 25 | exact |
| A3a | 2 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 5 | exact |
| A3b | 6 | authentication/biometrics | Describe | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 7 | exact |
| A4a | 2 | access control models | List | 024 - Formal Security Model, slide 5 | topic+marks (any command); LOW |
| A5a | 2 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 8 | exact |
| A5b | 6 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15; 073 - Trusted Computing, slide 6 | exact |
| A6a | 2 | attacks/malware | List | 051 - Software Security, slide 12 | topic+marks (any command); LOW |
| A6b | 6 | attacks/malware | Discuss | 051 - Software Security, slide 10; 051 - Software Security, slide 13; 051 - Software Security, slide 7 | topic+marks (any command); LOW |
| A7a | 2 | attacks/malware | Explain | 011 - Introduction to Computer Security, slide 10 | exact |
| A7b | 6 | attacks/malware | State | 052 - Web Security, slide 13; 052 - Web Security, slide 15; 052 - Web Security, slide 16 | exact |
| A8a | 2 | software/OS security | Explain | 051 - Software Security, slide 21; 051 - Software Security, slide 23 | exact |
| A8b | 6 | software/OS security | Describe | 041 - Windows Security, slide 11; 041 - Windows Security, slide 16; 041 - Windows Security, slide 21 | topic+marks (any command); LOW |
| A9a | 2 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 5 | exact |
| A9b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 11; 071 - Ethics and Computer Security, slide 12 | exact |
| B1a | 5 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 12; 022 - Identification and Authentication, slide 8 | topic+marks (any command); LOW |
| B1b | 5 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 18; 022 - Identification and Authentication, slide 23 | topic+marks (any command); LOW |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| B2a | 5 | access control models | State | 4 | B2a: sub-angle not followed; use one of ['acl', 'acm', 'capability', 'access control list', 'matrix'] |
| B2b | 5 | access control models | Discuss | 0 | B2b: Part B (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1b | 1 | accepted | no | 031 - Classical Cryptography s25; 031 - Classical Cryptography s26; 031 - Classical Cryptography s4 |
| A10 | A10a, A10b | 1 | accepted | no | 061 - Network Security s4; 061 - Network Security s3; 062 - Intrusion Detection System s8 |
| A2 | A2a | 1 | accepted | no | 031 - Classical Cryptography s24; 031 - Classical Cryptography s25; 031 - Classical Cryptography s26 |
| A3 | A3a, A3b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s24 |
| A4 | A4a | 1 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 023 - Access Control and Authorization s18 |
| A5 | A5a, A5b | 1 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A6 | A6a, A6b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 051 - Software Security s12 |
| A7 | A7a, A7b | 3 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A8 | A8a, A8b | 1 | accepted | no | 051 - Software Security s23; 051 - Software Security s30; 041 - Windows Security s21 |
| A9 | A9a, A9b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s7 |
| B1 | B1a, B1b | 1 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s9; 022 - Identification and Authentication s12 |
| B2 | B2a, B2b | 4 | placeholder | no | 024 - Formal Security Model s25; 023 - Access Control and Authorization s7; 024 - Formal Security Model s26 |

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