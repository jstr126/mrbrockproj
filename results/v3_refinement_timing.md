# Bolt sizer benchmark

Host: macOS-26.6.2-arm64-arm-64bit-Mach-O; CPU threads: 2
19:30  up 10 days,  8:13, 3 users, load averages: 2.00 3.90 3.80

### boltnet_v3.onnx on `data/v3_fresh_normal` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **72.2%** |
| Checkerboard found | 98.2% |
| Bolts recognised as bolts (all bolts) | 96.0% |
| Fully right (all bolts) | 65.7% |
| Right size bin (all bolts) | 35.3% |
| Non-bolts rejected as 'not a bolt' | 92.0% |
| Diameter right (ignoring metric/imperial) | 90.3% |
| Thread exactly right (incl. metric/imperial) | 77.1% |
| Length exactly right | 75.7% |
| Head type right | 91.0% |
| Metric/imperial right | 82.6% |
| Exact size + type (of bolts recognised) | 68.4% |
| Mean diameter error | 0.30 mm |
| Mean length error | 1.5 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 30.6 | 25.7 | 60.0 | 86.2 | 224.9 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 0.5 |
| network | 13.8 | 11.6 | 22.1 | 22.9 | 26.7 |
| measurement | 3.3 | 3.6 | 6.3 | 8.5 | 14.0 |
| total | 47.5 | 42.4 | 81.5 | 109.2 | 244.1 |

Frames under 100 ms: **98.0%**
Frames at or above 100 ms: **8/400**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| socket head cap screw | 48 | 85.4% | 89.6% | 64.6% |
| flat head (countersunk) | 52 | 80.8% | 73.1% | 57.7% |
| button head | 71 | 84.5% | 85.9% | 59.2% |
| carriage bolt | 70 | 88.6% | 95.7% | 72.9% |
| hex bolt | 59 | 93.2% | 89.8% | 72.9% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M8 | 21 | 95.2% | 95.2% | 81.0% |
| M10 | 23 | 95.7% | 100.0% | 87.0% |
| M6 | 26 | 96.2% | 88.5% | 73.1% |
| 3/8-16 | 18 | 100.0% | 100.0% | 94.4% |
| 5/16-18 | 21 | 85.7% | 85.7% | 76.2% |
| 1/4-20 | 16 | 100.0% | 93.8% | 68.8% |
| 7/16-14 | 20 | 75.0% | 90.0% | 75.0% |
| M3 | 16 | 62.5% | 37.5% | 25.0% |
| 1/2-13 | 21 | 90.5% | 100.0% | 90.5% |
| M4 | 27 | 81.5% | 81.5% | 44.4% |
| #8-32 | 25 | 76.0% | 88.0% | 28.0% |
| M12 | 18 | 100.0% | 100.0% | 88.9% |
| M5 | 13 | 84.6% | 76.9% | 69.2% |
| #6-32 | 20 | 65.0% | 80.0% | 25.0% |
| #10-24 | 15 | 93.3% | 80.0% | 66.7% |

Sample mistakes (truth -> predicted):

- M6 x 60 button head  ->  M6 x 55 button head
- M8 x 55 carriage bolt  ->  M8 x 60 carriage bolt
- 1/4-20 x 4" flat head (countersunk)  ->  1/4-20 x 4" hex bolt
- 7/16-14 x 2-1/2" socket head cap screw  ->  3/8-16 x 2-1/2" socket head cap screw
- 1/4-20 x 3/4" flat head (countersunk)  ->  M6 x 20 flat head (countersunk)
- M3 x 12 flat head (countersunk)  ->  #6-32 x 1/2" flat head (countersunk)
- M4 x 16 hex bolt  ->  #6-32 x 5/8" hex bolt
- M6 x 50 button head  ->  M5 x 55 flat head (countersunk)
- #8-32 x 1-3/4" hex bolt  ->  #10-24 x 1-3/4" hex bolt
- M5 x 12 button head  ->  M6 x 12 button head
- #8-32 x 2-1/2" button head  ->  M4 x 65 button head
- #6-32 x 2-1/2" socket head cap screw  ->  M4 x 65 hex bolt

