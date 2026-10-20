# Theory module report

- model: **deepseek-v4-flash-0731**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **20** (supported by lecture slides, not lecturer-marked); placeholders: **4**
- source overlap: **0** keys; target 0
- low term-overlap points: **11**; short quotes: **6**; repaired quotes: **0**
- tokens: 168360 prompt + 11744 completion = 180104 across 58 calls
- estimated cost: **$0.0646** (input $0.3/M, output $1.2/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0032**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 11 | exact |
| A10b | 6 | risk/management (ethics) | Discuss | 071 - Ethics and Computer Security, slide 6; 071 - Ethics and Computer Security, slide 7 | exact |
| A1a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 5 | exact |
| A1b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 12 | exact |
| A2a | 2 | access control models | State | 024 - Formal Security Model, slide 5 | exact |
| A2b | 6 | access control models | Explain | 023 - Access Control and Authorization, slide 10; 023 - Access Control and Authorization, slide 7; 023 - Access Control and Authorization, slide 8; 042 - Linux Security, slide 27 | exact |
| A3a | 2 | software/OS security | State | 051 - Software Security, slide 30 | topic+marks (any command); LOW |
| A3b | 6 | software/OS security | Explain | 041 - Windows Security, slide 11; 041 - Windows Security, slide 2; 041 - Windows Security, slide 21; 041 - Windows Security, slide 4; 041 - Windows Security, slide 6 | exact |
| A4a | 2 | authentication/biometrics | List | 072 - Biometrics and Authentication, slide 5 | exact |
| A4b | 6 | authentication/biometrics | Discuss | 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 9 | exact |
| A5a | 2 | authentication/biometrics | State | 022 - Identification and Authentication, slide 12 | exact |
| A5b | 6 | authentication/biometrics | State | 022 - Identification and Authentication, slide 18; 022 - Identification and Authentication, slide 23 | topic+marks (any command); LOW |
| A6a | 2 | attacks/malware | Explain | 051 - Software Security, slide 12 | exact |
| A6b | 6 | attacks/malware | Discuss | 051 - Software Security, slide 10; 051 - Software Security, slide 13; 051 - Software Security, slide 7; 052 - Web Security, slide 13 | topic+marks (any command); LOW |
| A7a | 2 | access control models | List | 023 - Access Control and Authorization, slide 4 | topic+marks (any command); LOW |
| A7b | 6 | access control models | Describe | 024 - Formal Security Model, slide 21; 024 - Formal Security Model, slide 25; 024 - Formal Security Model, slide 26; 024 - Formal Security Model, slide 27 | topic+marks (any command); LOW |
| A8a | 2 | attacks/malware | Explain | 011 - Introduction to Computer Security, slide 10 | exact |
| A8b | 6 | attacks/malware | State | 052 - Web Security, slide 14; 052 - Web Security, slide 15 | exact |
| A9a | 2 | network security | Explain | 062 - Intrusion Detection System, slide 7 | exact |
| A9b | 6 | network security | Describe | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| B1a | 5 | trusted computing/blockchain | State | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-0c85ee33-aaa8-948f-b0f0-ef87e48fe1d5', 'request_id': '0c85ee33-aaa8-948f-b0f0-ef87e48fe1d5'} |
| B1b | 5 | trusted computing/blockchain | Discuss | 0 | B1b: Part B (a) is unresolved |
| B2a | 5 | attacks/malware | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-c8384b68-02f0-9298-b8ec-729fb67f1866', 'request_id': 'c8384b68-02f0-9298-b8ec-729fb67f1866'} |
| B2b | 5 | attacks/malware | Explain | 0 | B2b: Part B (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6 |
| A10 | A10a, A10b | 1 | accepted | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6; 071 - Ethics and Computer Security s8 |
| A2 | A2a, A2b | 2 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s25; 024 - Formal Security Model s26 |
| A3 | A3a, A3b | 2 | accepted | no | 051 - Software Security s30; 051 - Software Security s3; 042 - Linux Security s26 |
| A4 | A4a, A4b | 3 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s24; 022 - Identification and Authentication s8 |
| A5 | A5a, A5b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s19; 022 - Identification and Authentication s18 |
| A6 | A6a, A6b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A7 | A7a, A7b | 2 | accepted | no | 023 - Access Control and Authorization s18; 023 - Access Control and Authorization s4; 024 - Formal Security Model s21 |
| A8 | A8a, A8b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A9 | A9a, A9b | 2 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 061 - Network Security s3 |
| B1 | B1a, B1b | 4 | placeholder | no | 073 - Trusted Computing s8; 073 - Trusted Computing s14; 073 - Trusted Computing s6 |
| B2 | B2a, B2b | 4 | placeholder | no | 011 - Introduction to Computer Security s28; 062 - Intrusion Detection System s19; 062 - Intrusion Detection System s29 |

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