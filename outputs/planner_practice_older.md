# Planner slot table

- mode: **practice**; style: **older**; seed: 9
- computed marks: **22**; clean-modern distribution: [0, 0, 0, 0, 0, 2, 6, 6, 12, 14] (mean 4.0)
- clean modern papers: 10

| Computed marks | 0 | 2 | 6 | 12 | 14 |
|---|---:|---:|---:|---:|---:|
| clean papers | 5 | 1 | 2 | 1 | 1 |

## Slots

| Slot | Marks | Kind | Topic | Task | Computed type | Target size / key | Notes |
|---|---:|---|---|---|---|---|---|
| A1a | 2 | computed | classical ciphers | compute | caesar | 11-15 letters; shift 7 | computed slot |
| A1b | 6 | theory | attacks/malware | short objective |  |  | theory slot |
| A2a | 2 | theory | attacks/malware | short objective |  |  | theory slot |
| A2b | 6 | computed | classical ciphers | compute | vigenere | 13-18 letters; keyword 6-8 letters | computed slot |
| A3a | 2 | computed | classical ciphers | compute | columnar_3x4 | 12 cells (3 rows x 4 columns); pad X | computed slot |
| A3b | 6 | theory | attacks/malware | short objective |  |  | theory slot |
| A4a | 2 | theory | authentication/biometrics | define/explain |  |  | theory slot |
| A4b | 6 | computed | classical ciphers | compute | playfair | 10-12 letters; key 5-6; 5 x 5 grid, I/J merge, X filler | computed slot |
| A5a | 2 | theory | authentication/biometrics | list/enumerate |  |  | theory slot |
| A5b | 6 | computed | classical ciphers | compute | affine | 13-15 letters; key (a,b) | computed slot |
| A6a | 2 | theory | access control models | short objective |  |  | theory slot |
| A6b | 6 | theory | authentication/biometrics | short objective |  |  | theory slot |
| A7a | 2 | theory | attacks/malware | short objective |  |  | theory slot |
| A7b | 6 | theory | access control models | short objective |  |  | theory slot |
| A8a | 2 | theory | attacks/malware | short objective |  |  | theory slot |
| A8b | 6 | theory | trusted computing/blockchain | short objective |  |  | theory slot |
| A9a | 2 | theory | attacks/malware | compare |  |  | theory slot |
| A9b | 6 | theory | authentication/biometrics | short objective |  |  | theory slot |
| A10a | 2 | theory | attacks/malware | list/enumerate |  |  | theory slot |
| A10b | 6 | theory | network security | short objective |  |  | theory slot |
| B1a | 5 | theory | access control models | define/explain |  |  | theory slot |
| B1b | 5 | theory | software/OS security | define/explain |  |  | theory slot |
| B2a | 5 | theory | attacks/malware | define/explain |  |  | theory slot |
| B2b | 5 | theory | trusted computing/blockchain | define/explain |  |  | theory slot |

## Theory topic marks (assigned vs modern-share target)

| Topic | Assigned | Target | Modern weight |
|---|---:|---:|---:|
| attacks/malware | 27 | 27 | 0.342 |
| authentication/biometrics | 16 | 17 | 0.223 |
| access control models | 13 | 14 | 0.173 |
| trusted computing/blockchain | 11 | 9 | 0.113 |
| software/OS security | 5 | 5 | 0.068 |
| network security | 6 | 6 | 0.080 |

## Calibration used for computed sizes

| Type | Marks | n | Length range | Key | Working steps | Note |
|---|---:|---:|---|---|---|---|
| caesar | 2 | 1 | not printed (word) | shift 4 | word length | n=1 at 2m; widened 2-6m gives n=4, lengths 11-24 |
| caesar | 6 | 2 | 11-38 | shift 7/18 | 11-38 mappings | n=2 at 6m; widened 4-6m gives n=3, lengths 11-38 |
| vigenere | 6 | 1 | 13 | table/keyword | 13 table lookups | n=1 at 6m; widened 3-10m gives n=3, lengths 13-18 |
| columnar_3x4 | 2-6 | 3 | 21-30 | 4-5 columns / keyword | columns + rows | slide 3x4 demo is 12 cells; real examples are 21-30 letters |
| columnar_keyword | 6 | 1 | 21-30 | keyword (4-6 letters) | columns + rows | n=1 at 6m; widened 2-6m gives n=3 |
| rail_fence | 6 | 3 | 21-34 | 3-4 rails | zigzag rows + read | n=3 at 6m (2012, 2013, 2018) |
| otp | 6 | 1 | 12-13 | 12 key numbers/letters | 12 modular additions | n=1 at 6m; widened 5-6m gives n=2; still thin, keep lengths 12-13 |
| acm | 6 | 1 | 4 users x 3 objects | matrix only | 12 matrix cells | 6m = matrix only; 9m = matrix + ACL + CL (2015-06, 2016-12) |
| playfair | 6 | 1 | 10 | key REDFOX (6) | 5 pairs | older style only; no current lecture slide |
| affine | 6 | 1 | 13 | key (17,20) | 13 inverse operations | older style only; no current lecture slide |

ACM rule: 6 marks = matrix only; about 9 marks = matrix + ACL + CL. Playfair and affine are never used in realistic mode; the older style labels them 'not in current lecture slides'.