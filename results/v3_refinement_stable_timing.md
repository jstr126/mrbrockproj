# Bolt sizer benchmark

Host: macOS-26.6.2-arm64-arm-64bit-Mach-O; CPU threads: 2
23:12  up 10 days, 11:55, 3 users, load averages: 4.48 9.57 6.94

### boltnet_v3.onnx on `data/v3_fresh_normal` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **72.5%** |
| Checkerboard found | 98.5% |
| Bolts recognised as bolts (all bolts) | 96.3% |
| Fully right (all bolts) | 65.3% |
| Right size bin (all bolts) | 34.0% |
| Non-bolts rejected as 'not a bolt' | 94.0% |
| Diameter right (ignoring metric/imperial) | 87.9% |
| Thread exactly right (incl. metric/imperial) | 76.5% |
| Length exactly right | 76.8% |
| Head type right | 89.6% |
| Metric/imperial right | 84.1% |
| Exact size + type (of bolts recognised) | 67.8% |
| Mean diameter error | 0.30 mm |
| Mean length error | 1.8 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 35.5 | 30.7 | 66.1 | 92.6 | 145.0 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.3 |
| network | 15.9 | 15.5 | 17.4 | 17.5 | 23.4 |
| measurement | 3.7 | 4.8 | 6.1 | 6.5 | 12.3 |
| total | 55.1 | 51.0 | 86.4 | 111.7 | 162.5 |

Frames under 100 ms: **97.2%**
Frames at or above 100 ms: **11/400**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| socket head cap screw | 48 | 79.2% | 87.5% | 60.4% |
| flat head (countersunk) | 52 | 82.7% | 73.1% | 65.4% |
| button head | 71 | 81.7% | 85.9% | 60.6% |
| carriage bolt | 70 | 87.1% | 92.9% | 67.1% |
| hex bolt | 59 | 91.5% | 89.8% | 72.9% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M8 | 21 | 90.5% | 90.5% | 76.2% |
| M10 | 23 | 95.7% | 100.0% | 91.3% |
| M6 | 26 | 92.3% | 88.5% | 76.9% |
| 3/8-16 | 18 | 100.0% | 100.0% | 94.4% |
| 5/16-18 | 21 | 85.7% | 90.5% | 81.0% |
| 1/4-20 | 16 | 93.8% | 87.5% | 68.8% |
| 7/16-14 | 20 | 70.0% | 85.0% | 65.0% |
| M3 | 16 | 87.5% | 31.2% | 25.0% |
| 1/2-13 | 21 | 90.5% | 100.0% | 81.0% |
| M4 | 27 | 88.9% | 77.8% | 48.1% |
| #8-32 | 25 | 68.0% | 84.0% | 28.0% |
| M12 | 18 | 94.4% | 100.0% | 83.3% |
| M5 | 13 | 69.2% | 84.6% | 69.2% |
| #6-32 | 20 | 55.0% | 85.0% | 25.0% |
| #10-24 | 15 | 86.7% | 80.0% | 73.3% |

Sample mistakes (truth -> predicted):

- M6 x 60 button head  ->  M6 x 55 button head
- M8 x 55 carriage bolt  ->  M8 x 60 carriage bolt
- 5/16-18 x 1" flat head (countersunk)  ->  3/8-16 x 2" button head
- 1/4-20 x 4" flat head (countersunk)  ->  1/4-20 x 4" hex bolt
- 7/16-14 x 2-1/2" socket head cap screw  ->  3/8-16 x 2-1/2" socket head cap screw
- M3 x 25 button head  ->  M3 x 25 hex bolt
- 1/4-20 x 3/4" flat head (countersunk)  ->  M6 x 20 flat head (countersunk)
- M3 x 12 flat head (countersunk)  ->  M4 x 12 button head
- M4 x 16 hex bolt  ->  #6-32 x 5/8" hex bolt
- M6 x 50 button head  ->  M5 x 55 flat head (countersunk)
- #8-32 x 1-3/4" hex bolt  ->  #10-24 x 1-3/4" hex bolt
- M5 x 12 button head  ->  M6 x 12 button head

