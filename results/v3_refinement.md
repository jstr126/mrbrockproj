# V3 refinement progress

Status: experimental. The 99% automatic-bin precision requirement remains unmet. Physical camera and Raspberry Pi timing remain untested. Automatic routing in the Pi server remains locked to REVIEW.

Both regression and outline measurements now support validation-fitted correction. A comparison against metric and imperial standards improves candidate labels; disagreement with the network always bypasses to REVIEW. Native-frame pitch evidence retains priority. The ONNX network and its five fp32 outputs are unchanged, with no additional network passes. Original v2 and v3 model files remain intact.

The metadata was selected using synthetic samples from the original fixed validation partition. The internal 890-frame audit is development validation because model selection had previously used that partition. The fresh 800 frames use new renderer seeds, fixed after the metadata candidate was frozen. No fresh or legacy benchmark labels were used to fit the calibration or parameters.

An additional OpenCV repeatability defect was found during timing: 8/20 sampled frames produced different rectifications across unseeded repeats; resetting the OpenCV seed made all 20 repeat exactly. Board acquisition now resets that seed. Both models were rerun with this same acquisition fix, sharing each detected board in the comparison. This makes evaluation repeatable; it does not prove the board transform is physically correct.

## Accuracy with repeatable board acquisition

| Set | Model | Exact label / all bolts | Correct bin / assignments (precision) | Correct bin / all bolts (coverage) | Wrong bin assignments |
|---|---|---|---|---|---|
| test_catalog_normal | boltnet_v3 | 145/225 (64.4%) | 92/110 (83.6%) | 92/225 (40.9%) | 18 |
| test_catalog_normal | boltnet_v3_refined | 154/225 (68.4%) | 88/100 (88.0%) | 88/225 (39.1%) | 12 |
| test_catalog_heavy | boltnet_v3 | 51/225 (22.7%) | 17/31 (54.8%) | 17/225 (7.6%) | 14 |
| test_catalog_heavy | boltnet_v3_refined | 56/225 (24.9%) | 16/30 (53.3%) | 16/225 (7.1%) | 14 |
| test_junk_normal | boltnet_v3 | — | 0/5 (0.0%) | — | 5 |
| test_junk_normal | boltnet_v3_refined | — | 0/6 (0.0%) | — | 6 |
| test_junk_heavy | boltnet_v3 | — | 0/4 (0.0%) | — | 4 |
| test_junk_heavy | boltnet_v3_refined | — | 0/3 (0.0%) | — | 3 |
| test_ai_normal | boltnet_v3 | — | — | — | 0 |
| test_ai_normal | boltnet_v3_refined | — | — | — | 0 |
| test_ai_heavy | boltnet_v3 | — | — | — | 0 |
| test_ai_heavy | boltnet_v3_refined | — | — | — | 0 |
| test_webhold_normal | boltnet_v3 | 1/120 (0.8%) | 0/4 (0.0%) | 0/120 (0.0%) | 4 |
| test_webhold_normal | boltnet_v3_refined | 2/120 (1.7%) | 0/3 (0.0%) | 0/120 (0.0%) | 3 |
| test_webhold_heavy | boltnet_v3 | 1/120 (0.8%) | 0/2 (0.0%) | 0/120 (0.0%) | 2 |
| test_webhold_heavy | boltnet_v3_refined | 2/120 (1.7%) | 0/1 (0.0%) | 0/120 (0.0%) | 1 |
| v3_fresh_normal | boltnet_v3 | 196/300 (65.3%) | 102/121 (84.3%) | 102/300 (34.0%) | 19 |
| v3_fresh_normal | boltnet_v3_refined | 206/300 (68.7%) | 110/121 (90.9%) | 110/300 (36.7%) | 11 |
| v3_fresh_heavy | boltnet_v3 | 75/300 (25.0%) | 23/37 (62.2%) | 23/300 (7.7%) | 14 |
| v3_fresh_heavy | boltnet_v3_refined | 96/300 (32.0%) | 23/28 (82.1%) | 23/300 (7.7%) | 5 |

All bolts, including board detection failures, stay in the coverage denominator. A negative assigned to a size bin is counted as an incorrect assignment. These are offline diagnostic candidate bins; the Pi server still outputs REVIEW for every inspection.

## Fresh-frame latency on this Mac

| Condition | Model | Mean / p95 / p99 ms | Maximum ms | Frames >=100 ms |
|---|---|---|---|---|
| v3_fresh_normal | boltnet_v3 | 55.1 / 86.4 / 111.7 | 162.5 | 11/400 |
| v3_fresh_heavy | boltnet_v3 | 58.5 / 95.7 / 134.6 | 250.4 | 17/400 |
| v3_fresh_normal | boltnet_v3_refined | 59.7 / 112.6 / 183.1 | 330.2 | 33/400 |
| v3_fresh_heavy | boltnet_v3_refined | 37.1 / 53.8 / 62.5 | 88.6 | 0/400 |

Timings include board detection, rectification, ONNX inference and measurement. They exclude camera exposure, browser networking and mechanical motion. A sequential run can reflect CPU load and thermal changes; this is not a claim that calibration accelerates the unchanged network.

## Bypass rule rejected

A validation-selected guard retained 401/403 correct assignments (99.5%) on the fitting portion, then only 100/102 (98.0%) on the reserved synthetic portion. It was not activated as a 99% policy. Correct-bin coverage there was 15.8%.

## Verify and try the experimental runtime

The test and refitting commands below require the full source checkout and its validation data. For the smaller runtime archive, install the dependencies as described in pi_web/README.md and use the final server command.

```bash
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python tools/refine_measurement.py
.venv/bin/python -m pi_web.server --model models/boltnet_v3_refined.onnx --camera 0 --port 8080
```

The included experimental runtime archive contains both the original v3 model and the refined metadata candidate. The original model is the default. The candidate is selected explicitly with `--model` as above. Both remain diagnostic and the server enforces REVIEW. No public Site or Pi deployment was changed in this iteration.

30 tests pass, including regression/outline calibration, system-conflict bypass, strong-pitch priority and board-repeatability checks. Actual ONNX inference was also verified in a process that rejects imports of torch and torchvision.
