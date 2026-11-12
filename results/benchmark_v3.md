# Bolt sizer benchmark

Host: macOS-26.6.2-arm64-arm-64bit-Mach-O; CPU threads: 2
12:52  up 10 days,  1:35, 3 users, load averages: 4.41 5.22 5.62

### boltnet.onnx on `data/test_catalog_normal` (281 frames: 225 bolts, 56 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **66.2%** |
| Checkerboard found | 99.6% |
| Bolts recognised as bolts (all bolts) | 95.6% |
| Fully right (all bolts) | 58.2% |
| Right size bin (all bolts) | 52.0% |
| Non-bolts rejected as 'not a bolt' | 98.2% |
| Diameter right (ignoring metric/imperial) | 91.6% |
| Thread exactly right (incl. metric/imperial) | 80.0% |
| Length exactly right | 68.4% |
| Head type right | 93.0% |
| Metric/imperial right | 85.6% |
| Exact size + type (of bolts recognised) | 60.9% |
| Mean diameter error | 0.27 mm |
| Mean length error | 1.8 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.2 | 23.3 | 45.5 | 71.6 | 90.0 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.6 |
| network | 7.9 | 7.6 | 8.5 | 10.5 | 49.5 |
| measurement | 0.1 | 0.1 | 0.1 | 0.2 | 0.2 |
| total | 34.4 | 31.5 | 54.2 | 79.4 | 98.8 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/281**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 45 | 88.9% | 82.2% | 53.3% |
| socket head cap screw | 45 | 88.9% | 91.1% | 53.3% |
| carriage bolt | 45 | 88.9% | 91.1% | 64.4% |
| flat head (countersunk) | 45 | 84.4% | 91.1% | 66.7% |
| button head | 45 | 86.7% | 88.9% | 53.3% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M3 | 15 | 86.7% | 53.3% | 33.3% |
| M4 | 15 | 100.0% | 100.0% | 46.7% |
| M5 | 15 | 93.3% | 86.7% | 46.7% |
| M6 | 15 | 86.7% | 100.0% | 73.3% |
| M8 | 15 | 93.3% | 93.3% | 80.0% |
| M10 | 15 | 93.3% | 100.0% | 66.7% |
| M12 | 15 | 93.3% | 100.0% | 73.3% |
| #6-32 | 15 | 66.7% | 53.3% | 40.0% |
| #8-32 | 15 | 73.3% | 93.3% | 33.3% |
| #10-24 | 15 | 73.3% | 80.0% | 46.7% |
| 1/4-20 | 15 | 93.3% | 93.3% | 46.7% |
| 5/16-18 | 15 | 80.0% | 86.7% | 53.3% |
| 3/8-16 | 15 | 100.0% | 100.0% | 86.7% |
| 7/16-14 | 15 | 93.3% | 100.0% | 73.3% |
| 1/2-13 | 15 | 86.7% | 93.3% | 73.3% |

Sample mistakes (truth -> predicted):

- M3 x 8 hex bolt  ->  M3 x 8 flat head (countersunk)
- M3 x 8 socket head cap screw  ->  M3 x 10 socket head cap screw
- M3 x 8 button head  ->  M3 x 10 button head
- M3 x 30 hex bolt  ->  M3 x 30 flat head (countersunk)
- M3 x 30 socket head cap screw  ->  M3 x 30 button head
- M3 x 30 button head  ->  M3 x 30 socket head cap screw
- M3 x 60 hex bolt  ->  M3 x 60 button head
- M3 x 60 button head  ->  M3 x 55 button head
- M4 x 8 hex bolt  ->  M4 x 10 hex bolt
- M4 x 8 socket head cap screw  ->  M4 x 10 socket head cap screw
- M4 x 8 carriage bolt  ->  M4 x 10 carriage bolt
- M4 x 8 button head  ->  M4 x 10 button head

