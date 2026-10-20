# Theory module report

- model: **deepseek-v4-flash-0731**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **17** (supported by lecture slides, not lecturer-marked); placeholders: **7**
- source overlap: **0** keys; target 0
- low term-overlap points: **17**; short quotes: **7**; repaired quotes: **1**
- tokens: 155298 prompt + 10665 completion = 165963 across 64 calls
- estimated cost: **$0.0594** (input $0.3/M, output $1.2/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0035**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A1a | 2 | attacks/malware | State | 051 - Software Security, slide 12 | exact |
| A1b | 6 | attacks/malware | State | 051 - Software Security, slide 10; 051 - Software Security, slide 7; 051 - Software Security, slide 9; 052 - Web Security, slide 16; 052 - Web Security, slide 19 | exact |
| A2a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 5 | exact |
| A2b | 6 | risk/management (ethics) | Discuss | 071 - Ethics and Computer Security, slide 12 | exact |
| A3a | 2 | risk/management (ethics) | State | 071 - Ethics and Computer Security, slide 11 | exact |
| A3b | 6 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 6; 071 - Ethics and Computer Security, slide 7 | exact |
| A4a | 2 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 8 | exact |
| A4b | 6 | trusted computing/blockchain | Describe | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A5a | 2 | access control models | State | 024 - Formal Security Model, slide 21; 024 - Formal Security Model, slide 5 | exact |
| A6a | 2 | software/OS security | List | 051 - Software Security, slide 30 | exact |
| A6b | 6 | software/OS security | Compare | 041 - Windows Security, slide 11; 041 - Windows Security, slide 4; 041 - Windows Security, slide 6; 042 - Linux Security, slide 19; 042 - Linux Security, slide 23; 042 - Linux Security, slide 28 | topic+marks (any command); LOW |
| A7a | 2 | network security | List | 062 - Intrusion Detection System, slide 7 | exact |
| A7b | 6 | network security | Discuss | 061 - Network Security, slide 3; 061 - Network Security, slide 4 | topic+marks (any command); LOW |
| A8a | 2 | attacks/malware | Explain | 051 - Software Security, slide 13 | exact |
| A8b | 6 | attacks/malware | Explain | 052 - Web Security, slide 13; 052 - Web Security, slide 15 | exact |
| A9a | 2 | attacks/malware | Explain | 062 - Intrusion Detection System, slide 17; 062 - Intrusion Detection System, slide 29 | exact |
| A9b | 6 | attacks/malware | State | 011 - Introduction to Computer Security, slide 10; 011 - Introduction to Computer Security, slide 28; 011 - Introduction to Computer Security, slide 9 | exact |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| A10a | 2 | authentication/biometrics | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-c4163251-df71-9931-8f16-7a1713c6ef8b', 'request_id': 'c4163251-df71-9931-8f16-7a1713c6ef8b'} |
| A10b | 6 | authentication/biometrics | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-91d58d7b-e867-922a-a951-80a100eae169', 'request_id': '91d58d7b-e867-922a-a951-80a100eae169'} |
| A5b | 6 | access control models | Describe | 4 | A5b: sub-angle not followed; use one of ['acl', 'acm', 'capability', 'access control list', 'matrix'] |
| B1a | 5 | access control models | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-c806a90a-6435-9be6-8a55-35114c5529b7', 'request_id': 'c806a90a-6435-9be6-8a55-35114c5529b7'} |
| B1b | 5 | access control models | Discuss | 0 | B1b: Part B (a) is unresolved |
| B2a | 5 | authentication/biometrics | State | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-77635e0d-5da5-914e-b0af-9ce1511682ac', 'request_id': '77635e0d-5da5-914e-b0af-9ce1511682ac'} |
| B2b | 5 | authentication/biometrics | Explain | 0 | B2b: Part B (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 1 | accepted | no | 011 - Introduction to Computer Security s28; 011 - Introduction to Computer Security s10; 051 - Software Security s12 |
| A10 | A10a, A10b | 4 | placeholder | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s24 |
| A2 | A2a, A2b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6 |
| A3 | A3a, A3b | 2 | accepted | no | 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s6 |
| A4 | A4a, A4b | 1 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A5 | A5a, A5b | 4 | placeholder | no | 024 - Formal Security Model s5; 024 - Formal Security Model s25; 024 - Formal Security Model s26 |
| A6 | A6a, A6b | 1 | accepted | no | 051 - Software Security s30; 051 - Software Security s23; 051 - Software Security s22 |
| A7 | A7a, A7b | 1 | accepted | no | 061 - Network Security s4; 062 - Intrusion Detection System s8; 062 - Intrusion Detection System s32 |
| A8 | A8a, A8b | 1 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A9 | A9a, A9b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| B1 | B1a, B1b | 4 | placeholder | no | 023 - Access Control and Authorization s4; 023 - Access Control and Authorization s18; 023 - Access Control and Authorization s7 |
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