### boltnet_v3.onnx on `data/v3_fresh_heavy` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **38.0%** |
| Checkerboard found | 96.8% |
| Bolts recognised as bolts (all bolts) | 85.0% |
| Fully right (all bolts) | 25.0% |
| Right size bin (all bolts) | 7.7% |
| Non-bolts rejected as 'not a bolt' | 77.0% |
| Diameter right (ignoring metric/imperial) | 69.0% |
| Thread exactly right (incl. metric/imperial) | 41.2% |
| Length exactly right | 40.0% |
| Head type right | 68.2% |
| Metric/imperial right | 54.1% |
| Exact size + type (of bolts recognised) | 29.4% |
| Mean diameter error | 0.54 mm |
| Mean length error | 3.3 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 37.9 | 34.9 | 66.4 | 100.7 | 226.2 |
| rectify | 0.2 | 0.2 | 0.3 | 0.5 | 0.5 |
| network | 17.5 | 15.5 | 26.9 | 33.8 | 33.8 |
| measurement | 3.5 | 4.2 | 7.5 | 10.7 | 11.7 |
| total | 58.5 | 54.5 | 95.7 | 134.6 | 250.4 |

Frames under 100 ms: **95.8%**
Frames at or above 100 ms: **17/400**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| button head | 67 | 59.7% | 52.2% | 26.9% |
| hex bolt | 49 | 61.2% | 53.1% | 30.6% |
| flat head (countersunk) | 58 | 58.6% | 56.9% | 24.1% |
| carriage bolt | 58 | 58.6% | 60.3% | 22.4% |
| socket head cap screw | 68 | 55.9% | 66.2% | 22.1% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| 5/16-18 | 18 | 77.8% | 66.7% | 38.9% |
| M12 | 13 | 38.5% | 61.5% | 30.8% |
| M5 | 25 | 64.0% | 60.0% | 20.0% |
| M6 | 19 | 42.1% | 57.9% | 21.1% |
| #10-24 | 15 | 53.3% | 33.3% | 6.7% |
| M4 | 32 | 46.9% | 34.4% | 6.2% |
| 7/16-14 | 22 | 68.2% | 86.4% | 50.0% |
| M10 | 18 | 77.8% | 72.2% | 44.4% |
| #6-32 | 19 | 31.6% | 26.3% | 5.3% |
| 3/8-16 | 28 | 78.6% | 78.6% | 21.4% |
| M8 | 19 | 73.7% | 63.2% | 42.1% |
| 1/2-13 | 17 | 41.2% | 82.4% | 41.2% |
| #8-32 | 17 | 52.9% | 47.1% | 11.8% |
| M3 | 13 | 38.5% | 15.4% | 15.4% |
| 1/4-20 | 25 | 72.0% | 68.0% | 28.0% |

Sample mistakes (truth -> predicted):

- 5/16-18 x 3" button head  ->  M8 x 70 hex bolt
- M5 x 45 hex bolt  ->  #10-24 x 1-3/4" flat head (countersunk)
- M6 x 30 flat head (countersunk)  ->  M8 x 30 flat head (countersunk)
- M4 x 16 carriage bolt  ->  #8-32 x 1/2" carriage bolt
- M6 x 20 carriage bolt  ->  #10-24 x 3/4" hex bolt
- M10 x 50 hex bolt  ->  M8 x 55 socket head cap screw
- 3/8-16 x 1-3/4" button head  ->  5/16-18 x 1-3/4" button head
- 1/2-13 x 1-1/4" button head  ->  M12 x 30 button head
- M8 x 90 carriage bolt  ->  5/16-18 x 3-1/2" carriage bolt
- #8-32 x 3/8" flat head (countersunk)  ->  #10-24 x 3/8" button head
- M5 x 65 carriage bolt  ->  M6 x 65 carriage bolt
- M5 x 30 flat head (countersunk)  ->  #10-24 x 1" button head

