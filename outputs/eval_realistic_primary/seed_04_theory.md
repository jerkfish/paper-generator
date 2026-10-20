# Theory module report

- model: **deepseek-v4-flash-0731**; attempt limit: 4 (initial + up to 3 retries)
- accepted theory answers: **18** (supported by lecture slides, not lecturer-marked); placeholders: **6**
- source overlap: **0** keys; target 0
- low term-overlap points: **17**; short quotes: **2**; repaired quotes: **0**
- tokens: 165868 prompt + 11139 completion = 177007 across 63 calls
- estimated cost: **$0.0631** (input $0.3/M, output $1.2/M; public qwen-flash list-price estimate, not an invoice)
- cost per accepted question: **$0.0035**

## Accepted questions

| Slot | Marks | Topic | Command | Sources | Style |
|---|---:|---|---|---|---|
| A10a | 2 | attacks/malware | List | 062 - Intrusion Detection System, slide 17; 062 - Intrusion Detection System, slide 29 | topic+marks (any command); LOW |
| A1a | 2 | attacks/malware | Explain | 051 - Software Security, slide 12; 051 - Software Security, slide 13 | exact |
| A1b | 6 | attacks/malware | Explain | 051 - Software Security, slide 10; 051 - Software Security, slide 6; 051 - Software Security, slide 7; 051 - Software Security, slide 9 | exact |
| A2b | 6 | risk/management (ethics) | Describe | 071 - Ethics and Computer Security, slide 12 | topic+marks (any command); LOW |
| A3a | 2 | authentication/biometrics | Explain | 072 - Biometrics and Authentication, slide 5 | exact |
| A3b | 6 | authentication/biometrics | State | 072 - Biometrics and Authentication, slide 4 | topic+marks (any command); LOW |
| A4a | 2 | attacks/malware | State | 011 - Introduction to Computer Security, slide 10 | exact |
| A4b | 6 | attacks/malware | Explain | 052 - Web Security, slide 13; 052 - Web Security, slide 15 | exact |
| A5a | 2 | risk/management (ethics) | Explain | 071 - Ethics and Computer Security, slide 11 | exact |
| A5b | 6 | risk/management (ethics) | Discuss | 071 - Ethics and Computer Security, slide 5; 071 - Ethics and Computer Security, slide 6; 071 - Ethics and Computer Security, slide 7 | exact |
| A6a | 2 | access control models | Explain | 024 - Formal Security Model, slide 25; 024 - Formal Security Model, slide 26 | exact |
| A6b | 6 | access control models | Compare | 023 - Access Control and Authorization, slide 18; 023 - Access Control and Authorization, slide 7; 041 - Windows Security, slide 18; 041 - Windows Security, slide 19; 042 - Linux Security, slide 27 | topic+marks (any command); LOW |
| A7a | 2 | access control models | Explain | 023 - Access Control and Authorization, slide 4 | exact |
| A7b | 6 | access control models | State | 024 - Formal Security Model, slide 21; 024 - Formal Security Model, slide 27; 024 - Formal Security Model, slide 5 | topic+marks (any command); LOW |
| A8a | 2 | trusted computing/blockchain | State | 073 - Trusted Computing, slide 8 | exact |
| A8b | 6 | trusted computing/blockchain | Explain | 073 - Trusted Computing, slide 13; 073 - Trusted Computing, slide 14; 073 - Trusted Computing, slide 15 | exact |
| A9a | 2 | software/OS security | List | 051 - Software Security, slide 30 | exact |
| A9b | 6 | software/OS security | Discuss | 041 - Windows Security, slide 11; 041 - Windows Security, slide 21 | topic+marks (any command); LOW |

## Placeholders

| Slot | Marks | Topic | Command | Attempts | Reason |
|---|---:|---|---|---:|---|
| A10b | 6 | attacks/malware | Describe | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-31ce9ca7-c272-90d4-8943-9c0142b6c7ea', 'request_id': '31ce9ca7-c272-90d4-8943-9c0142b6c7ea'} |
| A2a | 2 | risk/management (ethics) | State | 4 | A2a: question too short (7 words) |
| B1a | 5 | authentication/biometrics | Discuss | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-e897965a-c817-9df4-8b86-0bc9f37b34f5', 'request_id': 'e897965a-c817-9df4-8b86-0bc9f37b34f5'} |
| B1b | 5 | authentication/biometrics | Explain | 0 | B1b: Part B (a) is unresolved |
| B2a | 5 | network security | Explain | 4 | LLM/API error: LLM call failed after 3 tries: Error code: 403 - {'error': {'message': 'The free quota has been exhausted. To continue accessing the model on a paid basis, please complete your payment information （or disable the "use free tier only" mode in the management console if already completed).', 'type': 'AllocationQuota.FreeTierOnly', 'param': None, 'code': 'AllocationQuota.FreeTierOnly'}, 'id': 'chatcmpl-68300d3c-6b06-9b89-a6f9-617c69bf7b83', 'request_id': '68300d3c-6b06-9b89-a6f9-617c69bf7b83'} |
| B2b | 5 | network security | State | 0 | B2b: Part B (a) is unresolved |

## Group attempts and retrieval

| Question | Slots | Attempts | Result | Fallback retrieval | Top sources |
|---|---|---:|---|---|---|
| A1 | A1a, A1b | 2 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 022 - Identification and Authentication s11 |
| A10 | A10a, A10b | 4 | placeholder | no | 011 - Introduction to Computer Security s28; 062 - Intrusion Detection System s19; 062 - Intrusion Detection System s17 |
| A2 | A2a, A2b | 4 | placeholder | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s11; 071 - Ethics and Computer Security s7 |
| A3 | A3a, A3b | 3 | accepted | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s8; 022 - Identification and Authentication s24 |
| A4 | A4a, A4b | 1 | accepted | no | 011 - Introduction to Computer Security s10; 011 - Introduction to Computer Security s28; 052 - Web Security s13 |
| A5 | A5a, A5b | 2 | accepted | no | 071 - Ethics and Computer Security s5; 071 - Ethics and Computer Security s7; 071 - Ethics and Computer Security s6 |
| A6 | A6a, A6b | 2 | accepted | no | 024 - Formal Security Model s5; 024 - Formal Security Model s21; 024 - Formal Security Model s27 |
| A7 | A7a, A7b | 1 | accepted | no | 024 - Formal Security Model s5; 023 - Access Control and Authorization s4; 024 - Formal Security Model s21 |
| A8 | A8a, A8b | 2 | accepted | no | 073 - Trusted Computing s8; 073 - Trusted Computing s6; 073 - Trusted Computing s14 |
| A9 | A9a, A9b | 2 | accepted | no | 051 - Software Security s30; 051 - Software Security s23; 051 - Software Security s22 |
| B1 | B1a, B1b | 4 | placeholder | no | 022 - Identification and Authentication s16; 022 - Identification and Authentication s12; 022 - Identification and Authentication s19 |
| B2 | B2a, B2b | 4 | placeholder | no | 061 - Network Security s4; 061 - Network Security s16; 062 - Intrusion Detection System s7 |

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