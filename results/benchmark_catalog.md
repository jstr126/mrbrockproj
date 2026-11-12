# Bolt sizer benchmark

### boltnet.onnx on `data/test_catalog_normal` (281 frames: 225 bolts, 56 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **61.2%** |
| Checkerboard found | 99.6% |
| Bolts recognised as bolts | 96.9% |
| Non-bolts rejected as 'not a bolt' | 98.2% |
| Diameter right (ignoring metric/imperial) | 88.9% |
| Thread exactly right (incl. metric/imperial) | 75.6% |
| Length exactly right | 60.4% |
| Head type right | 91.2% |
| Metric/imperial right | 82.5% |
| Exact size + type (of bolts recognised) | 53.9% |
| Mean diameter error | 0.29 mm |
| Mean length error | 2.4 mm |

| Time per frame (ms) | mean | median | p95 | max |
|---|---|---|---|---|
| detect | 26.6 | 24.3 | 43.9 | 73.4 |
| rectify | 0.2 | 0.2 | 0.2 | 0.4 |
| network | 5.8 | 5.5 | 5.9 | 58.0 |
| total | 32.5 | 30.0 | 49.8 | 94.2 |

Frames under 100 ms: **100.0%**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 45 | 82.2% | 88.9% | 48.9% |
| socket head cap screw | 45 | 91.1% | 88.9% | 53.3% |
| carriage bolt | 44 | 88.6% | 95.5% | 54.5% |
| flat head (countersunk) | 45 | 84.4% | 86.7% | 62.2% |
| button head | 45 | 84.4% | 82.2% | 42.2% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M3 | 15 | 66.7% | 66.7% | 26.7% |
| M4 | 15 | 100.0% | 93.3% | 40.0% |
| M5 | 15 | 86.7% | 86.7% | 53.3% |
| M6 | 15 | 93.3% | 93.3% | 60.0% |
| M8 | 15 | 93.3% | 100.0% | 73.3% |
| M10 | 15 | 93.3% | 100.0% | 60.0% |
| M12 | 15 | 86.7% | 100.0% | 73.3% |
| #6-32 | 15 | 73.3% | 53.3% | 40.0% |
| #8-32 | 15 | 60.0% | 73.3% | 13.3% |
| #10-24 | 15 | 73.3% | 80.0% | 46.7% |
| 1/4-20 | 15 | 100.0% | 93.3% | 53.3% |
| 5/16-18 | 15 | 80.0% | 93.3% | 46.7% |
| 3/8-16 | 15 | 100.0% | 93.3% | 66.7% |
| 7/16-14 | 15 | 93.3% | 100.0% | 80.0% |
| 1/2-13 | 14 | 92.9% | 100.0% | 50.0% |

Sample mistakes (truth -> predicted):

- M3 x 8 hex bolt  ->  M3 x 8 carriage bolt
- M3 x 8 socket head cap screw  ->  M4 x 12 socket head cap screw
- M3 x 8 flat head (countersunk)  ->  M3 x 10 flat head (countersunk)
- M3 x 8 button head  ->  M4 x 8 button head
- M3 x 30 hex bolt  ->  #6-32 x 1-1/4" hex bolt
- M3 x 30 socket head cap screw  ->  M3 x 30 button head
- M3 x 30 carriage bolt  ->  M3 x 35 carriage bolt
- M3 x 30 button head  ->  M3 x 25 socket head cap screw
- M3 x 60 carriage bolt  ->  M3 x 55 carriage bolt
- M4 x 8 hex bolt  ->  M4 x 10 hex bolt
- M4 x 8 socket head cap screw  ->  M4 x 10 socket head cap screw
- M4 x 8 carriage bolt  ->  #8-32 x 3/8" carriage bolt

### boltnet.onnx on `data/test_catalog_heavy` (281 frames: 225 bolts, 56 not bolts)

| Metric | Result |
|---|---|
| **Overall correct answer** (exact size+type for bolts, 'not a bolt' for others) | **27.4%** |
| Checkerboard found | 96.1% |
| Bolts recognised as bolts | 94.0% |
| Non-bolts rejected as 'not a bolt' | 88.9% |
| Diameter right (ignoring metric/imperial) | 64.5% |
| Thread exactly right (incl. metric/imperial) | 43.8% |
| Length exactly right | 28.1% |
| Head type right | 67.5% |
| Metric/imperial right | 60.6% |
| Exact size + type (of bolts recognised) | 14.3% |
| Mean diameter error | 0.53 mm |
| Mean length error | 4.5 mm |

| Time per frame (ms) | mean | median | p95 | max |
|---|---|---|---|---|
| detect | 27.2 | 24.9 | 45.5 | 92.4 |
| rectify | 0.2 | 0.2 | 0.2 | 0.3 |
| network | 5.6 | 5.5 | 5.8 | 6.9 |
| total | 32.8 | 30.5 | 51.2 | 98.1 |

Frames under 100 ms: **100.0%**

| By head type | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| hex bolt | 40 | 72.5% | 60.0% | 15.0% |
| socket head cap screw | 43 | 65.1% | 72.1% | 11.6% |
| carriage bolt | 44 | 61.4% | 63.6% | 11.4% |
| flat head (countersunk) | 45 | 55.6% | 51.1% | 17.8% |
| button head | 44 | 50.0% | 70.5% | 11.4% |

| By size | n | diameter right | head type right | fully right |
|---|---|---|---|---|
| M3 | 14 | 42.9% | 35.7% | 7.1% |
| M4 | 14 | 57.1% | 35.7% | 14.3% |
| M5 | 15 | 53.3% | 60.0% | 6.7% |
| M6 | 14 | 78.6% | 71.4% | 7.1% |
| M8 | 12 | 91.7% | 75.0% | 8.3% |
| M10 | 15 | 66.7% | 93.3% | 6.7% |
| M12 | 15 | 26.7% | 86.7% | 20.0% |
| #6-32 | 15 | 46.7% | 46.7% | 6.7% |
| #8-32 | 15 | 33.3% | 40.0% | 6.7% |
| #10-24 | 15 | 60.0% | 33.3% | 6.7% |
| 1/4-20 | 13 | 69.2% | 69.2% | 15.4% |
| 5/16-18 | 14 | 78.6% | 85.7% | 21.4% |
| 3/8-16 | 15 | 73.3% | 60.0% | 6.7% |
| 7/16-14 | 15 | 73.3% | 80.0% | 26.7% |
| 1/2-13 | 15 | 66.7% | 80.0% | 40.0% |

Sample mistakes (truth -> predicted):

- M3 x 8 hex bolt  ->  M3 x 8 carriage bolt
- M3 x 8 socket head cap screw  ->  M3 x 10 socket head cap screw
- M3 x 8 button head  ->  M3 x 12 hex bolt
- M3 x 30 carriage bolt  ->  M3 x 30 button head
- M3 x 30 flat head (countersunk)  ->  M4 x 30 button head
- M3 x 30 button head  ->  M5 x 25 button head
- M3 x 60 hex bolt  ->  M4 x 65 socket head cap screw
- M3 x 60 socket head cap screw  ->  #6-32 x 2-1/4" hex bolt
- M3 x 60 carriage bolt  ->  M3 x 40 carriage bolt
- M3 x 60 flat head (countersunk)  ->  #6-32 x 2-1/2" flat head (countersunk)
- M4 x 8 socket head cap screw  ->  M4 x 10 socket head cap screw
- M4 x 40 hex bolt  ->  M4 x 45 button head