### boltnet.onnx on `data/test_catalog_heavy` (281 frames: 225 bolts, 56 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **34.9%** |
| Checkerboard found | 96.1% |
| Bolts recognised as bolts (all bolts) | 89.8% |
| Fully right (all bolts) | 22.7% |
| Right size bin (all bolts) | 11.6% |
| Non-bolts rejected as 'not a bolt' | 83.9% |
| Diameter right (ignoring metric/imperial) | 68.8% |
| Thread exactly right (incl. metric/imperial) | 49.0% |
| Length exactly right | 35.1% |
| Head type right | 70.8% |
| Metric/imperial right | 59.9% |
| Exact size + type (of bolts recognised) | 25.2% |
| Mean diameter error | 0.49 mm |
| Mean length error | 4.0 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.2 | 23.5 | 46.3 | 74.2 | 91.8 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.9 |
| network | 7.7 | 7.6 | 8.2 | 8.8 | 9.4 |
| measurement | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 |
| total | 33.8 | 31.0 | 54.0 | 78.9 | 99.8 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/281**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 45 | 62.2% | 51.1% | 28.9% |
| socket head cap screw | 45 | 64.4% | 80.0% | 24.4% |
| carriage bolt | 45 | 62.2% | 71.1% | 17.8% |
| flat head (countersunk) | 45 | 64.4% | 60.0% | 28.9% |
| button head | 45 | 55.6% | 55.6% | 13.3% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M3 | 15 | 60.0% | 26.7% | 13.3% |
| M4 | 15 | 46.7% | 46.7% | 6.7% |
| M5 | 15 | 60.0% | 60.0% | 26.7% |
| M6 | 15 | 60.0% | 66.7% | 33.3% |
| M8 | 15 | 66.7% | 66.7% | 26.7% |
| M10 | 15 | 60.0% | 80.0% | 13.3% |
| M12 | 15 | 46.7% | 80.0% | 26.7% |
| #6-32 | 15 | 40.0% | 46.7% | 6.7% |
| #8-32 | 15 | 66.7% | 40.0% | 13.3% |
| #10-24 | 15 | 73.3% | 46.7% | 13.3% |
| 1/4-20 | 15 | 60.0% | 60.0% | 6.7% |
| 5/16-18 | 15 | 73.3% | 80.0% | 26.7% |
| 3/8-16 | 15 | 86.7% | 73.3% | 33.3% |
| 7/16-14 | 15 | 60.0% | 93.3% | 46.7% |
| 1/2-13 | 15 | 66.7% | 86.7% | 46.7% |

Sample mistakes (truth -> predicted):

- M3 x 8 hex bolt  ->  M3 x 8 carriage bolt
- M3 x 8 button head  ->  M3 x 10 button head
- M3 x 30 socket head cap screw  ->  M3 x 35 button head
- M3 x 30 carriage bolt  ->  M3 x 30 button head
- M3 x 30 flat head (countersunk)  ->  #8-32 x 1" socket head cap screw
- M3 x 30 button head  ->  M4 x 25 flat head (countersunk)
- M3 x 60 hex bolt  ->  M3 x 60 socket head cap screw
- M3 x 60 socket head cap screw  ->  M4 x 55 hex bolt
- M3 x 60 carriage bolt  ->  M3 x 50 carriage bolt
- M3 x 60 button head  ->  M3 x 60 hex bolt
- M4 x 8 socket head cap screw  ->  M4 x 10 socket head cap screw
- M4 x 8 carriage bolt  ->  M3 x 10 carriage bolt

### boltnet.onnx on `data/test_junk_normal` (200 frames: 0 bolts, 200 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **78.0%** |
| Checkerboard found | 97.0% |
| Bolts recognised as bolts (all bolts) | n/a |
| Fully right (all bolts) | n/a |
| Right size bin (all bolts) | n/a |
| Non-bolts rejected as 'not a bolt' | 78.0% |
| Diameter right (ignoring metric/imperial) | n/a |
| Thread exactly right (incl. metric/imperial) | n/a |
| Length exactly right | n/a |
| Head type right | n/a |
| Metric/imperial right | n/a |
| Exact size + type (of bolts recognised) | n/a |
| Mean diameter error | n/a |
| Mean length error | n/a |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 28.0 | 24.5 | 52.0 | 70.3 | 83.2 |
| rectify | 0.2 | 0.2 | 0.3 | 0.9 | 1.8 |
| network | 8.7 | 7.7 | 10.7 | 14.6 | 125.6 |
| measurement | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 |
| total | 36.6 | 32.7 | 63.7 | 85.3 | 183.1 |

Frames under 100 ms: **99.5%**
Frames at or above 100 ms: **1/200**

### boltnet.onnx on `data/test_junk_heavy` (200 frames: 0 bolts, 200 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **47.5%** |
| Checkerboard found | 94.5% |
| Bolts recognised as bolts (all bolts) | n/a |
| Fully right (all bolts) | n/a |
| Right size bin (all bolts) | n/a |
| Non-bolts rejected as 'not a bolt' | 47.5% |
| Diameter right (ignoring metric/imperial) | n/a |
| Thread exactly right (incl. metric/imperial) | n/a |
| Length exactly right | n/a |
| Head type right | n/a |
| Metric/imperial right | n/a |
| Exact size + type (of bolts recognised) | n/a |
| Mean diameter error | n/a |
| Mean length error | n/a |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.7 | 22.6 | 50.9 | 96.9 | 110.9 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.9 |
| network | 7.7 | 7.6 | 8.3 | 10.1 | 15.3 |
| measurement | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 |
| total | 34.2 | 30.4 | 58.3 | 103.4 | 110.9 |

