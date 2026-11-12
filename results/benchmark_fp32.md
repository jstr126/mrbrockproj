# Bolt sizer benchmark

### boltnet.onnx on `data/test_web_heavy` (464 frames: 204 bolts, 260 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **33.4%** |
| Checkerboard found | 95.7% |
| Bolts recognised as bolts | 79.6% |
| Non-bolts rejected as 'not a bolt' | 62.1% |
| Diameter right (ignoring metric/imperial) | 50.0% |
| Thread exactly right (incl. metric/imperial) | 28.8% |
| Length exactly right | 9.0% |
| Head type right | 19.2% |
| Metric/imperial right | 42.9% |
| Exact size + type (of bolts recognised) | 0.6% |
| Mean diameter error | 0.76 mm |
| Mean length error | 6.0 mm |

| Time per frame (ms) | mean | median | p95 | max |
|---|---|---|---|---|
| detect | 35.9 | 31.1 | 66.8 | 235.8 |
| rectify | 0.2 | 0.2 | 0.3 | 0.4 |
| network | 7.2 | 7.7 | 9.9 | 14.6 |
| total | 43.0 | 38.6 | 75.4 | 246.7 |

Frames under 100 ms: **98.3%**

Sample mistakes (truth -> predicted):

- 1/2-13 x 1-3/4" hex bolt  ->  1/2-13 x 1-1/2" carriage bolt
- M8 x 30 hex bolt  ->  5/16-18 x 3/4" hex bolt
- M12 x 45 hex bolt  ->  1/2-13 x 1-1/2" carriage bolt
- M10 x 35 hex bolt  ->  3/8-16 x 1-1/4" carriage bolt
- M8 x 30 hex bolt  ->  M6 x 40 button head
- M10 x 35 hex bolt  ->  7/16-14 x 1-1/4" hex bolt
- M12 x 45 hex bolt  ->  M12 x 40 hex bolt
- #6-32 x 1/2" hex bolt  ->  M3 x 12 button head
- M10 x 35 hex bolt  ->  M8 x 35 carriage bolt
- #6-32 x 1/2" hex bolt  ->  M3 x 8 carriage bolt
- 7/16-14 x 1-1/2" hex bolt  ->  7/16-14 x 1-1/4" carriage bolt
- 1/4-20 x 1" hex bolt  ->  M5 x 30 button head

### boltnet.onnx on `data/test_web_normal` (464 frames: 204 bolts, 260 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **40.9%** |
| Checkerboard found | 98.7% |
| Bolts recognised as bolts | 84.5% |
| Non-bolts rejected as 'not a bolt' | 71.7% |
| Diameter right (ignoring metric/imperial) | 69.2% |
| Thread exactly right (incl. metric/imperial) | 52.7% |
| Length exactly right | 4.1% |
| Head type right | 29.0% |
| Metric/imperial right | 63.9% |
| Exact size + type (of bolts recognised) | 3.0% |
| Mean diameter error | 0.65 mm |
| Mean length error | 7.1 mm |

| Time per frame (ms) | mean | median | p95 | max |
|---|---|---|---|---|
| detect | 41.6 | 36.9 | 75.0 | 193.9 |
| rectify | 0.2 | 0.2 | 0.3 | 0.3 |
| network | 8.1 | 7.8 | 9.1 | 10.5 |
| total | 49.8 | 45.2 | 83.2 | 204.4 |

Frames under 100 ms: **97.8%**

Sample mistakes (truth -> predicted):

- 1/2-13 x 1-3/4" hex bolt  ->  7/16-14 x 1-1/2" carriage bolt
- M8 x 30 hex bolt  ->  M8 x 25 carriage bolt
- 1/2-13 x 1-3/4" hex bolt  ->  7/16-14 x 1-1/2" carriage bolt
- #6-32 x 1/2" hex bolt  ->  #8-32 x 3/8" button head
- M8 x 30 hex bolt  ->  M8 x 20 carriage bolt
- M10 x 35 hex bolt  ->  M10 x 30 hex bolt
- M12 x 45 hex bolt  ->  7/16-14 x 1-1/4" carriage bolt
- #6-32 x 1/2" hex bolt  ->  M4 x 8 carriage bolt
- 1/2-13 x 1-3/4" hex bolt  ->  M12 x 35 carriage bolt
- #6-32 x 1/2" hex bolt  ->  M4 x 10 hex bolt
- 7/16-14 x 1-1/2" hex bolt  ->  M10 x 35 carriage bolt
- M12 x 45 hex bolt  ->  M12 x 35 carriage bolt

### boltnet.onnx on `data/test_synth_heavy` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **36.8%** |
| Checkerboard found | 96.0% |
| Bolts recognised as bolts | 91.0% |
| Non-bolts rejected as 'not a bolt' | 87.4% |
| Diameter right (ignoring metric/imperial) | 62.7% |
| Thread exactly right (incl. metric/imperial) | 43.7% |
| Length exactly right | 39.5% |
| Head type right | 66.5% |
| Metric/imperial right | 59.3% |
| Exact size + type (of bolts recognised) | 24.3% |
| Mean diameter error | 0.61 mm |
| Mean length error | 4.1 mm |

| Time per frame (ms) | mean | median | p95 | max |
|---|---|---|---|---|
| detect | 38.7 | 34.7 | 69.3 | 158.1 |
| rectify | 0.2 | 0.2 | 0.3 | 0.4 |
| network | 8.3 | 7.7 | 10.1 | 191.7 |
| total | 46.9 | 42.5 | 79.2 | 221.2 |

Frames under 100 ms: **98.2%**

Sample mistakes (truth -> predicted):

- M12 x 25 flat head (countersunk)  ->  7/16-14 x 1-1/4" flat head (countersunk)
- M6 x 50 hex bolt  ->  #10-24 x 2" hex bolt
- M6 x 90 flat head (countersunk)  ->  #10-24 x 3-1/2" socket head cap screw
- M12 x 80 button head  ->  7/16-14 x 3-1/2" button head
- 1/4-20 x 5/8" socket head cap screw  ->  M6 x 16 carriage bolt
- #6-32 x 3/4" socket head cap screw  ->  M3 x 16 flat head (countersunk)
- #10-24 x 3" button head  ->  M5 x 80 button head
- M3 x 35 hex bolt  ->  M4 x 45 hex bolt
- M3 x 16 hex bolt  ->  M3 x 20 button head
- #6-32 x 3/4" socket head cap screw  ->  M4 x 20 socket head cap screw
- M6 x 40 button head  ->  M8 x 40 button head
- #6-32 x 1-1/2" hex bolt  ->  #8-32 x 1-1/2" hex bolt
