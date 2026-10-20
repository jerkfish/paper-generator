# Theory module report

- model: **deepseek-v4-flash-0731**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **16** (supported by lecture slides, not lecturer-marked); placeholders: **7**
- source overlap: **0** keys; target 0
- low term-overlap points: **10**; short quotes: **5**; repaired quotes: **0**
- tokens: 177040 prompt + 12297 completion = 189337 across 57 calls
- estimated cost: **$0.0679** (input $0.3/M, output $1.2/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0042**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | attacks/malware | List | 062 - Intrusion Detection System, slide 14; 062 - Intrusion Detection System, slide 29 | topic+marks (any command); LOW |
| A1b | 6 | classical ciphers | Explain | 031 - Classical Cryptography, slide 14; 031 - Classical Cryptography, slide 4 | topic+marks (any command); LOW |
| A2a | 2 | network security | State | 062 - Intrusion Detection System, slide 7 | topic+marks (any command); LOW |
| A2b | 6 | network security | Describe | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A3a | 2 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 8 | exact |
| A3b | 6 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A4b | 6 | authentication/biometrics | State | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 6 | topic+marks (any command); LOW |
| A5b | 6 | attacks/malware | Discuss | 051 - Software Security, slide 10; 051 - Software Security, slide 12; 051 - Software Security, slide 13; 051 - Software Security, slide 7 | topic+marks (any command); LOW |
| A6a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 5 | exact |
| A6b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 12 | exact |
| A7a | 2 | access control models | Explain | 024 - Formal Security Model, slide 27; 024 - Formal Security Model, slide 5 | exact |
| A7b | 6 | access control models | Compare | 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 7; 041 - Windows Security, slide 18; 041 - Windows Security, slide 19; 042 - Linux Security, slide 27 | topic+marks (any command); LOW |
| A8a | 2 | software/OS security | Explain | 051 - Software Security, slide 23; 051 - Software Security, slide 30 | exact |
| A8b | 6 | software/OS security | State | 041 - Windows Security, slide 11; 041 - Windows Security, slide 3; 041 - Windows Security, slide 6 | topic+marks (any command); LOW |
| A9a | 2 | attacks/malware | State | 011 - Introduction to Computer Security, slide 10 | exact |
| A9b | 6 | attacks/malware | Describe | 052 - Web Security, slide 13; 052 - Web Security, slide 15 | exact |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| A10b | 6 | attacks/malware | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-fd12aac1-baab-9fe9-a38d-d9a4a9883ae6', 'request_id': 'fd12aac1-baab-9fe9-a38d-d9a4a9883ae6'} |
| A4a | 2 | authentication/biometrics | List | 4 | A4a: near-copy 0.88 of CSC662-2022-02 QA5a; rephrase the scenario and wording |
| A5a | 2 | attacks/malware | Explain | 4 | A5a: question too short (6 words) |
| B1a | 5 | risk/management (ethics) | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-70c10da8-6da9-97cb-ad5b-f21504f49d6f', 'request_id': '70c10da8-6da9-97cb-ad5b-f21504f49d6f'} |
| B1b | 5 | risk/management (ethics) | Explain | 0 | B1b: Part B (a) is unresolved |
| B2a | 5 | authentication/biometrics | State | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-7899b3c8-d403-9d32-a102-5a4c096f6026', 'request_id': '7899b3c8-d403-9d32-a102-5a4c096f6026'} |
| B2b | 5 | authentication/biometrics | Discuss | 0 | B2b: Part B (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1b | 1 | accepted | no | 031 - Classical Cryptography s25; 031 - Classical Cryptography s26; 031 - Classical Cryptography s4 |
| A10 | A10a, A10b | 4 | placeholder | no | 011 - Introduction to Computer Security s28; 062 - Intrusion Detection System s19; 062 - Intrusion Detection System s17 |
| A2 | A2a, A2b | 2 | accepted | no | 061 - Network Security s4; 061 - Network Security s3; 062 - Intrusion Detection System s8 |
| A3 | A3a, A3b | 4 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A4 | A4a, A4b | 4 | placeholder | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s24; 022 - Identification and Authentication s8 |
| A5 | A5a, A5b | 4 | placeholder | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A6 | A6a, A6b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6 |
| A7 | A7a, A7b | 2 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| A8 | A8a, A8b | 2 | accepted | no | 051 - Software Security s23; 051 - Software Security s30; 041 - Windows Security s21 |
| A9 | A9a, A9b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 051 - Software Security s6 |
| B1 | B1a, B1b | 4 | placeholder | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s6 |
| B2 | B2a, B2b | 4 | placeholder | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s12; 022 - Identification and Authentication s10 |

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