Frames under 100 ms: **98.5%**
Frames at or above 100 ms: **3/200**

### boltnet.onnx on `data/test_ai_normal` (45 frames: 0 bolts, 45 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **91.1%** |
| Checkerboard found | 95.6% |
| Bolts recognised as bolts (all bolts) | n/a |
| Fully right (all bolts) | n/a |
| Right size bin (all bolts) | n/a |
| Non-bolts rejected as 'not a bolt' | 91.1% |
| Diameter right (ignoring metric/imperial) | n/a |
| Thread exactly right (incl. metric/imperial) | n/a |
| Length exactly right | n/a |
| Head type right | n/a |
| Metric/imperial right | n/a |
| Exact size + type (of bolts recognised) | n/a |
| Mean diameter error | n/a |
| Mean length error | n/a |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.2 | 24.9 | 43.0 | 49.3 | 50.5 |
| rectify | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| network | 7.7 | 7.6 | 8.2 | 8.5 | 8.6 |
| measurement | 0.0 | 0.0 | 0.0 | 0.1 | 0.1 |
| total | 33.7 | 32.8 | 50.8 | 57.1 | 58.3 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/45**

### boltnet.onnx on `data/test_ai_heavy` (45 frames: 0 bolts, 45 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **84.4%** |
| Checkerboard found | 97.8% |
| Bolts recognised as bolts (all bolts) | n/a |
| Fully right (all bolts) | n/a |
| Right size bin (all bolts) | n/a |
| Non-bolts rejected as 'not a bolt' | 84.4% |
| Diameter right (ignoring metric/imperial) | n/a |
| Thread exactly right (incl. metric/imperial) | n/a |
| Length exactly right | n/a |
| Head type right | n/a |
| Metric/imperial right | n/a |
| Exact size + type (of bolts recognised) | n/a |
| Mean diameter error | n/a |
| Mean length error | n/a |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 25.9 | 23.1 | 44.1 | 68.5 | 72.3 |
| rectify | 0.2 | 0.2 | 0.2 | 0.2 | 0.3 |
| network | 7.6 | 7.6 | 7.7 | 8.0 | 8.1 |
| measurement | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 |
| total | 33.5 | 31.0 | 51.9 | 76.5 | 80.6 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/45**

### boltnet.onnx on `data/test_webhold_normal` (295 frames: 120 bolts, 175 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **54.2%** |
| Checkerboard found | 97.3% |
| Bolts recognised as bolts (all bolts) | 30.8% |
| Fully right (all bolts) | 0.0% |
| Right size bin (all bolts) | 0.0% |
| Non-bolts rejected as 'not a bolt' | 91.4% |
| Diameter right (ignoring metric/imperial) | 62.2% |
| Thread exactly right (incl. metric/imperial) | 51.4% |
| Length exactly right | 5.4% |
| Head type right | 35.1% |
| Metric/imperial right | 67.6% |
| Exact size + type (of bolts recognised) | 0.0% |
| Mean diameter error | 0.63 mm |
| Mean length error | 6.9 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.2 | 23.8 | 47.3 | 75.8 | 102.6 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.6 |
| network | 7.7 | 7.6 | 8.4 | 9.7 | 17.0 |
| measurement | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 |
| total | 33.9 | 31.7 | 55.1 | 88.0 | 112.3 |

Frames under 100 ms: **99.3%**
Frames at or above 100 ms: **2/295**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 48 | 27.1% | 14.6% | 0.0% |
| socket head cap screw | 24 | 33.3% | 25.0% | 0.0% |
| button head | 24 | 4.2% | 0.0% | 0.0% |
| carriage bolt | 12 | 0.0% | 0.0% | 0.0% |
| flat head (countersunk) | 12 | 8.3% | 0.0% | 0.0% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M12 | 32 | 6.2% | 6.2% | 0.0% |
| M10 | 24 | 16.7% | 8.3% | 0.0% |
| M6 | 15 | 26.7% | 13.3% | 0.0% |
| M8 | 12 | 16.7% | 8.3% | 0.0% |
| M3 | 6 | 50.0% | 16.7% | 0.0% |
| #6-32 | 9 | 33.3% | 44.4% | 0.0% |
| 1/2-13 | 5 | 0.0% | 0.0% | 0.0% |
| M5 | 5 | 60.0% | 20.0% | 0.0% |
| M4 | 2 | 50.0% | 0.0% | 0.0% |
| #8-32 | 3 | 33.3% | 0.0% | 0.0% |
| 7/16-14 | 6 | 0.0% | 0.0% | 0.0% |
| 1/4-20 | 1 | 0.0% | 0.0% | 0.0% |

