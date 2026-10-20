# Theory module report

- model: **deepseek-v4-flash-0731**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **17** (supported by lecture slides, not lecturer-marked); placeholders: **7**
- source overlap: **0** keys; target 0
- low term-overlap points: **10**; short quotes: **9**; repaired quotes: **3**
- tokens: 179236 prompt + 12348 completion = 191584 across 56 calls
- estimated cost: **$0.0686** (input $0.3/M, output $1.2/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0040**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A1a | 2 | software/OS security | State | 051 - Software Security, slide 30 | topic+marks (any command); LOW |
| A1b | 6 | software/OS security | Explain | 041 - Windows Security, slide 11; 041 - Windows Security, slide 21; 041 - Windows Security, slide 4; 041 - Windows Security, slide 6 | exact |
| A2a | 2 | attacks/malware | Explain | 051 - Software Security, slide 12; 051 - Software Security, slide 13 | exact |
| A2b | 6 | attacks/malware | Explain | 051 - Software Security, slide 10; 051 - Software Security, slide 6; 051 - Software Security, slide 7; 051 - Software Security, slide 9; 052 - Web Security, slide 15 | exact |
| A3a | 2 | attacks/malware | Explain | 011 - Introduction to Computer Security, slide 10; 011 - Introduction to Computer Security, slide 7 | exact |
| A3b | 6 | attacks/malware | Discuss | 051 - Software Security, slide 2; 052 - Web Security, slide 13; 052 - Web Security, slide 16 | topic+marks (any command); LOW |
| A4a | 2 | network security | State | 062 - Intrusion Detection System, slide 7 | topic+marks (any command); LOW |
| A4b | 6 | network security | Explain | 061 - Network Security, slide 26; 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A5a | 2 | access control models | List | 024 - Formal Security Model, slide 5 | topic+marks (any command); LOW |
| A5b | 6 | access control models | Discuss | 023 - Access Control and Authorization, slide 10; 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 7; 023 - Access Control and Authorization, slide 8; 041 - Windows Security, slide 18; 042 - Linux Security, slide 27 | topic+marks (any command); LOW |
| A6a | 2 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 8 | exact |
| A6b | 6 | trusted computing/blockchain | Describe | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A7a | 2 | authentication/biometrics | List | 072 - Biometrics and Authentication, slide 5 | exact |
| A7b | 6 | authentication/biometrics | State | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 2; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 6 | topic+marks (any command); LOW |
| A8a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 5 | exact |
| A8b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 12 | exact |
| A9a | 2 | authentication/biometrics | Explain | 022 - Identification and Authentication, slide 12 | exact |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| A10a | 2 | attacks/malware | State | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-6de7fd91-3f80-9725-a343-74f50ced4a2c', 'request_id': '6de7fd91-3f80-9725-a343-74f50ced4a2c'} |
| A10b | 6 | attacks/malware | Compare | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-2e5d6329-100c-969f-b853-3792c92f2fa6', 'request_id': '2e5d6329-100c-969f-b853-3792c92f2fa6'} |
| A9b | 6 | authentication/biometrics | State | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-72a704f8-3f7b-91d1-9155-bd6d44db5a41', 'request_id': '72a704f8-3f7b-91d1-9155-bd6d44db5a41'} |
| B1a | 5 | access control models | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-0250cbc7-385e-9576-a366-f664a8dbdb6e', 'request_id': '0250cbc7-385e-9576-a366-f664a8dbdb6e'} |
| B1b | 5 | access control models | State | 0 | B1b: Part B (a) is unresolved |
| B2a | 5 | risk/management (ethics) | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-390a09eb-b27c-921e-9221-92343a7dbf1a', 'request_id': '390a09eb-b27c-921e-9221-92343a7dbf1a'} |
| B2b | 5 | risk/management (ethics) | Discuss | 0 | B2b: Part B (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 2 | accepted | no | 051 - Software Security s30; 051 - Software Security s3; 042 - Linux Security s26 |
| A10 | A10a, A10b | 4 | placeholder | no | 011 - Introduction to Computer Security s28; 062 - Intrusion Detection System s14; 062 - Intrusion Detection System s21 |
| A2 | A2a, A2b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A3 | A3a, A3b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A4 | A4a, A4b | 2 | accepted | no | 061 - Network Security s4; 061 - Network Security s3; 062 - Intrusion Detection System s8 |
| A5 | A5a, A5b | 4 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 023 - Access Control and Authorization s18 |
| A6 | A6a, A6b | 1 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A7 | A7a, A7b | 4 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s24; 022 - Identification and Authentication s8 |
| A8 | A8a, A8b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6 |
| A9 | A9a, A9b | 4 | placeholder | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s12; 022 - Identification and Authentication s10 |
| B1 | B1a, B1b | 4 | placeholder | no | 023 - Access Control and Authorization s4; 024 - Formal Security Model s25; 024 - Formal Security Model s27 |
| B2 | B2a, B2b | 4 | placeholder | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s6 |

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