### boltnet_v3_refined.onnx on `data/v3_fresh_normal` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **75.0%** |
| Checkerboard found | 98.5% |
| Bolts recognised as bolts (all bolts) | 96.3% |
| Fully right (all bolts) | 68.7% |
| Right size bin (all bolts) | 36.7% |
| Non-bolts rejected as 'not a bolt' | 94.0% |
| Diameter right (ignoring metric/imperial) | 88.2% |
| Thread exactly right (incl. metric/imperial) | 79.6% |
| Length exactly right | 79.2% |
| Head type right | 89.6% |
| Metric/imperial right | 85.8% |
| Exact size + type (of bolts recognised) | 71.3% |
| Mean diameter error | 0.31 mm |
| Mean length error | 1.7 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 38.7 | 32.0 | 82.6 | 117.2 | 261.2 |
| rectify | 0.2 | 0.2 | 0.3 | 0.6 | 1.3 |
| network | 17.2 | 15.4 | 26.8 | 43.0 | 67.7 |
| measurement | 4.0 | 3.8 | 8.4 | 11.9 | 20.9 |
| total | 59.7 | 54.2 | 112.6 | 183.1 | 330.2 |

Frames under 100 ms: **91.8%**
Frames at or above 100 ms: **33/400**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| socket head cap screw | 48 | 81.2% | 87.5% | 68.8% |
| flat head (countersunk) | 52 | 80.8% | 73.1% | 65.4% |
| button head | 71 | 84.5% | 85.9% | 63.4% |
| carriage bolt | 70 | 87.1% | 92.9% | 72.9% |
| hex bolt | 59 | 89.8% | 89.8% | 72.9% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M8 | 21 | 90.5% | 90.5% | 81.0% |
| M10 | 23 | 95.7% | 100.0% | 91.3% |
| M6 | 26 | 96.2% | 88.5% | 76.9% |
| 3/8-16 | 18 | 100.0% | 100.0% | 94.4% |
| 5/16-18 | 21 | 85.7% | 90.5% | 76.2% |
| 1/4-20 | 16 | 93.8% | 87.5% | 81.2% |
| 7/16-14 | 20 | 70.0% | 85.0% | 65.0% |
| M3 | 16 | 75.0% | 31.2% | 25.0% |
| 1/2-13 | 21 | 90.5% | 100.0% | 81.0% |
| M4 | 27 | 88.9% | 77.8% | 51.9% |
| #8-32 | 25 | 72.0% | 84.0% | 40.0% |
| M12 | 18 | 100.0% | 100.0% | 94.4% |
| M5 | 13 | 69.2% | 84.6% | 69.2% |
| #6-32 | 20 | 55.0% | 85.0% | 35.0% |
| #10-24 | 15 | 86.7% | 80.0% | 73.3% |

Sample mistakes (truth -> predicted):

- M6 x 60 button head  ->  M6 x 55 button head
- M8 x 55 carriage bolt  ->  5/16-18 x 2-1/4" carriage bolt
- 5/16-18 x 1" flat head (countersunk)  ->  3/8-16 x 2" button head
- 1/4-20 x 4" flat head (countersunk)  ->  1/4-20 x 4" hex bolt
- 7/16-14 x 2-1/2" socket head cap screw  ->  3/8-16 x 2-1/2" socket head cap screw
- M3 x 25 button head  ->  M3 x 25 hex bolt
- 1/4-20 x 3/4" flat head (countersunk)  ->  M6 x 20 flat head (countersunk)
- M3 x 12 flat head (countersunk)  ->  M4 x 12 button head
- M4 x 16 hex bolt  ->  #6-32 x 5/8" hex bolt
- M6 x 50 button head  ->  M6 x 55 flat head (countersunk)
- #8-32 x 1-3/4" hex bolt  ->  #10-24 x 1-3/4" hex bolt
- M5 x 12 button head  ->  M6 x 12 button head