Sample mistakes (truth -> predicted):

- M10 x 45 hex bolt  ->  M12 x 40 button head
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M12 x 55 hex bolt  ->  M12 x 45 hex bolt
- M6 x 25 hex bolt  ->  1/4-20 x 1" carriage bolt
- M10 x 45 hex bolt  ->  M10 x 40 hex bolt
- M6 x 25 hex bolt  ->  M5 x 25 carriage bolt
- M10 x 45 hex bolt  ->  M10 x 35 hex bolt
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M12 x 50 hex bolt  ->  M12 x 40 hex bolt
- M6 x 25 hex bolt  ->  M6 x 20 carriage bolt
- M10 x 45 hex bolt  ->  M8 x 35 carriage bolt
- M8 x 35 hex bolt  ->  M8 x 30 carriage bolt

### boltnet.onnx on `data/test_webhold_heavy` (295 frames: 120 bolts, 175 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **48.5%** |
| Checkerboard found | 96.9% |
| Bolts recognised as bolts (all bolts) | 40.8% |
| Fully right (all bolts) | 0.0% |
| Right size bin (all bolts) | 0.0% |
| Non-bolts rejected as 'not a bolt' | 81.7% |
| Diameter right (ignoring metric/imperial) | 46.9% |
| Thread exactly right (incl. metric/imperial) | 34.7% |
| Length exactly right | 8.2% |
| Head type right | 22.4% |
| Metric/imperial right | 57.1% |
| Exact size + type (of bolts recognised) | 0.0% |
| Mean diameter error | 0.84 mm |
| Mean length error | 7.4 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 25.6 | 22.0 | 42.6 | 71.7 | 200.5 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.6 |
| network | 7.7 | 7.6 | 8.2 | 9.0 | 11.7 |
| measurement | 0.0 | 0.0 | 0.1 | 0.1 | 0.2 |
| total | 33.3 | 29.8 | 49.2 | 79.5 | 208.5 |

Frames under 100 ms: **99.7%**
Frames at or above 100 ms: **1/295**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 48 | 25.0% | 12.5% | 0.0% |
| socket head cap screw | 24 | 29.2% | 8.3% | 0.0% |
| button head | 24 | 12.5% | 12.5% | 0.0% |
| carriage bolt | 12 | 0.0% | 0.0% | 0.0% |
| flat head (countersunk) | 12 | 8.3% | 0.0% | 0.0% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M12 | 35 | 5.7% | 2.9% | 0.0% |
| M10 | 25 | 28.0% | 12.0% | 0.0% |
| M8 | 15 | 26.7% | 13.3% | 0.0% |
| M6 | 8 | 50.0% | 25.0% | 0.0% |
| M3 | 6 | 50.0% | 0.0% | 0.0% |
| #6-32 | 7 | 14.3% | 14.3% | 0.0% |
| 1/2-13 | 5 | 0.0% | 0.0% | 0.0% |
| M5 | 4 | 0.0% | 0.0% | 0.0% |
| M4 | 5 | 0.0% | 0.0% | 0.0% |
| #8-32 | 3 | 0.0% | 33.3% | 0.0% |
| 7/16-14 | 6 | 16.7% | 16.7% | 0.0% |
| 1/4-20 | 1 | 100.0% | 0.0% | 0.0% |

Sample mistakes (truth -> predicted):

- M12 x 55 hex bolt  ->  1/2-13 x 2" carriage bolt
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M10 x 45 hex bolt  ->  7/16-14 x 1-1/2" button head
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M10 x 45 hex bolt  ->  7/16-14 x 1-1/2" hex bolt
- M10 x 45 hex bolt  ->  M10 x 35 hex bolt
- M12 x 55 hex bolt  ->  1/2-13 x 2" carriage bolt
- M10 x 45 hex bolt  ->  M10 x 45 button head
- M10 x 45 hex bolt  ->  3/8-16 x 1-1/2" hex bolt
- M8 x 35 hex bolt  ->  M6 x 30 carriage bolt
- M8 x 35 hex bolt  ->  M6 x 80 button head
- M12 x 50 hex bolt  ->  M12 x 50 button head

