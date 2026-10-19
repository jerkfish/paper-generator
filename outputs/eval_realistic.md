# Realistic-mode evaluation - seeds 1-20

Each seed runs the revised realistic planner and the full theory module (BM25 retrieval, cheap Qwen model, up to 3 retries, source overlap/topic/quote checks). Model and price settings are those in `src/config.py`; costs are estimates, not invoices.

- Models used: **qwen3.6-flash**, **qwen3.6-plus**, **qwen3.8-flash**, **qwen3.8-max** (free-tier quotas rotated; per-seed model in the table).
- Seeds completed: **20/20**
- Theory slots: 464; accepted **448**; placeholders **16**; placeholder rate **3.4%**.
- Source overlap: **0** keys across 0/20 papers; **0** slots involved; target 0.
- Max near-copy similarity against the 35 past papers: **0.78** (threshold 0.80).
- Calls: 564; tokens: 2115646; estimated total cost: **$0.0892**; cost per accepted question: **$0.0002**.
- Scenario questions generated: **70** Part B slots.
- Low term-overlap marking points flagged: **694**.

## Computed-marks distribution vs fingerprint

| Computed marks | Fingerprint count | Eval count |
|---:|---:|---:|
| 0 | 5 | 11 |
| 2 | 1 | 2 |
| 6 | 2 | 3 |
| 12 | 1 | 1 |
| 14 | 1 | 3 |

Fingerprint distribution: `[0, 0, 0, 0, 0, 2, 6, 6, 12, 14]`; eval mean **3.80** marks/paper (fingerprint mean 4.0).

## Per-seed results

| Seed | Model | Computed | Placeholders | Attempts avg | Attempts max | Overlap keys | Overlap rate | Max near-copy | Part B scenarios | Cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | qwen3.8-flash | 0 | 1 | 2.42 | 5 | 0 | 0.0% | 0.78 | 4 | $0.0047 |
| 2 | qwen3.8-flash | 0 | 0 | 2.25 | 4 | 0 | 0.0% | 0.68 | 4 | $0.0044 |
| 3 | qwen3.8-flash | 0 | 0 | 2.33 | 3 | 0 | 0.0% | 0.78 | 4 | $0.0043 |
| 4 | qwen3.8-flash | 0 | 0 | 2.17 | 3 | 0 | 0.0% | 0.68 | 4 | $0.0042 |
| 5 | qwen3.8-max | 14 | 0 | 1.75 | 2 | 0 | 0.0% | 0.63 | 4 | $0.0033 |
| 6 | qwen3.6-flash | 14 | 1 | 2.75 | 5 | 0 | 0.0% | 0.67 | 4 | $0.0053 |
| 7 | qwen3.8-max | 2 | 0 | 2.00 | 3 | 0 | 0.0% | 0.72 | 4 | $0.0039 |
| 8 | qwen3.8-max | 0 | 1 | 2.50 | 5 | 0 | 0.0% | 0.72 | 4 | $0.0046 |
| 9 | qwen3.8-flash | 6 | 0 | 2.00 | 3 | 0 | 0.0% | 0.76 | 4 | $0.0037 |
| 10 | qwen3.8-max | 14 | 1 | 2.08 | 5 | 0 | 0.0% | 0.72 | 4 | $0.0040 |
| 11 | qwen3.8-max | 6 | 1 | 2.33 | 7 | 0 | 0.0% | 0.72 | 3 | $0.0044 |
| 12 | qwen3.8-max | 6 | 0 | 1.92 | 2 | 0 | 0.0% | 0.64 | 4 | $0.0036 |
| 13 | qwen3.6-plus | 0 | 2 | 2.83 | 6 | 0 | 0.0% | 0.69 | 2 | $0.0055 |
| 14 | qwen3.6-flash | 0 | 2 | 2.83 | 4 | 0 | 0.0% | 0.70 | 2 | $0.0055 |
| 15 | qwen3.6-plus | 0 | 3 | 2.83 | 5 | 0 | 0.0% | 0.69 | 2 | $0.0052 |
| 16 | qwen3.6-flash | 2 | 3 | 3.17 | 7 | 0 | 0.0% | 0.70 | 1 | $0.0048 |
| 17 | qwen3.6-plus | 12 | 0 | 2.00 | 3 | 0 | 0.0% | 0.56 | 4 | $0.0037 |
| 18 | qwen3.6-plus | 0 | 0 | 2.33 | 4 | 0 | 0.0% | 0.69 | 4 | $0.0046 |
| 19 | qwen3.6-plus | 0 | 1 | 2.67 | 5 | 0 | 0.0% | 0.56 | 4 | $0.0051 |
| 20 | qwen3.6-plus | 0 | 0 | 2.42 | 4 | 0 | 0.0% | 0.69 | 4 | $0.0045 |

Attempts are per question group (12 groups per paper); a group contains one slot or an (a)/(b) pair.

## Topic mix: planned vs actual (marks summed over 20 seeds)

| Topic | Planned marks | Planned % | Actual marks | Actual % |
|---|---:|---:|---:|---:|
| access control models | 282 | 15.0% | 275 | 14.9% |
| attacks/malware | 466 | 24.8% | 118 | 6.4% |
| authentication/biometrics | 340 | 18.1% | 328 | 17.7% |
| classical ciphers | 0 | 0.0% | 44 | 2.4% |
| network security | 162 | 8.6% | 204 | 11.0% |
| risk/management (ethics) | 296 | 15.7% | 249 | 13.5% |
| software/OS security | 164 | 8.7% | 468 | 25.3% |
| trusted computing/blockchain | 170 | 9.0% | 164 | 8.9% |

Actual topic mix is inferred from the cited decks (majority deck topic per accepted question; ties fall back to the slot topic).

## Placeholder slots by seed

- seed 1: A7a
- seed 6: A9a
- seed 8: A3b
- seed 10: A8a
- seed 11: B1b
- seed 13: B2a, B2b
- seed 14: B2a, B2b
- seed 15: A4b, B2a, B2b
- seed 16: B1b, B2a, B2b
- seed 19: A8b

## Reading the metrics

- Computed marks are sampled from the clean-modern fingerprint; the eval count should approximate the fingerprint distribution.
- Placeholder rate counts theory slots left unresolved after the attempt limit.
- Source overlap is the number of (deck, slide) keys cited by more than one accepted question; target is 0. A non-zero value is only allowed when retrieval had fewer than three unused chunks and is listed in the per-seed theory JSON.
- Max near-copy is the maximum SequenceMatcher ratio of an accepted question against any of the 35 past papers; the verifier rejects at 0.80.
- Actual topic mix is inferred from cited decks, so it can differ from the planner's slot topics when a question cites a deck that serves more than one topic.
- Multiple Qwen models were used because the free-tier quota was exhausted during the 20-seed run; the per-seed model is shown. The cost column uses the configurable qwen-flash list-price estimate, not per-model invoices.