### boltnet_v3_refined.onnx on `data/v3_fresh_heavy` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **43.2%** |
| Checkerboard found | 96.8% |
| Bolts recognised as bolts (all bolts) | 85.0% |
| Fully right (all bolts) | 32.0% |
| Right size bin (all bolts) | 7.7% |
| Non-bolts rejected as 'not a bolt' | 77.0% |
| Diameter right (ignoring metric/imperial) | 69.8% |
| Thread exactly right (incl. metric/imperial) | 48.6% |
| Length exactly right | 47.8% |
| Head type right | 68.2% |
| Metric/imperial right | 61.2% |
| Exact size + type (of bolts recognised) | 37.6% |
| Mean diameter error | 0.54 mm |
| Mean length error | 3.5 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 24.3 | 22.3 | 40.4 | 49.9 | 75.1 |
| rectify | 0.2 | 0.2 | 0.2 | 0.2 | 0.3 |
| network | 10.9 | 11.0 | 11.1 | 11.7 | 13.7 |
| measurement | 2.2 | 3.1 | 3.9 | 4.2 | 5.4 |
| total | 37.1 | 35.5 | 53.8 | 62.5 | 88.6 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/400**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| button head | 67 | 61.2% | 52.2% | 32.8% |
| hex bolt | 49 | 63.3% | 53.1% | 38.8% |
| flat head (countersunk) | 58 | 63.8% | 56.9% | 31.0% |
| carriage bolt | 58 | 50.0% | 60.3% | 22.4% |
| socket head cap screw | 68 | 58.8% | 66.2% | 35.3% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| 5/16-18 | 18 | 72.2% | 66.7% | 38.9% |
| M12 | 13 | 38.5% | 61.5% | 30.8% |
| M5 | 25 | 52.0% | 60.0% | 24.0% |
| M6 | 19 | 52.6% | 57.9% | 31.6% |
| #10-24 | 15 | 53.3% | 33.3% | 13.3% |
| M4 | 32 | 46.9% | 34.4% | 6.2% |
| 7/16-14 | 22 | 68.2% | 86.4% | 50.0% |
| M10 | 18 | 77.8% | 72.2% | 66.7% |
| #6-32 | 19 | 47.4% | 26.3% | 10.5% |
| 3/8-16 | 28 | 78.6% | 78.6% | 46.4% |
| M8 | 19 | 73.7% | 63.2% | 36.8% |
| 1/2-13 | 17 | 52.9% | 82.4% | 52.9% |
| #8-32 | 17 | 47.1% | 47.1% | 17.6% |
| M3 | 13 | 38.5% | 15.4% | 15.4% |
| 1/4-20 | 25 | 72.0% | 68.0% | 40.0% |

Sample mistakes (truth -> predicted):

- 5/16-18 x 3" button head  ->  5/16-18 x 3" hex bolt
- M5 x 45 hex bolt  ->  M5 x 45 flat head (countersunk)
- M6 x 30 flat head (countersunk)  ->  1/4-20 x 1-1/4" flat head (countersunk)
- M4 x 16 carriage bolt  ->  #8-32 x 1/2" carriage bolt
- M6 x 20 carriage bolt  ->  M5 x 20 hex bolt
- M10 x 50 hex bolt  ->  5/16-18 x 2" socket head cap screw
- 3/8-16 x 1-3/4" button head  ->  M8 x 40 button head
- 1/2-13 x 1-1/4" button head  ->  M12 x 30 button head
- M8 x 90 carriage bolt  ->  5/16-18 x 3-1/2" carriage bolt
- #8-32 x 3/8" flat head (countersunk)  ->  M6 x 10 button head
- M4 x 65 carriage bolt  ->  #8-32 x 2-1/2" carriage bolt
- M5 x 65 carriage bolt  ->  M6 x 65 carriage bolt