### boltnet_v3.onnx on `data/test_catalog_normal` (281 frames: 225 bolts, 56 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **71.9%** |
| Checkerboard found | 98.9% |
| Bolts recognised as bolts (all bolts) | 96.9% |
| Fully right (all bolts) | 65.3% |
| Right size bin (all bolts) | 41.8% |
| Non-bolts rejected as 'not a bolt' | 98.2% |
| Diameter right (ignoring metric/imperial) | 88.5% |
| Thread exactly right (incl. metric/imperial) | 77.1% |
| Length exactly right | 74.8% |
| Head type right | 94.0% |
| Metric/imperial right | 83.9% |
| Exact size + type (of bolts recognised) | 67.4% |
| Mean diameter error | 0.31 mm |
| Mean length error | 1.7 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 25.7 | 23.4 | 42.5 | 61.6 | 120.8 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.3 |
| network | 11.3 | 11.2 | 12.1 | 13.9 | 14.7 |
| measurement | 2.9 | 3.4 | 4.5 | 5.4 | 7.2 |
| total | 39.9 | 37.4 | 57.7 | 76.1 | 132.2 |

Frames under 100 ms: **99.6%**
Frames at or above 100 ms: **1/281**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 45 | 91.1% | 91.1% | 64.4% |
| socket head cap screw | 45 | 86.7% | 91.1% | 62.2% |
| carriage bolt | 45 | 82.2% | 88.9% | 66.7% |
| flat head (countersunk) | 45 | 86.7% | 93.3% | 75.6% |
| button head | 45 | 82.2% | 91.1% | 57.8% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M3 | 15 | 73.3% | 46.7% | 26.7% |
| M4 | 15 | 93.3% | 100.0% | 46.7% |
| M5 | 15 | 86.7% | 93.3% | 66.7% |
| M6 | 15 | 86.7% | 100.0% | 73.3% |
| M8 | 15 | 100.0% | 100.0% | 86.7% |
| M10 | 15 | 93.3% | 100.0% | 73.3% |
| M12 | 15 | 100.0% | 100.0% | 100.0% |
| #6-32 | 15 | 60.0% | 73.3% | 40.0% |
| #8-32 | 15 | 60.0% | 86.7% | 33.3% |
| #10-24 | 15 | 80.0% | 93.3% | 60.0% |
| 1/4-20 | 15 | 93.3% | 93.3% | 60.0% |
| 5/16-18 | 15 | 93.3% | 100.0% | 66.7% |
| 3/8-16 | 15 | 93.3% | 93.3% | 86.7% |
| 7/16-14 | 15 | 86.7% | 100.0% | 86.7% |
| 1/2-13 | 15 | 86.7% | 86.7% | 73.3% |

Sample mistakes (truth -> predicted):

- M3 x 8 hex bolt  ->  M3 x 8 carriage bolt
- M3 x 8 socket head cap screw  ->  M4 x 10 socket head cap screw
- M3 x 8 carriage bolt  ->  M3 x 8 hex bolt
- M3 x 8 button head  ->  M4 x 8 button head
- M3 x 30 hex bolt  ->  M3 x 35 flat head (countersunk)
- M3 x 30 socket head cap screw  ->  M3 x 30 button head
- M3 x 30 button head  ->  M3 x 30 socket head cap screw
- M3 x 60 hex bolt  ->  M3 x 60 carriage bolt
- M3 x 60 button head  ->  M3 x 55 button head
- M4 x 8 hex bolt  ->  #6-32 x 3/8" hex bolt
- M4 x 8 socket head cap screw  ->  M4 x 10 socket head cap screw
- M4 x 8 carriage bolt  ->  #8-32 x 3/8" carriage bolt

### boltnet_v3.onnx on `data/test_catalog_heavy` (281 frames: 225 bolts, 56 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **34.9%** |
| Checkerboard found | 97.5% |
| Bolts recognised as bolts (all bolts) | 87.1% |
| Fully right (all bolts) | 22.2% |
| Right size bin (all bolts) | 8.0% |
| Non-bolts rejected as 'not a bolt' | 85.7% |
| Diameter right (ignoring metric/imperial) | 71.4% |
| Thread exactly right (incl. metric/imperial) | 48.0% |
| Length exactly right | 33.2% |
| Head type right | 70.9% |
| Metric/imperial right | 54.6% |
| Exact size + type (of bolts recognised) | 25.5% |
| Mean diameter error | 0.50 mm |
| Mean length error | 4.6 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 25.6 | 23.1 | 42.3 | 63.3 | 89.2 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.3 |
| network | 11.3 | 11.1 | 12.0 | 13.8 | 14.7 |
| measurement | 2.5 | 3.2 | 4.3 | 4.5 | 4.7 |
| total | 39.1 | 37.0 | 55.6 | 77.9 | 100.6 |

