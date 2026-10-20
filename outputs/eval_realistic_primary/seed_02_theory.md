# Theory module report

- model: **deepseek-v4-flash-0731**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **17** (supported by lecture slides, not lecturer-marked); placeholders: **7**
- source overlap: **0** keys; target 0
- low term-overlap points: **10**; short quotes: **9**; repaired quotes: **1**
- tokens: 141806 prompt + 12207 completion = 154013 across 55 calls
- estimated cost: **$0.0572** (input $0.3/M, output $1.2/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0034**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A1a | 2 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 8 | exact |
| A1b | 6 | trusted computing/blockchain | Discuss | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A2a | 2 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 5 | exact |
| A2b | 6 | authentication/biometrics | State | 072 - Biometrics and Authentication, slide 10; 072 - Biometrics and Authentication, slide 4; 072 - Biometrics and Authentication, slide 6 | topic+marks (any command); LOW |
| A3a | 2 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 5 | exact |
| A3b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 12 | exact |
| A4a | 2 | attacks/malware | State | 051 - Software Security, slide 12 | exact |
| A4b | 6 | attacks/malware | State | 051 - Software Security, slide 10; 051 - Software Security, slide 7; 051 - Software Security, slide 9; 052 - Web Security, slide 15; 052 - Web Security, slide 16 | exact |
| A5a | 2 | software/OS security | Explain | 051 - Software Security, slide 23; 051 - Software Security, slide 30 | exact |
| A5b | 6 | software/OS security | Explain | 041 - Windows Security, slide 11; 041 - Windows Security, slide 2; 041 - Windows Security, slide 21; 041 - Windows Security, slide 4; 041 - Windows Security, slide 6 | exact |
| A6a | 2 | attacks/malware | List | 051 - Software Security, slide 13 | topic+marks (any command); LOW |
| A6b | 6 | attacks/malware | Describe | 011 - Introduction to Computer Security, slide 10; 051 - Software Security, slide 2; 052 - Web Security, slide 13; 052 - Web Security, slide 14 | exact |
| A7a | 2 | network security | List | 062 - Intrusion Detection System, slide 7 | exact |
| A7b | 6 | network security | Explain | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | exact |
| A8a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 11 | exact |
| A8b | 6 | risk/management (ethics) | Compare | 071 - Ethics and Computer Security, slide 6; 071 - Ethics and Computer Security, slide 7 | topic+marks (any command); LOW |
| A9a | 2 | access control models | Explain | 024 - Formal Security Model, slide 25; 024 - Formal Security Model, slide 26 | exact |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| A10a | 2 | authentication/biometrics | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-7625fb7b-fced-9060-bf54-80225f2ebadc', 'request_id': '7625fb7b-fced-9060-bf54-80225f2ebadc'} |
| A10b | 6 | authentication/biometrics | Describe | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-87bc6079-9dc0-9b0e-8bb5-09a2080311a5', 'request_id': '87bc6079-9dc0-9b0e-8bb5-09a2080311a5'} |
| A9b | 6 | access control models | Discuss | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-5d7b8cb9-d40e-9211-9efe-535f7c7083bd', 'request_id': '5d7b8cb9-d40e-9211-9efe-535f7c7083bd'} |
| B1a | 5 | attacks/malware | Discuss | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-3a06d7e0-a22a-914b-8ae9-3ca7f47dc09c', 'request_id': '3a06d7e0-a22a-914b-8ae9-3ca7f47dc09c'} |
| B1b | 5 | attacks/malware | Explain | 0 | B1b: Part B (a) is unresolved |
| B2a | 5 | access control models | State | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-285c7850-2b06-9d31-ae1c-b501bfb5b756', 'request_id': '285c7850-2b06-9d31-ae1c-b501bfb5b756'} |
| B2b | 5 | access control models | Explain | 0 | B2b: Part B (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 3 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A10 | A10a, A10b | 4 | placeholder | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s12; 022 - Identification and Authentication s10 |
| A2 | A2a, A2b | 2 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s24 |
| A3 | A3a, A3b | 4 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s7 |
| A4 | A4a, A4b | 2 | accepted | no | 011 - Introduction to Computer Security s28; 011 - Introduction to Computer Security s10; 051 - Software Security s12 |
| A5 | A5a, A5b | 2 | accepted | no | 051 - Software Security s23; 051 - Software Security s30; 041 - Windows Security s21 |
| A6 | A6a, A6b | 1 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 011 - Introduction to Computer Security s7 |
| A7 | A7a, A7b | 4 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 062 - Intrusion Detection System s32 |
| A8 | A8a, A8b | 3 | accepted | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6; 071 - Ethics and Computer Security s8 |
| A9 | A9a, A9b | 4 | placeholder | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| B1 | B1a, B1b | 4 | placeholder | no | 011 - Introduction to Computer Security s28; 062 - Intrusion Detection System s29; 062 - Intrusion Detection System s14 |
| B2 | B2a, B2b | 4 | placeholder | no | 024 - Formal Security Model s5; 023 - Access Control and Authorization s4; 024 - Formal Security Model s27 |

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