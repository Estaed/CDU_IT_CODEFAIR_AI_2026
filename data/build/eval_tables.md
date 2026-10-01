# Evaluation on 150 holdout reports

## fault_type

| class | extractor P [95% CI] | extractor R [95% CI] | baseline P [95% CI] | baseline R [95% CI] | extractor F1 | baseline F1 |
|---|---|---|---|---|---|---|
| electrical | 0.947 [0.754, 0.991] | 1.000 [0.824, 1.000] | 0.900 [0.699, 0.972] | 1.000 [0.824, 1.000] | 0.973 | 0.947 |
| plumbing_water | 0.969 [0.843, 0.995] | 1.000 [0.890, 1.000] | 0.816 [0.666, 0.908] | 1.000 [0.890, 1.000] | 0.984 | 0.899 |
| sewer_drainage | 1.000 [0.785, 1.000] | 1.000 [0.785, 1.000] | 1.000 [0.785, 1.000] | 1.000 [0.785, 1.000] | 1.000 | 1.000 |
| cooling | 1.000 [0.806, 1.000] | 0.941 [0.730, 0.990] | 1.000 [0.816, 1.000] | 1.000 [0.816, 1.000] | 0.970 | 1.000 |
| hot_water | 1.000 [0.757, 1.000] | 0.923 [0.667, 0.986] | 1.000 [0.723, 1.000] | 0.769 [0.497, 0.918] | 0.960 | 0.870 |
| roof_structure | 0.923 [0.667, 0.986] | 1.000 [0.757, 1.000] | 1.000 [0.757, 1.000] | 1.000 [0.757, 1.000] | 0.960 | 1.000 |
| doors_locks_security | 1.000 [0.796, 1.000] | 1.000 [0.796, 1.000] | 0.882 [0.657, 0.967] | 1.000 [0.796, 1.000] | 1.000 | 0.938 |
| stove_cooking | 1.000 [0.741, 1.000] | 1.000 [0.741, 1.000] | 1.000 [0.701, 1.000] | 0.818 [0.523, 0.949] | 1.000 | 0.900 |
| pests | 1.000 [0.701, 1.000] | 1.000 [0.701, 1.000] | 1.000 [0.676, 1.000] | 0.889 [0.565, 0.980] | 1.000 | 0.941 |
| other | 1.000 [0.701, 1.000] | 0.900 [0.596, 0.982] | 1.000 [0.566, 1.000] | 0.500 [0.237, 0.763] | 0.947 | 0.667 |
| **macro** | 0.984 | 0.976 | 0.960 | 0.898 | **0.979** | **0.916** |

extractor accuracy 0.980 [0.943, 0.993]; baseline accuracy 0.927 [0.874, 0.959]

## safety_class

| class | extractor P [95% CI] | extractor R [95% CI] | baseline P [95% CI] | baseline R [95% CI] | extractor F1 | baseline F1 |
|---|---|---|---|---|---|---|
| immediate | 1.000 [0.785, 1.000] | 1.000 [0.785, 1.000] | 1.000 [0.646, 1.000] | 0.500 [0.268, 0.732] | 1.000 | 0.667 |
| urgent | 1.000 [0.929, 1.000] | 0.893 [0.785, 0.950] | 0.915 [0.817, 0.963] | 0.964 [0.879, 0.990] | 0.943 | 0.939 |
| routine | 0.930 [0.856, 0.968] | 1.000 [0.954, 1.000] | 0.952 [0.884, 0.981] | 1.000 [0.954, 1.000] | 0.964 | 0.976 |
| **macro** | 0.977 | 0.964 | 0.956 | 0.821 | **0.969** | **0.861** |

extractor accuracy 0.960 [0.915, 0.982]; baseline accuracy 0.940 [0.890, 0.968]

## health_risk

| class | extractor P [95% CI] | extractor R [95% CI] | extractor F1 |
|---|---|---|---|
| infant_or_young_child | 1.000 [0.910, 1.000] | 1.000 [0.910, 1.000] | 1.000 |
| elderly | 1.000 [0.886, 1.000] | 0.968 [0.838, 0.994] | 0.984 |
| pregnancy_or_chronic_condition | 1.000 [0.910, 1.000] | 0.975 [0.871, 0.996] | 0.987 |
| overcrowding | 1.000 [0.862, 1.000] | 1.000 [0.862, 1.000] | 1.000 |
| extreme_heat_exposure | 0.957 [0.790, 0.992] | 1.000 [0.851, 1.000] | 0.978 |
| no_water_or_sanitation | 0.900 [0.699, 0.972] | 1.000 [0.824, 1.000] | 0.947 |
| **macro** | 0.976 | 0.991 | **0.983** |

extractor exact set match 0.967 [0.924, 0.986]

## Cross-vendor challenge set (36 reports written by gpt-6-luna, read by the same extractor)

| field | extractor macro-F1 | extractor accuracy [95% CI] | baseline macro-F1 |
|---|---|---|---|
| fault_type | 0.904 | 0.917 [0.782, 0.971] | 0.764 |
| safety_class | 0.944 | 0.944 [0.819, 0.985] | 0.667 |
| health_risk | 0.917 | 0.833 [0.681, 0.921] | — |

Substring verification: 1.000 [0.997, 1.000] of 1472 extraction rows.
Macro-F1 target 0.85: fault_type met, safety_class met.

Notes:

- location_mentioned and crew_or_access_note have no gold label in labels.json, so they get no precision, recall or F1.
- 0 of 150 holdout rows went to the human queue; their fields count as empty predictions (false negatives). The scores therefore measure what reaches the ranking, not each field in isolation.
- Macro precision, recall and F1 are means over classes, not proportions, so they carry no Wilson interval; each per-class precision and recall, accuracy, exact-set match and the substring rate do.
- The baseline is scored for fault_type and safety_class only.
- The substring rate is over every extraction row, adversarial items included, after verification: the 1 proposed fields whose phrase was not in the text were already dropped (they never display), so the rate shows the display rule holds, not that the model never proposed an ungrounded phrase.
- span_scores is null: no gold spans exist (labels were drawn first and the generator returned text only), and none were invented.