Frames under 100 ms: **99.6%**
Frames at or above 100 ms: **1/281**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 45 | 60.0% | 51.1% | 26.7% |
| socket head cap screw | 45 | 64.4% | 75.6% | 31.1% |
| carriage bolt | 45 | 60.0% | 66.7% | 15.6% |
| flat head (countersunk) | 45 | 64.4% | 57.8% | 28.9% |
| button head | 45 | 62.2% | 57.8% | 8.9% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M3 | 15 | 53.3% | 33.3% | 20.0% |
| M4 | 15 | 46.7% | 46.7% | 20.0% |
| M5 | 15 | 66.7% | 66.7% | 26.7% |
| M6 | 15 | 66.7% | 66.7% | 33.3% |
| M8 | 15 | 80.0% | 73.3% | 26.7% |
| M10 | 15 | 73.3% | 80.0% | 26.7% |
| M12 | 15 | 73.3% | 80.0% | 40.0% |
| #6-32 | 15 | 46.7% | 33.3% | 0.0% |
| #8-32 | 15 | 46.7% | 46.7% | 6.7% |
| #10-24 | 15 | 66.7% | 33.3% | 13.3% |
| 1/4-20 | 15 | 53.3% | 60.0% | 0.0% |
| 5/16-18 | 15 | 86.7% | 66.7% | 6.7% |
| 3/8-16 | 15 | 80.0% | 73.3% | 26.7% |
| 7/16-14 | 15 | 53.3% | 86.7% | 46.7% |
| 1/2-13 | 15 | 40.0% | 80.0% | 40.0% |

Sample mistakes (truth -> predicted):

- M3 x 8 hex bolt  ->  M3 x 8 button head
- M3 x 8 carriage bolt  ->  M6 x 100 socket head cap screw
- M3 x 8 button head  ->  M3 x 10 flat head (countersunk)
- M3 x 30 flat head (countersunk)  ->  #8-32 x 1" socket head cap screw
- M3 x 60 socket head cap screw  ->  M4 x 45 carriage bolt
- M3 x 60 carriage bolt  ->  M3 x 45 carriage bolt
- M3 x 60 flat head (countersunk)  ->  M3 x 55 flat head (countersunk)
- M3 x 60 button head  ->  M3 x 60 carriage bolt
- M4 x 8 socket head cap screw  ->  M4 x 12 socket head cap screw
- M4 x 8 carriage bolt  ->  M3 x 8 carriage bolt
- M4 x 40 hex bolt  ->  #10-24 x 1-1/2" hex bolt
- M4 x 40 carriage bolt  ->  #8-32 x 1-1/4" hex bolt

### boltnet_v3.onnx on `data/test_junk_normal` (200 frames: 0 bolts, 200 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **78.0%** |
| Checkerboard found | 98.5% |
| Bolts recognised as bolts (all bolts) | n/a |
| Fully right (all bolts) | n/a |
| Right size bin (all bolts) | n/a |
| Non-bolts rejected as 'not a bolt' | 78.0% |
| Diameter right (ignoring metric/imperial) | n/a |
| Thread exactly right (incl. metric/imperial) | n/a |
| Length exactly right | n/a |
| Head type right | n/a |
| Metric/imperial right | n/a |
| Exact size + type (of bolts recognised) | n/a |
| Mean diameter error | n/a |
| Mean length error | n/a |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.0 | 22.8 | 42.9 | 68.9 | 78.2 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.3 |
| network | 11.5 | 11.3 | 12.7 | 14.5 | 14.7 |
| measurement | 0.7 | 0.0 | 3.6 | 3.9 | 4.2 |
| total | 38.1 | 35.6 | 55.6 | 80.3 | 91.5 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/200**

### boltnet_v3.onnx on `data/test_junk_heavy` (200 frames: 0 bolts, 200 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **50.0%** |
| Checkerboard found | 94.5% |
| Bolts recognised as bolts (all bolts) | n/a |
| Fully right (all bolts) | n/a |
| Right size bin (all bolts) | n/a |
| Non-bolts rejected as 'not a bolt' | 50.0% |
| Diameter right (ignoring metric/imperial) | n/a |
| Thread exactly right (incl. metric/imperial) | n/a |
| Length exactly right | n/a |
| Head type right | n/a |
| Metric/imperial right | n/a |
| Exact size + type (of bolts recognised) | n/a |
| Mean diameter error | n/a |
| Mean length error | n/a |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.0 | 22.5 | 52.1 | 62.5 | 106.1 |
| rectify | 0.2 | 0.2 | 0.2 | 0.2 | 0.3 |
| network | 11.4 | 11.2 | 12.2 | 13.0 | 34.1 |
| measurement | 1.4 | 0.0 | 4.0 | 4.3 | 8.9 |
| total | 38.4 | 34.9 | 64.4 | 74.4 | 117.7 |

