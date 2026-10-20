# Theory module report

- model: **qwen3.6-flash**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **20** (supported by lecture slides, not lecturer-marked); placeholders: **3**
- source overlap: **0** keys; target 0
- low term-overlap points: **22**; short quotes: **9**; repaired quotes: **5**
- tokens: 105591 prompt + 11433 completion = 117024 across 31 calls
- estimated cost: **$0.0048** (input $0.022/M, output $0.216/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0002**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | authentication/biometrics | List | 072 - Biometrics and Authentication, slide 5 | exact |
| A10b | 6 | authentication/biometrics | Compare | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 7 | topic+marks (any command); LOW |
| A1b | 6 | classical ciphers | Describe | 031 - Classical Cryptography, slide 10; 031 - Classical Cryptography, slide 4 | topic+marks (any command); LOW |
| A2a | 2 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 8 | exact |
| A2b | 6 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A3a | 2 | software/OS security | List | 051 - Software Security, slide 30 | exact |
| A3b | 6 | software/OS security | Describe | 041 - Windows Security, slide 11; 041 - Windows Security, slide 16; 041 - Windows Security, slide 21; 041 - Windows Security, slide 6 | topic+marks (any command); LOW |
| A4a | 2 | access control models | State | 024 - Formal Security Model, slide 5 | exact |
| A4b | 6 | access control models | Explain | 023 - Access Control and Authorization, slide 10; 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 7; 023 - Access Control and Authorization, slide 8 | exact |
| A5a | 2 | attacks/malware | Explain | 051 - Software Security, slide 12 | exact |
| A5b | 6 | attacks/malware | Discuss | 011 - Introduction to Computer Security, slide 10; 011 - Introduction to Computer Security, slide 28; 051 - Software Security, slide 13; 051 - Software Security, slide 2; 051 - Software Security, slide 6; 051 - Software Security, slide 7 | topic+marks (any command); LOW |
| A6a | 2 | attacks/malware | State | 052 - Web Security, slide 13; 052 - Web Security, slide 16 | exact |
| A6b | 6 | attacks/malware | Discuss | 052 - Web Security, slide 14; 052 - Web Security, slide 15 | topic+marks (any command); LOW |
| A7a | 2 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 5 | exact |
| A7b | 6 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 12 | topic+marks (any command); LOW |
| A8a | 2 | attacks/malware | Explain | 062 - Intrusion Detection System, slide 2 | exact |
| A8b | 6 | attacks/malware | State | 011 - Introduction to Computer Security, slide 9; 051 - Software Security, slide 9; 061 - Network Security, slide 26 | exact |
| A9a | 2 | network security | Explain | 062 - Intrusion Detection System, slide 7; 062 - Intrusion Detection System, slide 8 | exact |
| A9b | 6 | network security | Explain | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| B1a | 5 | access control models | State | 023 - Access Control and Authorization, slide 4 | exact |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| B1b | 5 | access control models | Explain | 5 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-51ea8c5d-f4e2-9c3a-baaf-c555baf6329a', 'request_id': '51ea8c5d-f4e2-9c3a-baaf-c555baf6329a'} |
| B2a | 5 | authentication/biometrics | Discuss | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-df90a58c-ad69-9ac4-9893-d4c3083a63d7', 'request_id': 'df90a58c-ad69-9ac4-9893-d4c3083a63d7'} |
| B2b | 5 | authentication/biometrics | Explain | 0 | B2b: Part B scenario (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1b | 1 | accepted | no | 031 - Classical Cryptography s25; 031 - Classical Cryptography s26; 031 - Classical Cryptography s14 |
| A10 | A10a, A10b | 7 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s24; 022 - Identification and Authentication s8 |
| A2 | A2a, A2b | 2 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A3 | A3a, A3b | 2 | accepted | no | 051 - Software Security s30; 051 - Software Security s23; 051 - Software Security s22 |
| A4 | A4a, A4b | 3 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s25; 024 - Formal Security Model s26 |
| A5 | A5a, A5b | 3 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A6 | A6a, A6b | 2 | accepted | no | 052 - Web Security s13; 062 - Intrusion Detection System s21; 051 - Software Security s9 |
| A7 | A7a, A7b | 4 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s7 |
| A8 | A8a, A8b | 2 | accepted | no | 022 - Identification and Authentication s11; 062 - Intrusion Detection System s29; 062 - Intrusion Detection System s14 |
| A9 | A9a, A9b | 3 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 061 - Network Security s3 |
| B1 | B1a, B1b | 5 | placeholder | no | 024 - Formal Security Model s25; 024 - Formal Security Model s26; 023 - Access Control and Authorization s4 |
| B2 | B2a, B2b | 4 | placeholder | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s12; 022 - Identification and Authentication s19 |

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