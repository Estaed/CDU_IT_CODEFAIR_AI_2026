# Evaluation on 150 holdout reports

## fault_type

| class | extractor P [95% CI] | extractor R [95% CI] | baseline P [95% CI] | baseline R [95% CI] | extractor F1 | baseline F1 |
|---|---|---|---|---|---|---|
| electrical | 0.944 [0.742, 0.990] | 0.944 [0.742, 0.990] | 0.783 [0.581, 0.903] | 1.000 [0.824, 1.000] | 0.944 | 0.878 |
| plumbing_water | 1.000 [0.879, 1.000] | 0.903 [0.751, 0.967] | 0.882 [0.734, 0.953] | 0.968 [0.838, 0.994] | 0.949 | 0.923 |
| sewer_drainage | 1.000 [0.741, 1.000] | 0.786 [0.524, 0.924] | 1.000 [0.757, 1.000] | 0.857 [0.601, 0.960] | 0.880 | 0.923 |
| cooling | 1.000 [0.816, 1.000] | 1.000 [0.816, 1.000] | 0.938 [0.717, 0.989] | 0.882 [0.657, 0.967] | 1.000 | 0.909 |
| hot_water | 0.867 [0.621, 0.963] | 1.000 [0.772, 1.000] | 0.917 [0.646, 0.985] | 0.846 [0.578, 0.957] | 0.929 | 0.880 |
| roof_structure | 1.000 [0.757, 1.000] | 1.000 [0.757, 1.000] | 1.000 [0.757, 1.000] | 1.000 [0.757, 1.000] | 1.000 | 1.000 |
| doors_locks_security | 0.833 [0.608, 0.942] | 1.000 [0.796, 1.000] | 0.833 [0.608, 0.942] | 1.000 [0.796, 1.000] | 0.909 | 0.909 |
| stove_cooking | 0.909 [0.623, 0.984] | 0.909 [0.623, 0.984] | 0.909 [0.623, 0.984] | 0.909 [0.623, 0.984] | 0.909 | 0.909 |
| pests | 1.000 [0.701, 1.000] | 1.000 [0.701, 1.000] | 1.000 [0.701, 1.000] | 1.000 [0.701, 1.000] | 1.000 | 1.000 |
| other | 1.000 [0.566, 1.000] | 0.500 [0.237, 0.763] | 1.000 [0.439, 1.000] | 0.300 [0.108, 0.603] | 0.667 | 0.462 |
| **macro** | 0.955 | 0.904 | 0.926 | 0.876 | **0.919** | **0.879** |

extractor accuracy 0.913 [0.857, 0.949]; baseline accuracy 0.900 [0.842, 0.939]

## safety_class

| class | extractor P [95% CI] | extractor R [95% CI] | baseline P [95% CI] | baseline R [95% CI] | extractor F1 | baseline F1 |
|---|---|---|---|---|---|---|
| immediate | 0.271 [0.166, 0.410] | 0.929 [0.685, 0.987] | 0.000 [0.000, 1.000] | 0.000 [0.000, 0.215] | 0.419 | 0.000 |
| urgent | 0.553 [0.397, 0.699] | 0.375 [0.260, 0.506] | 0.726 [0.614, 0.815] | 0.946 [0.854, 0.982] | 0.447 | 0.822 |
| routine | 0.983 [0.909, 0.997] | 0.713 [0.605, 0.800] | 0.961 [0.892, 0.987] | 0.925 [0.846, 0.965] | 0.826 | 0.943 |
| **macro** | 0.602 | 0.672 | 0.562 | 0.624 | **0.564** | **0.588** |

extractor accuracy 0.607 [0.527, 0.681]; baseline accuracy 0.847 [0.780, 0.896]

## health_risk

| class | extractor P [95% CI] | extractor R [95% CI] | extractor F1 |
|---|---|---|---|
| infant_or_young_child | 0.974 [0.865, 0.995] | 0.949 [0.831, 0.986] | 0.961 |
| elderly | 1.000 [0.879, 1.000] | 0.903 [0.751, 0.967] | 0.949 |
| pregnancy_or_chronic_condition | 1.000 [0.893, 1.000] | 0.800 [0.652, 0.895] | 0.889 |
| overcrowding | 1.000 [0.851, 1.000] | 0.917 [0.742, 0.977] | 0.957 |
| extreme_heat_exposure | 1.000 [0.824, 1.000] | 0.818 [0.615, 0.927] | 0.900 |
| no_water_or_sanitation | 1.000 [0.757, 1.000] | 0.667 [0.438, 0.837] | 0.800 |
| **macro** | 0.996 | 0.842 | **0.909** |

extractor exact set match 0.873 [0.811, 0.917]

Substring verification: 1.000 [0.997, 1.000] of 1472 extraction rows.
Macro-F1 target 0.85: fault_type met, safety_class not met.

Notes:

- location_mentioned and crew_or_access_note have no gold label in labels.json, so they get no precision, recall or F1.
- 6 of 150 holdout rows went to the human queue; their fields count as empty predictions (false negatives).
- Macro precision, recall and F1 are means over classes, not proportions, so they carry no Wilson interval; each per-class precision and recall, accuracy, exact-set match and the substring rate do.
- The baseline is scored for fault_type and safety_class only.
- The substring rate is over every extraction row, adversarial items included.
- span_scores is null: no gold spans exist (labels were drawn first and the generator returned text only), and none were invented.