Frames under 100 ms: **99.5%**
Frames at or above 100 ms: **1/200**

### boltnet_v3.onnx on `data/test_ai_normal` (45 frames: 0 bolts, 45 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **73.3%** |
| Checkerboard found | 95.6% |
| Bolts recognised as bolts (all bolts) | n/a |
| Fully right (all bolts) | n/a |
| Right size bin (all bolts) | n/a |
| Non-bolts rejected as 'not a bolt' | 73.3% |
| Diameter right (ignoring metric/imperial) | n/a |
| Thread exactly right (incl. metric/imperial) | n/a |
| Length exactly right | n/a |
| Head type right | n/a |
| Metric/imperial right | n/a |
| Exact size + type (of bolts recognised) | n/a |
| Mean diameter error | n/a |
| Mean length error | n/a |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.6 | 25.5 | 43.9 | 49.4 | 52.4 |
| rectify | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| network | 11.4 | 11.3 | 12.6 | 13.3 | 13.5 |
| measurement | 0.7 | 0.0 | 3.4 | 3.7 | 3.8 |
| total | 38.4 | 38.1 | 55.9 | 61.9 | 64.1 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/45**

### boltnet_v3.onnx on `data/test_ai_heavy` (45 frames: 0 bolts, 45 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **53.3%** |
| Checkerboard found | 93.3% |
| Bolts recognised as bolts (all bolts) | n/a |
| Fully right (all bolts) | n/a |
| Right size bin (all bolts) | n/a |
| Non-bolts rejected as 'not a bolt' | 53.3% |
| Diameter right (ignoring metric/imperial) | n/a |
| Thread exactly right (incl. metric/imperial) | n/a |
| Length exactly right | n/a |
| Head type right | n/a |
| Metric/imperial right | n/a |
| Exact size + type (of bolts recognised) | n/a |
| Mean diameter error | n/a |
| Mean length error | n/a |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 25.8 | 21.2 | 57.2 | 60.5 | 61.0 |
| rectify | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| network | 11.3 | 11.2 | 12.0 | 13.8 | 14.7 |
| measurement | 1.3 | 0.0 | 3.6 | 3.9 | 4.0 |
| total | 37.7 | 33.6 | 72.9 | 73.3 | 73.4 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/45**

### boltnet_v3.onnx on `data/test_webhold_normal` (295 frames: 120 bolts, 175 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **51.5%** |
| Checkerboard found | 97.3% |
| Bolts recognised as bolts (all bolts) | 75.8% |
| Fully right (all bolts) | 1.7% |
| Right size bin (all bolts) | 0.0% |
| Non-bolts rejected as 'not a bolt' | 85.7% |
| Diameter right (ignoring metric/imperial) | 74.7% |
| Thread exactly right (incl. metric/imperial) | 67.0% |
| Length exactly right | 7.7% |
| Head type right | 46.2% |
| Metric/imperial right | 74.7% |
| Exact size + type (of bolts recognised) | 2.2% |
| Mean diameter error | 0.47 mm |
| Mean length error | 6.8 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.4 | 23.4 | 47.2 | 73.9 | 83.7 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.5 |
| network | 11.4 | 11.2 | 12.2 | 13.7 | 17.5 |
| measurement | 1.3 | 0.0 | 4.0 | 4.1 | 4.9 |
| total | 38.9 | 36.7 | 59.4 | 85.9 | 97.9 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/295**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 48 | 85.4% | 50.0% | 2.1% |
| socket head cap screw | 24 | 70.8% | 29.2% | 0.0% |
| button head | 24 | 25.0% | 41.7% | 0.0% |
| carriage bolt | 12 | 8.3% | 8.3% | 8.3% |
| flat head (countersunk) | 12 | 25.0% | 0.0% | 0.0% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M12 | 32 | 53.1% | 46.9% | 0.0% |
| M10 | 24 | 66.7% | 29.2% | 0.0% |
| M6 | 15 | 80.0% | 33.3% | 13.3% |
| M8 | 12 | 75.0% | 50.0% | 0.0% |
| M3 | 6 | 66.7% | 33.3% | 0.0% |
| #6-32 | 9 | 33.3% | 22.2% | 0.0% |
| 1/2-13 | 5 | 20.0% | 0.0% | 0.0% |
| M5 | 5 | 60.0% | 20.0% | 0.0% |
| M4 | 2 | 50.0% | 0.0% | 0.0% |
| #8-32 | 3 | 33.3% | 33.3% | 0.0% |
| 7/16-14 | 6 | 0.0% | 50.0% | 0.0% |
| 1/4-20 | 1 | 100.0% | 0.0% | 0.0% |

