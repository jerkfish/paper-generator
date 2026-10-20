# Appendix - pre-hardening multi-model realistic run

**This appendix is not the primary evaluation.** It is the earlier 20-seed, quota-rotated run collected before the final hardening pass. It used several Qwen models because free-tier quotas were exhausted during the run; the per-seed model is shown. The primary evaluation uses one model (DeepSeek V4.1 Flash) across all 20 seeds and is reported in `eval_realistic.md`. Costs here are recomputed from each call's model price table and are estimates, not invoices.

## Results grouped by model

| Model | Seeds | Seed list | Accepted | Placeholders | Placeholder rate | Attempts avg | Max near-copy | Cost |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| qwen3.6-flash | 3 | 6, 14, 16 | 62 | 6 | 8.8% | 2.92 | 0.7012 | $0.0143 |
| qwen3.6-plus | 6 | 13, 15, 17, 18, 19, 20 | 136 | 6 | 4.2% | 2.51 | 0.6918 | $0.0820 |
| qwen3.8-flash | 5 | 1, 2, 3, 4, 9 | 118 | 1 | 0.8% | 2.23 | 0.7845 | $0.0195 |
| qwen3.8-max | 6 | 5, 7, 8, 10, 11, 12 | 132 | 3 | 2.2% | 2.10 | 0.7208 | $0.9447 |

Quota exhaustion is visible as clusters of higher-placeholder seeds within a model group: qwen3.6-flash seeds 14 and 16 have 2 and 3 placeholders, and qwen3.6-plus seeds 13 and 15 have 2 and 3 (seed 19 has 1). The primary evaluation uses one model across all 20 seeds and is in `outputs/eval_realistic.md`.

## Per-seed

| Seed | Model | Computed | Placeholders | Attempts avg | Attempts max | Overlap keys | Max near-copy | Cost |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | qwen3.8-flash | 0 | 1 | 2.42 | 5 | 0 | 0.78 | $0.0043 |
| 2 | qwen3.8-flash | 0 | 0 | 2.25 | 4 | 0 | 0.68 | $0.0041 |
| 3 | qwen3.8-flash | 0 | 0 | 2.33 | 3 | 0 | 0.78 | $0.0040 |
| 4 | qwen3.8-flash | 0 | 0 | 2.17 | 3 | 0 | 0.68 | $0.0038 |
| 5 | qwen3.8-max | 14 | 0 | 1.75 | 2 | 0 | 0.63 | $0.1327 |
| 6 | qwen3.6-flash | 14 | 1 | 2.75 | 5 | 0 | 0.67 | $0.0049 |
| 7 | qwen3.8-max | 2 | 0 | 2.00 | 3 | 0 | 0.72 | $0.1535 |
| 8 | qwen3.8-max | 0 | 1 | 2.50 | 5 | 0 | 0.72 | $0.1807 |
| 9 | qwen3.8-flash | 6 | 0 | 2.00 | 3 | 0 | 0.76 | $0.0034 |
| 10 | qwen3.8-max | 14 | 1 | 2.08 | 5 | 0 | 0.72 | $0.1609 |
| 11 | qwen3.8-max | 6 | 1 | 2.33 | 7 | 0 | 0.72 | $0.1722 |
| 12 | qwen3.8-max | 6 | 0 | 1.92 | 2 | 0 | 0.64 | $0.1446 |
| 13 | qwen3.6-plus | 0 | 2 | 2.83 | 6 | 0 | 0.69 | $0.0158 |
| 14 | qwen3.6-flash | 0 | 2 | 2.83 | 4 | 0 | 0.70 | $0.0050 |
| 15 | qwen3.6-plus | 0 | 3 | 2.83 | 5 | 0 | 0.69 | $0.0151 |
| 16 | qwen3.6-flash | 2 | 3 | 3.17 | 7 | 0 | 0.70 | $0.0044 |
| 17 | qwen3.6-plus | 12 | 0 | 2.00 | 3 | 0 | 0.56 | $0.0107 |
| 18 | qwen3.6-plus | 0 | 0 | 2.33 | 4 | 0 | 0.69 | $0.0130 |
| 19 | qwen3.6-plus | 0 | 1 | 2.67 | 5 | 0 | 0.56 | $0.0145 |
| 20 | qwen3.6-plus | 0 | 0 | 2.42 | 4 | 0 | 0.69 | $0.0128 |