### boltnet_v3.onnx on `data/v3_fresh_heavy` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **39.0%** |
| Checkerboard found | 97.5% |
| Bolts recognised as bolts (all bolts) | 84.7% |
| Fully right (all bolts) | 25.0% |
| Right size bin (all bolts) | 8.0% |
| Non-bolts rejected as 'not a bolt' | 81.0% |
| Diameter right (ignoring metric/imperial) | 69.3% |
| Thread exactly right (incl. metric/imperial) | 42.1% |
| Length exactly right | 40.9% |
| Head type right | 69.7% |
| Metric/imperial right | 55.1% |
| Exact size + type (of bolts recognised) | 29.5% |
| Mean diameter error | 0.52 mm |
| Mean length error | 3.1 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 35.4 | 32.1 | 59.5 | 80.5 | 112.2 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 | 1.5 |
| network | 16.2 | 15.4 | 17.6 | 22.2 | 27.1 |
| measurement | 3.3 | 4.4 | 6.1 | 6.7 | 8.3 |
| total | 54.6 | 51.8 | 80.0 | 99.0 | 131.8 |

Frames under 100 ms: **99.0%**
Frames at or above 100 ms: **4/400**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| button head | 67 | 61.2% | 49.3% | 25.4% |
| hex bolt | 49 | 65.3% | 59.2% | 30.6% |
| flat head (countersunk) | 58 | 58.6% | 62.1% | 27.6% |
| carriage bolt | 58 | 55.2% | 56.9% | 22.4% |
| socket head cap screw | 68 | 54.4% | 67.6% | 20.6% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| 5/16-18 | 18 | 77.8% | 72.2% | 38.9% |
| M12 | 13 | 46.2% | 69.2% | 38.5% |
| M5 | 25 | 64.0% | 64.0% | 20.0% |
| M6 | 19 | 42.1% | 57.9% | 21.1% |
| #10-24 | 15 | 46.7% | 40.0% | 6.7% |
| M4 | 32 | 50.0% | 31.2% | 3.1% |
| 7/16-14 | 22 | 68.2% | 86.4% | 50.0% |
| M10 | 18 | 94.4% | 88.9% | 55.6% |
| #6-32 | 19 | 31.6% | 26.3% | 5.3% |
| 3/8-16 | 28 | 71.4% | 78.6% | 25.0% |
| M8 | 19 | 68.4% | 57.9% | 42.1% |
| 1/2-13 | 17 | 41.2% | 82.4% | 35.3% |
| #8-32 | 17 | 52.9% | 47.1% | 11.8% |
| M3 | 13 | 30.8% | 7.7% | 7.7% |
| 1/4-20 | 25 | 72.0% | 64.0% | 24.0% |

Sample mistakes (truth -> predicted):

- 5/16-18 x 3" button head  ->  M8 x 70 hex bolt
- M5 x 45 hex bolt  ->  #10-24 x 1-3/4" flat head (countersunk)
- M6 x 30 flat head (countersunk)  ->  M8 x 30 flat head (countersunk)
- M6 x 20 carriage bolt  ->  #10-24 x 3/4" hex bolt
- M10 x 50 hex bolt  ->  M8 x 55 socket head cap screw
- 3/8-16 x 1-3/4" button head  ->  M8 x 50 flat head (countersunk)
- M8 x 65 hex bolt  ->  5/16-18 x 2-1/2" hex bolt
- 1/2-13 x 1-1/4" button head  ->  M12 x 30 button head
- #8-32 x 3/8" flat head (countersunk)  ->  M5 x 12 button head
- M5 x 65 carriage bolt  ->  M6 x 65 carriage bolt
- M5 x 30 flat head (countersunk)  ->  #10-24 x 1" button head
- M3 x 60 socket head cap screw  ->  M4 x 60 flat head (countersunk)

