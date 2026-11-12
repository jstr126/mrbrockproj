# V3 failure audit

These are diagnostic cutoffs fixed before inspecting the case results. They are not a validated routing policy.
Precision counts every automatic size-bin assignment, including non-bolts mistakenly assigned to size bins.
A high confidence is not a calibrated probability of a correct thread/length/head combination.

| Set | Minimum confidence on all three heads | Correct / automatic bins | Precision | Correct automatic assignments / all bolts |
|---|---|---|---|---|
| test_catalog_normal | 0% | 90/108 | 83.3% | 90/225 (40.0%) |
| test_catalog_normal | 70% | 83/94 | 88.3% | 83/225 (36.9%) |
| test_catalog_normal | 80% | 77/86 | 89.5% | 77/225 (34.2%) |
| test_catalog_normal | 90% | 67/72 | 93.1% | 67/225 (29.8%) |
| test_catalog_normal | 95% | 17/19 | 89.5% | 17/225 (7.6%) |
| test_catalog_normal | 99% | 3/4 | 75.0% | 3/225 (1.3%) |
| test_catalog_heavy | 0% | 17/29 | 58.6% | 17/225 (7.6%) |
| test_catalog_heavy | 70% | 13/17 | 76.5% | 13/225 (5.8%) |
| test_catalog_heavy | 80% | 8/10 | 80.0% | 8/225 (3.6%) |
| test_catalog_heavy | 90% | 6/7 | 85.7% | 6/225 (2.7%) |
| test_catalog_heavy | 95% | 1/1 | 100.0% | 1/225 (0.4%) |
| test_catalog_heavy | 99% | 0/0 | — | 0/225 (0.0%) |
| test_junk_normal | 0% | 0/4 | 0.0% | — |
| test_junk_normal | 70% | 0/4 | 0.0% | — |
| test_junk_normal | 80% | 0/2 | 0.0% | — |
| test_junk_normal | 90% | 0/2 | 0.0% | — |
| test_junk_normal | 95% | 0/1 | 0.0% | — |
| test_junk_normal | 99% | 0/0 | — | — |
| test_junk_heavy | 0% | 0/4 | 0.0% | — |
| test_junk_heavy | 70% | 0/1 | 0.0% | — |
| test_junk_heavy | 80% | 0/1 | 0.0% | — |
| test_junk_heavy | 90% | 0/0 | — | — |
| test_junk_heavy | 95% | 0/0 | — | — |
| test_junk_heavy | 99% | 0/0 | — | — |
| test_ai_normal | 0% | 0/0 | — | — |
| test_ai_normal | 70% | 0/0 | — | — |
| test_ai_normal | 80% | 0/0 | — | — |
| test_ai_normal | 90% | 0/0 | — | — |
| test_ai_normal | 95% | 0/0 | — | — |
| test_ai_normal | 99% | 0/0 | — | — |
| test_ai_heavy | 0% | 0/0 | — | — |
| test_ai_heavy | 70% | 0/0 | — | — |
| test_ai_heavy | 80% | 0/0 | — | — |
| test_ai_heavy | 90% | 0/0 | — | — |
| test_ai_heavy | 95% | 0/0 | — | — |
| test_ai_heavy | 99% | 0/0 | — | — |
| test_webhold_normal | 0% | 0/6 | 0.0% | 0/120 (0.0%) |
| test_webhold_normal | 70% | 0/1 | 0.0% | 0/120 (0.0%) |
| test_webhold_normal | 80% | 0/0 | — | 0/120 (0.0%) |
| test_webhold_normal | 90% | 0/0 | — | 0/120 (0.0%) |
| test_webhold_normal | 95% | 0/0 | — | 0/120 (0.0%) |
| test_webhold_normal | 99% | 0/0 | — | 0/120 (0.0%) |
| test_webhold_heavy | 0% | 0/2 | 0.0% | 0/120 (0.0%) |
| test_webhold_heavy | 70% | 0/1 | 0.0% | 0/120 (0.0%) |
| test_webhold_heavy | 80% | 0/0 | — | 0/120 (0.0%) |
| test_webhold_heavy | 90% | 0/0 | — | 0/120 (0.0%) |
| test_webhold_heavy | 95% | 0/0 | — | 0/120 (0.0%) |
| test_webhold_heavy | 99% | 0/0 | — | 0/120 (0.0%) |

A 100% point result on a handful of retained frames is not evidence of a 99% physical sorting rate. The real-photo composites reuse source photographs and have noisy size labels; actual-camera, independently labeled trials are still required.

## test_catalog_normal

bolts sent to REVIEW: 112, bolts not recognised: 10, outline unavailable: 5, outline/regression disagreement: 93, pitch system overrides: 57, incorrect pitch system overrides: 1

