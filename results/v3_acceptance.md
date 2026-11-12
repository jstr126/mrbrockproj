# V3 acceptance

Status: requirements remain unmet

Precision is correct size-bin assignments / all size-bin assignments; coverage is correct assignments / all bolts.
Board failures count as REVIEW. Timing is from this Mac; Raspberry Pi timing remains unmeasured.

Target: at least 99% correct automatic bin assignments, with bypass/REVIEW coverage reported separately. A 99% model confidence is not measured 99% accuracy.
Rendered and Wikimedia composites do not qualify the physical machine. No labeled capture from the actual camera/feed has been evaluated; vision accuracy cannot prove a jam-free mechanism.

| Test set | Model | Fully right / bolts | Right size bin / bolts | Right bin / sent | Bolts recognised / bolts | Non-bolts REJECT / negatives | Negatives in size bins | Mean / p95 ms |
|---|---|---|---|---|---|---|---|---|
| test_catalog_normal | boltnet | 131/225 (58.2%) | 117/225 (52.0%) | 117/177 (66.1%) | 215/225 (95.6%) | 55/56 (98.2%) | 0 | 34.4 / 54.2 |
| test_catalog_normal | boltnet_v3 | 144/225 (64.0%) | 90/225 (40.0%) | 90/108 (83.3%) | 215/225 (95.6%) | 55/56 (98.2%) | 0 | 39.9 / 57.7 |
| test_catalog_heavy | boltnet | 51/225 (22.7%) | 26/225 (11.6%) | 26/66 (39.4%) | 202/225 (89.8%) | 44/56 (78.6%) | 0 | 33.8 / 54.0 |
| test_catalog_heavy | boltnet_v3 | 52/225 (23.1%) | 17/225 (7.6%) | 17/29 (58.6%) | 196/225 (87.1%) | 46/56 (82.1%) | 0 | 39.1 / 55.6 |
| test_junk_normal | boltnet | — | — | 0/19 (0.0%) | — | 146/200 (73.0%) | 19 | 36.6 / 63.7 |
| test_junk_normal | boltnet_v3 | — | — | 0/4 (0.0%) | — | 147/200 (73.5%) | 4 | 38.1 / 55.6 |
| test_junk_heavy | boltnet | — | — | 0/8 (0.0%) | — | 80/200 (40.0%) | 8 | 34.2 / 58.3 |
| test_junk_heavy | boltnet_v3 | — | — | 0/4 (0.0%) | — | 79/200 (39.5%) | 4 | 38.4 / 64.4 |
| test_ai_normal | boltnet | — | — | 0/1 (0.0%) | — | 41/45 (91.1%) | 1 | 33.7 / 50.8 |
| test_ai_normal | boltnet_v3 | — | — | — | — | 30/45 (66.7%) | 0 | 38.4 / 55.9 |
| test_ai_heavy | boltnet | — | — | — | — | 34/45 (75.6%) | 0 | 33.5 / 51.9 |
| test_ai_heavy | boltnet_v3 | — | — | — | — | 15/45 (33.3%) | 0 | 37.7 / 72.9 |
| test_webhold_normal | boltnet | 0/120 (0.0%) | 0/120 (0.0%) | 0/27 (0.0%) | 37/120 (30.8%) | 152/175 (86.9%) | 6 | 33.9 / 55.1 |
| test_webhold_normal | boltnet_v3 | 1/120 (0.8%) | 0/120 (0.0%) | 0/6 (0.0%) | 92/120 (76.7%) | 143/175 (81.7%) | 0 | 38.9 / 59.4 |
| test_webhold_heavy | boltnet | 0/120 (0.0%) | 0/120 (0.0%) | 0/10 (0.0%) | 49/120 (40.8%) | 136/175 (77.7%) | 1 | 33.3 / 49.2 |
| test_webhold_heavy | boltnet_v3 | 1/120 (0.8%) | 0/120 (0.0%) | 0/2 (0.0%) | 93/120 (77.5%) | 124/175 (70.9%) | 0 | 37.4 / 53.5 |

| Check | Outcome |
|---|---|
| test_catalog_normal: fully right | PASS |
| test_catalog_normal: correct-bin coverage | FAIL |
| test_catalog_normal: bin precision | PASS |
| test_catalog_normal: at least 99% of automatic size-bin assignments correct | FAIL |
| test_catalog_heavy: fully right | PASS |
| test_catalog_heavy: correct-bin coverage | FAIL |
| test_catalog_heavy: bin precision | PASS |
| test_catalog_heavy: at least 99% of automatic size-bin assignments correct | FAIL |
| test_junk_normal: rejection | PASS |
| test_junk_normal: no extra size-bin errors | PASS |
| test_junk_heavy: rejection | FAIL |
| test_junk_heavy: no extra size-bin errors | PASS |
| test_ai_normal: rejection | FAIL |
| test_ai_normal: no extra size-bin errors | PASS |
| test_ai_heavy: rejection | FAIL |
| test_ai_heavy: no extra size-bin errors | PASS |
| test_webhold_normal: recognition improves by at least 5 points | PASS |
| test_webhold_normal: at least 99% of automatic size-bin assignments correct | FAIL |
| test_webhold_heavy: recognition improves by at least 5 points | PASS |
| test_webhold_heavy: at least 99% of automatic size-bin assignments correct | FAIL |
| test_catalog_normal: mean and p95 below 100 ms | PASS |
| test_catalog_heavy: mean and p95 below 100 ms | PASS |
| test_junk_normal: mean and p95 below 100 ms | PASS |
| test_junk_heavy: mean and p95 below 100 ms | PASS |
| test_ai_normal: mean and p95 below 100 ms | PASS |
| test_ai_heavy: mean and p95 below 100 ms | PASS |
| test_webhold_normal: mean and p95 below 100 ms | PASS |
| test_webhold_heavy: mean and p95 below 100 ms | PASS |
