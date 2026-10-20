# Stem-length fix - before/after

## Measurement

Stem words are counted after removing `QUESTION n` labels and trailing
`(N marks)` text. The reference is the 10 clean modern papers (Questions
sheet); the 90th percentile is linear-interpolated.

| Marks | Clean modern n | Median words | p90 words | Verifier limit |
|---:|---:|---:|---:|---:|
| 2 | 106 | 9.0 | 18.0 | **18** |
| 5 | 33 | 26.0 | 53.4 | **54** |
| 6 | 88 | 17.0 | 42.6 | **43** |

Implementation: `src/planner/stem_length.py` computes the limits; the drafting
prompt states the per-slot limit; `src/theory/verify.py` rejects a stem above
the p90 for its mark value (in addition to the absolute 130-word guard).

## Before / after

Before: the full 20-seed final DeepSeek run (`outputs/eval_final_deepseek/`,
pre-fix). After: a fresh 8-seed sample (`outputs/eval_stem_sample/`, seeds
1-8, same model and pipeline plus the stem check).

| Marks | Before median | After median | Clean modern median | Before over p90 | After over p90 |
|---:|---:|---:|---:|---:|---:|
| 2 | 19.0 | **12.0** | 9.0 | 109/192 | **0/77** |
| 5 | 31.0 | **26.5** | 26.0 | 0/78 | **0/30** |
| 6 | 31.0 | **21.0** | 17.0 | 12/187 | **0/74** |

After-run totals: **181/185 accepted**, **4 placeholders (2.2%)**, source
overlap **0**. Costs are in `eval_stem_sample_run.log` (about $0.045 per
seed).

The 2-mark median is now close to the real papers and all generated stems are
inside the p90 limit. The 5-mark median matches the real median; the 6-mark
median is still a little above the real median but inside its p90. The full
20-seed evaluation report remains the pre-fix run; this sample is the
post-fix check requested in the small-fixes pass.