### boltnet_v3_refined.onnx on `data/v3_fresh_normal` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **74.5%** |
| Checkerboard found | 98.0% |
| Bolts recognised as bolts (all bolts) | 95.7% |
| Fully right (all bolts) | 68.0% |
| Right size bin (all bolts) | 37.0% |
| Non-bolts rejected as 'not a bolt' | 94.0% |
| Diameter right (ignoring metric/imperial) | 89.2% |
| Thread exactly right (incl. metric/imperial) | 80.5% |
| Length exactly right | 79.4% |
| Head type right | 90.9% |
| Metric/imperial right | 86.4% |
| Exact size + type (of bolts recognised) | 71.1% |
| Mean diameter error | 0.31 mm |
| Mean length error | 1.8 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 26.2 | 22.9 | 45.5 | 77.9 | 218.8 |
| rectify | 0.2 | 0.2 | 0.2 | 0.4 | 0.6 |
| network | 11.7 | 10.9 | 16.7 | 21.7 | 35.5 |
| measurement | 2.7 | 3.3 | 5.3 | 6.6 | 9.8 |
| total | 40.5 | 36.8 | 61.7 | 96.1 | 236.6 |

Frames under 100 ms: **99.2%**
Frames at or above 100 ms: **3/400**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| socket head cap screw | 48 | 81.2% | 89.6% | 64.6% |
| flat head (countersunk) | 52 | 78.8% | 75.0% | 63.5% |
| button head | 71 | 87.3% | 85.9% | 64.8% |
| carriage bolt | 70 | 85.7% | 92.9% | 72.9% |
| hex bolt | 59 | 91.5% | 89.8% | 72.9% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M8 | 21 | 95.2% | 95.2% | 85.7% |
| M10 | 23 | 95.7% | 100.0% | 87.0% |
| M6 | 26 | 100.0% | 92.3% | 80.8% |
| 3/8-16 | 18 | 100.0% | 100.0% | 94.4% |
| 5/16-18 | 21 | 85.7% | 90.5% | 71.4% |
| 1/4-20 | 16 | 93.8% | 87.5% | 81.2% |
| 7/16-14 | 20 | 75.0% | 90.0% | 70.0% |
| M3 | 16 | 56.2% | 37.5% | 18.8% |
| 1/2-13 | 21 | 85.7% | 95.2% | 76.2% |
| M4 | 27 | 85.2% | 74.1% | 44.4% |
| #8-32 | 25 | 84.0% | 88.0% | 48.0% |
| M12 | 18 | 94.4% | 100.0% | 88.9% |
| M5 | 13 | 76.9% | 84.6% | 69.2% |
| #6-32 | 20 | 55.0% | 80.0% | 35.0% |
| #10-24 | 15 | 86.7% | 80.0% | 73.3% |

Sample mistakes (truth -> predicted):

- M6 x 60 button head  ->  M6 x 55 button head
- M8 x 55 carriage bolt  ->  5/16-18 x 2-1/4" carriage bolt
- 5/16-18 x 1" flat head (countersunk)  ->  3/8-16 x 2" button head
- 1/4-20 x 4" flat head (countersunk)  ->  1/4-20 x 4" hex bolt
- 7/16-14 x 2-1/2" socket head cap screw  ->  3/8-16 x 2-1/2" socket head cap screw
- 1/4-20 x 3/4" flat head (countersunk)  ->  M6 x 20 flat head (countersunk)
- M3 x 12 flat head (countersunk)  ->  M4 x 12 button head
- M4 x 16 hex bolt  ->  #6-32 x 5/8" hex bolt
- M6 x 50 button head  ->  M6 x 55 flat head (countersunk)
- #8-32 x 1-3/4" hex bolt  ->  #10-24 x 1-3/4" hex bolt
- M5 x 12 button head  ->  M6 x 12 button head
- #8-32 x 2-1/2" button head  ->  M4 x 65 button head