- `test_00009.jpg`: M3 x 30 button head → M3 x 30 socket head cap screw; confidence bolt 96.9%, system 84.1%, head 62.5%.
- `test_00052.jpg`: M6 x 50 carriage bolt → M5 x 50 carriage bolt; confidence bolt 99.9%, system 88.0%, head 99.1%.
- `test_00069.jpg`: M8 x 50 button head → M8 x 45 button head; confidence bolt 99.8%, system 95.0%, head 99.9%.
- `test_00079.jpg`: M10 x 20 button head → 7/16-14 x 3/4" button head; confidence bolt 97.4%, system 86.4%, head 99.8%.
- `test_00094.jpg`: M12 x 25 button head → 1/2-13 x 1" button head; confidence bolt 99.8%, system 60.6%, head 99.8%.
- `test_00113.jpg`: #6-32 x 1-1/4" flat head (countersunk) → M3 x 30 flat head (countersunk); confidence bolt 76.4%, system 78.9%, head 69.9%.

## test_catalog_heavy

bolts sent to REVIEW: 186, bolts not recognised: 29, outline unavailable: 27, outline/regression disagreement: 107, pitch system overrides: 6, incorrect pitch system overrides: 0

- `test_00054.jpg`: M6 x 50 button head → 1/4-20 x 2" button head; confidence bolt 96.0%, system 79.2%, head 71.5%.
- `test_00061.jpg`: M8 x 16 socket head cap screw → 5/16-18 x 3/4" socket head cap screw; confidence bolt 95.0%, system 62.0%, head 98.8%.
- `test_00063.jpg`: M8 x 16 flat head (countersunk) → 5/16-18 x 3/4" flat head (countersunk); confidence bolt 93.0%, system 62.9%, head 87.4%.
- `test_00085.jpg`: M10 x 100 hex bolt → M10 x 90 hex bolt; confidence bolt 94.9%, system 62.5%, head 94.8%.
- `test_00088.jpg`: M10 x 100 flat head (countersunk) → M10 x 90 flat head (countersunk); confidence bolt 99.9%, system 95.0%, head 99.4%.
- `test_00089.jpg`: M10 x 100 button head → 3/8-16 x 4" button head; confidence bolt 99.9%, system 76.3%, head 98.4%.

## test_junk_normal

outline unavailable: 10, outline/regression disagreement: 17, pitch system overrides: 4, incorrect pitch system overrides: 4

- `test_00115.jpg`: not a bolt (headless) → M6 x 90 hex bolt; confidence bolt 99.6%, system 95.0%, head 78.5%.
- `test_00118.jpg`: not a bolt (broken) → 1/2-13 x 1-1/4" flat head (countersunk); confidence bolt 93.6%, system 97.0%, head 100.0%.
- `test_00152.jpg`: not a bolt (broken) → 7/16-14 x 1" button head; confidence bolt 95.4%, system 95.8%, head 99.7%.
- `test_00189.jpg`: not a bolt (headless) → 1/4-20 x 5/8" hex bolt; confidence bolt 95.9%, system 95.0%, head 73.0%.

## test_junk_heavy

outline unavailable: 27, outline/regression disagreement: 50

- `test_00037.jpg`: not a bolt (double_head) → #8-32 x 1-1/2" hex bolt; confidence bolt 95.2%, system 64.7%, head 82.4%.
- `test_00135.jpg`: not a bolt (double_head) → M5 x 80 socket head cap screw; confidence bolt 86.0%, system 61.3%, head 67.8%.
- `test_00173.jpg`: not a bolt (broken) → M8 x 16 flat head (countersunk); confidence bolt 96.9%, system 87.6%, head 100.0%.
- `test_00185.jpg`: not a bolt (double_head) → M6 x 100 socket head cap screw; confidence bolt 99.9%, system 68.4%, head 99.9%.

## test_ai_normal

outline unavailable: 1, outline/regression disagreement: 9


## test_ai_heavy

outline unavailable: 1, outline/regression disagreement: 16


## test_webhold_normal

bolts sent to REVIEW: 97, bolts not recognised: 28, outline unavailable: 13, outline/regression disagreement: 83, pitch system overrides: 2, incorrect pitch system overrides: 0

- `test_00004.jpg`: M10 x 45 hex bolt → M10 x 40 button head; confidence bolt 99.4%, system 79.4%, head 70.5%.
- `test_00006.jpg`: M10 x 45 hex bolt → M10 x 40 button head; confidence bolt 99.1%, system 60.3%, head 85.7%.
- `test_00017.jpg`: M12 x 50 hex bolt → M12 x 45 hex bolt; confidence bolt 97.1%, system 68.0%, head 76.0%.
- `test_00028.jpg`: M10 x 45 hex bolt → M10 x 35 button head; confidence bolt 99.3%, system 84.4%, head 61.1%.
- `test_00039.jpg`: M3 x 16 hex bolt → M3 x 12 socket head cap screw; confidence bolt 92.9%, system 65.7%, head 79.5%.
- `test_00056.jpg`: #6-32 x 5/8" socket head cap screw → #6-32 x 3/8" socket head cap screw; confidence bolt 71.1%, system 65.4%, head 66.9%.

## test_webhold_heavy

bolts sent to REVIEW: 101, bolts not recognised: 27, outline unavailable: 25, outline/regression disagreement: 81, pitch system overrides: 2, incorrect pitch system overrides: 1

- `test_00006.jpg`: M10 x 45 hex bolt → M10 x 40 hex bolt; confidence bolt 92.7%, system 60.3%, head 73.9%.
- `test_00069.jpg`: M8 x 40 socket head cap screw → M10 x 35 button head; confidence bolt 99.2%, system 74.8%, head 89.1%.
