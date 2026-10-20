# Planner slot table

- mode: **realistic**; style: **modern**; seed: 9
- computed marks: **6**; clean-modern distribution: [0, 0, 0, 0, 0, 2, 6, 6, 12, 14] (mean 4.0)
- clean modern papers: 10

| Computed marks | 0 | 2 | 6 | 12 | 14 |
|---|---:|---:|---:|---:|---:|
| clean papers | 5 | 1 | 2 | 1 | 1 |

## Slots

| Slot | Marks | Kind | Topic | Task | Computed type | Target size / key | Style examples n | Notes |
|---|---:|---|---|---|---|---|---:|---|
| A1a | 2 | theory | attacks/malware | define/explain |  |  | 9 | theory slot; style n=9 |
| A1b | 6 | theory | attacks/malware | scenario/justify |  |  | 5 | theory slot; style n=5 |
| A2a | 2 | theory | attacks/malware | define/explain |  |  | 9 | theory slot; style n=9 |
| A2b | 6 | computed | classical ciphers | compute | Vigenere | 13-18 letters; keyword 6-8 letters |  | computed slot |
| A3a | 2 | theory | attacks/malware | list/enumerate |  |  | 3 | theory slot; style n=3 |
| A3b | 6 | theory | authentication/biometrics | short objective |  |  | 12 | theory slot; style n=12 |
| A4a | 2 | theory | attacks/malware | short objective |  |  | 9 | theory slot; style n=9 |
| A4b | 6 | theory | attacks/malware | short objective |  |  | 14 | theory slot; style n=14 |
| A5a | 2 | theory | access control models | define/explain |  |  | 3 | theory slot; style n=3 |
| A5b | 6 | theory | authentication/biometrics | short objective |  |  | 12 | theory slot; style n=12 |
| A6a | 2 | theory | access control models | define/explain |  |  | 3 | theory slot; style n=3 |
| A6b | 6 | theory | attacks/malware | short objective |  |  | 14 | theory slot; style n=14 |
| A7a | 2 | theory | access control models | define/explain |  |  | 3 | theory slot; style n=3 |
| A7b | 6 | theory | trusted computing/blockchain | short objective |  |  | 7 | theory slot; style n=7 |
| A8a | 2 | theory | access control models | define/explain |  |  | 3 | theory slot; style n=3 |
| A8b | 6 | theory | authentication/biometrics | short objective |  |  | 12 | theory slot; style n=12 |
| A9a | 2 | theory | network security | list/enumerate |  |  | 3 | theory slot; style n=3 |
| A9b | 6 | theory | access control models | compare |  |  | 2 | theory slot; style n=2 (widened 2) |
| A10a | 2 | theory | software/OS security | list/enumerate |  |  | 4 | theory slot; style n=4 |
| A10b | 6 | theory | network security | short objective |  |  | 4 | theory slot; style n=4 |
| B1a | 5 | theory | attacks/malware | define/explain |  |  | 4 | theory slot; style n=4 |
| B1b | 5 | theory | trusted computing/blockchain | define/explain |  |  | 3 | theory slot; style n=3 |
| B2a | 5 | theory | software/OS security | define/explain |  |  | 2 | theory slot; style n=2 (widened 2) |
| B2b | 5 | theory | authentication/biometrics | define/explain |  |  | 2 | theory slot; style n=2 (widened 4) |

## Theory topic marks (assigned vs modern-share target)

| Topic | Assigned | Target | Modern weight |
|---|---:|---:|---:|
| attacks/malware | 31 | 32 | 0.342 |
| authentication/biometrics | 23 | 21 | 0.223 |
| access control models | 14 | 16 | 0.173 |
| trusted computing/blockchain | 11 | 11 | 0.113 |
| software/OS security | 7 | 6 | 0.068 |
| network security | 8 | 8 | 0.080 |

## Calibration used for computed sizes

| Type | Marks | n | Length range | Key | Working steps | Note |
|---|---:|---:|---|---|---|---|
| caesar | 2 | 1 | not printed (word) | shift 4 | word length | n=1 at 2m; widened 2-6m gives n=4, lengths 11-24 |
| caesar | 6 | 2 | 11-38 | shift 7/18 | 11-38 mappings | n=2 at 6m; widened 4-6m gives n=3, lengths 11-38 |
| vigenere | 6 | 1 | 13 | table/keyword | 13 table lookups | n=1 at 6m; widened 3-10m gives n=3, lengths 13-18 |
| columnar_3x4 | 2-6 | 3 | 21-30 | 4-5 columns / keyword | columns + rows | slide 3x4 demo is 12 cells; real examples are 21-30 letters |
| columnar_keyword | 6 | 1 | 21-30 | keyword (4-6 letters) | columns + rows | n=1 at 6m; widened 2-6m gives n=3 |
| rail_fence | 6 | 3 | 21-34 | 3-4 rails | zigzag rows + read | n=3 at 6m (2012, 2013, 2018) |
| otp | 6 | 1 | 12-13 | 12 key numbers/letters | 12 modular additions | n=1 at 6m; widened 5-6m gives n=2; still thin, keep lengths 12-13. 26-letter alphabet is verified against DEC 2019; slide 17 is inconsistent |
| acm | 6 | 1 | 4 users x 3 objects | matrix only | 12 matrix cells | 6m = matrix only; 9m = matrix + ACL + CL (2015-06, 2016-12) |
| playfair | 6 | 1 | 10 | key REDFOX (6) | 5 pairs | older style only; no current lecture slide |
| affine | 6 | 1 | 13 | key (17,20) | 13 inverse operations | older style only; no current lecture slide |

ACM rule: 6 marks = matrix only; about 9 marks = matrix + ACL + CL. Playfair and affine are never used in realistic mode; the older style labels them 'not in current lecture slides'.