### boltnet_v3_refined.onnx on `data/v3_fresh_heavy` (400 frames: 300 bolts, 100 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **42.8%** |
| Checkerboard found | 96.2% |
| Bolts recognised as bolts (all bolts) | 83.3% |
| Fully right (all bolts) | 30.3% |
| Right size bin (all bolts) | 7.0% |
| Non-bolts rejected as 'not a bolt' | 80.0% |
| Diameter right (ignoring metric/imperial) | 72.0% |
| Thread exactly right (incl. metric/imperial) | 49.6% |
| Length exactly right | 48.0% |
| Head type right | 68.4% |
| Metric/imperial right | 60.8% |
| Exact size + type (of bolts recognised) | 36.4% |
| Mean diameter error | 0.50 mm |
| Mean length error | 3.3 mm |

| Time per frame (ms) | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| detect | 23.9 | 22.0 | 40.4 | 49.9 | 75.6 |
| rectify | 0.1 | 0.1 | 0.2 | 0.2 | 0.3 |
| network | 10.8 | 10.9 | 11.0 | 11.1 | 14.1 |
| measurement | 2.2 | 3.0 | 4.0 | 4.3 | 4.7 |
| total | 36.6 | 34.7 | 54.4 | 62.7 | 89.0 |

Frames under 100 ms: **100.0%**
Frames at or above 100 ms: **0/400**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| button head | 67 | 61.2% | 50.7% | 29.9% |
| hex bolt | 49 | 67.3% | 59.2% | 40.8% |
| flat head (countersunk) | 58 | 63.8% | 53.4% | 27.6% |
| carriage bolt | 58 | 50.0% | 56.9% | 20.7% |
| socket head cap screw | 68 | 58.8% | 64.7% | 33.8% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| 5/16-18 | 18 | 72.2% | 72.2% | 44.4% |
| M12 | 13 | 46.2% | 61.5% | 38.5% |
| M5 | 25 | 56.0% | 60.0% | 24.0% |
| M6 | 19 | 52.6% | 52.6% | 26.3% |
| #10-24 | 15 | 53.3% | 33.3% | 13.3% |
| M4 | 32 | 50.0% | 34.4% | 0.0% |
| 7/16-14 | 22 | 68.2% | 86.4% | 45.5% |
| M10 | 18 | 83.3% | 77.8% | 66.7% |
| #6-32 | 19 | 47.4% | 26.3% | 10.5% |
| 3/8-16 | 28 | 78.6% | 75.0% | 42.9% |
| M8 | 19 | 73.7% | 63.2% | 36.8% |
| 1/2-13 | 17 | 47.1% | 76.5% | 41.2% |
| #8-32 | 17 | 41.2% | 47.1% | 17.6% |
| M3 | 13 | 38.5% | 23.1% | 23.1% |
| 1/4-20 | 25 | 72.0% | 56.0% | 36.0% |

Sample mistakes (truth -> predicted):

- 5/16-18 x 3" button head  ->  5/16-18 x 3" hex bolt
- M5 x 45 hex bolt  ->  M5 x 45 flat head (countersunk)
- M6 x 30 flat head (countersunk)  ->  1/4-20 x 1-1/4" flat head (countersunk)
- M4 x 16 carriage bolt  ->  #8-32 x 5/8" carriage bolt
- M6 x 20 carriage bolt  ->  M5 x 20 hex bolt
- M10 x 50 hex bolt  ->  5/16-18 x 2" socket head cap screw
- 3/8-16 x 1-3/4" button head  ->  M8 x 40 button head
- 1/2-13 x 1-1/4" button head  ->  M12 x 30 button head
- M8 x 90 carriage bolt  ->  5/16-18 x 3-1/2" carriage bolt
- M4 x 65 carriage bolt  ->  #8-32 x 2-1/2" carriage bolt
- M5 x 65 carriage bolt  ->  M6 x 65 carriage bolt
- M5 x 70 socket head cap screw  ->  M6 x 70 socket head cap screw