Sample mistakes (truth -> predicted):

- M10 x 45 hex bolt  ->  M10 x 40 button head
- M12 x 55 hex bolt  ->  M12 x 45 hex bolt
- M12 x 55 hex bolt  ->  M12 x 50 hex bolt
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M10 x 45 hex bolt  ->  M10 x 40 hex bolt
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M12 x 55 hex bolt  ->  M12 x 45 hex bolt
- M12 x 55 hex bolt  ->  M12 x 45 hex bolt
- M12 x 55 hex bolt  ->  M12 x 40 button head
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M6 x 25 hex bolt  ->  M6 x 25 carriage bolt
- M6 x 25 hex bolt  ->  M6 x 20 hex bolt

### boltnet_v3.onnx on `data/test_webhold_heavy` (295 frames: 120 bolts, 175 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **48.1%** |
| Checkerboard found | 96.3% |
| Bolts recognised as bolts (all bolts) | 77.5% |
| Fully right (all bolts) | 0.8% |
| Right size bin (all bolts) | 0.0% |
| Non-bolts rejected as 'not a bolt' | 80.6% |
| Diameter right (ignoring metric/imperial) | 59.1% |
| Thread exactly right (incl. metric/imperial) | 48.4% |
| Length exactly right | 4.3% |
| Head type right | 36.6% |
| Metric/imperial right | 64.5% |
| Exact size + type (of bolts recognised) | 1.1% |
| Mean diameter error | 0.71 mm |
| Mean length error | 7.8 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 25.1 | 21.9 | 40.2 | 53.3 | 149.8 |
| rectify | 0.2 | 0.2 | 0.2 | 0.2 | 0.3 |
| network | 11.3 | 11.2 | 12.1 | 13.2 | 14.7 |
| measurement | 1.4 | 0.0 | 3.9 | 4.1 | 4.4 |
| total | 37.4 | 35.1 | 53.5 | 67.6 | 164.0 |

Frames under 100 ms: **99.3%**
Frames at or above 100 ms: **2/295**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 48 | 70.8% | 43.8% | 2.1% |
| socket head cap screw | 24 | 45.8% | 12.5% | 0.0% |
| button head | 24 | 20.8% | 41.7% | 0.0% |
| carriage bolt | 12 | 8.3% | 0.0% | 0.0% |
| flat head (countersunk) | 12 | 33.3% | 0.0% | 0.0% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M12 | 35 | 45.7% | 25.7% | 2.9% |
| M10 | 25 | 56.0% | 28.0% | 0.0% |
| M8 | 15 | 60.0% | 46.7% | 0.0% |
| M6 | 8 | 62.5% | 37.5% | 0.0% |
| M3 | 6 | 50.0% | 16.7% | 0.0% |
| #6-32 | 7 | 14.3% | 14.3% | 0.0% |
| 1/2-13 | 5 | 20.0% | 20.0% | 0.0% |
| M5 | 4 | 75.0% | 0.0% | 0.0% |
| M4 | 5 | 40.0% | 20.0% | 0.0% |
| #8-32 | 3 | 0.0% | 66.7% | 0.0% |
| 7/16-14 | 6 | 0.0% | 33.3% | 0.0% |
| 1/4-20 | 1 | 100.0% | 0.0% | 0.0% |

Sample mistakes (truth -> predicted):

- M12 x 55 hex bolt  ->  M12 x 50 socket head cap screw
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M10 x 45 hex bolt  ->  M10 x 40 button head
- M10 x 45 hex bolt  ->  7/16-14 x 1-1/2" hex bolt
- M10 x 45 hex bolt  ->  M10 x 40 hex bolt
- M12 x 55 hex bolt  ->  1/2-13 x 1-3/4" hex bolt
- M10 x 45 hex bolt  ->  M10 x 40 hex bolt
- M12 x 55 hex bolt  ->  M12 x 50 button head
- M12 x 55 hex bolt  ->  M12 x 45 hex bolt
- M10 x 45 hex bolt  ->  M10 x 35 button head
- M10 x 45 hex bolt  ->  M10 x 40 hex bolt
