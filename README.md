# Bolt sizer

Point one camera at a bolt lying on a 0.25" checkerboard and get:

- **diameter / thread**, e.g. `M6` or `1/4-20`
- **length**, e.g. `30 mm` or `1-1/2"`
- **head type**: hex bolt, socket head cap screw, carriage bolt, flat head (countersunk), or button head
- **metric vs imperial**, with the other system's nearest size shown when the network is unsure
- **"not a bolt"** for anything else on the board: nuts, washers, coins, pins, batteries, wood screws, an empty board

Example output: `M6 x 30 hex bolt | d 6.04mm L 29.7mm | metric 94% type 98%`

## How it works

```
camera frame ──► undistort lens ──► find checkerboard ──► warp to top-down canvas ──► CNN ──► snap to standard size
                 (optional,          (any clean 5x5       (512x512 px, exactly         bolt or not, diameter,
                  calibrate.py)       patch of corners;     4 px per mm)                length (mm), metric/
                                      tracked in video)                                 imperial, head type
```

A single camera can't tell size from distance by itself, so the checkerboard
gives the scale. Every frame gets warped into a top-down image where
**1 mm = 4 pixels**, however far away or tilted the camera is. The network
then measures real millimetres. Its continuous outputs are then snapped to the
nearest standard size in `bolt_sizer/standards.py`.

The model is MobileNetV3-Small with four output heads. The v3 architecture
adds a light outline decoder (background, head, shank). Both versions run
through fp32 ONNX with numpy, OpenCV and onnxruntime on the Raspberry Pi.

## The bolt catalog

`bolt_sizer/catalog.py` is the dictionary the sorter is built on. It holds
every thread size (coarse and fine pitch), standard lengths, head types with
their dimensions and length conventions, finishes, strength grades, drive
types, metric/imperial look-alike pairs, and the list of **sorting factors**.
Each factor notes whether one camera can see it and whether the model uses
it yet. It also holds the **sorting rules**: one bin per
system/thread/length/head type, a REJECT bin for non-bolts, and a REVIEW bin
for low-confidence answers. `predict.py` prints the bin for every bolt.

```bash
.venv/bin/python -m bolt_sizer.catalog          # readable summary
.venv/bin/python -m bolt_sizer.catalog --json   # everything, as JSON
```

Entries marked `"active": True` are what the sorter handles today, and
exactly what the current model was trained on. To add a size, length or head
type, set it active, re-run `make_synthetic.py`, and retrain. Add new head
types at the end of the list, because the model's outputs follow their order.

## Supported sizes

| | Diameters | Lengths |
|---|---|---|
| Metric | M3, M4, M5, M6, M8, M10, M12 | 8 – 100 mm |
| Imperial | #6-32, #8-32, #10-24, 1/4-20, 5/16-18, 3/8-16, 7/16-14, 1/2-13 | 1/4" – 4" |

To change these, edit the active entries in `bolt_sizer/catalog.py`.
`standards.py` builds the active thread, length and head tables from it. Length is measured under the head, except flat heads, where
it includes the head.

## Setup (training computer)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 1. Print the board

```bash
.venv/bin/python make_board.py
```

Print `board.pdf` at **100% / actual size** and check with a ruler that 4
squares = 1 inch. Tape it flat; any wrinkle is a measuring error.

## 2. Train on synthetic data

```bash
.venv/bin/python make_synthetic.py --n 20000 --out data/synth
.venv/bin/python make_synthetic.py --n 12000 --out data/synth_mix --neg-frac 0.5 --heavy-frac 0.5 --seed 1
.venv/bin/python train.py --data data/synth_mix data/synth --epochs 10 --pretrained
```

`data/synth_mix` adds non-bolt scenes and heavily degraded frames, so the
"not a bolt" output has something to learn from.

The synthetic generator renders shaded bolts of every size, type and finish
(zinc, black oxide, yellow zinc, stainless). It then simulates a cheap camera:
random tilt and distance, barrel/pincushion lens distortion, chromatic
aberration, vignetting, defocus and hand-shake blur, low-res sensor upscaling,
shot/read/chroma noise, hot pixels, ISP over-sharpening, white-balance and
exposure errors, and JPEG compression.

## 3. Calibrate the lens (recommended for Pi cameras)

```bash
python calibrate.py --picamera        # or --camera 0 for a USB webcam
```

Show the board without a bolt from about 15 angles (SPACE grabs each one),
then press C. This writes `camera_calib.npz`. Pass `--calib camera_calib.npz`
to `capture.py` and `predict.py`.

## 4. Fine-tune on your own photos (important)

The synthetic-only model reads real bolts poorly (see **Current results**).
Photos from **your** camera, on **your** board, are the fix.

**What to shoot**

- Every bolt size and head type you want sorted: at least 2-3 physical
  bolts per head type, more for the look-alike sizes (M6/1/4", M8/5/16").
- About 20 shots per object. Between shots, roll and rotate the bolt, slide
  it around the middle of the view, and change the camera height and tilt a
  little. Do some shots under different light (lamp moved, room lights off).
- Non-bolts too: nuts, washers, wood screws, whatever ends up in the bin.
  Label them `none`. Aim for about a quarter of all shots.

```bash
# one bolt (finish is optional, for sorting by finish later)
.venv/bin/python capture.py --label "M6x30" --type hex --finish zinc --calib camera_calib.npz
# a non-bolt
.venv/bin/python capture.py --label none --calib camera_calib.npz
#   SPACE = save a shot, N = next object (type its label in the terminal), Q = quit
```

Label formats: `M6x30`, `M8x1.25x40`, `1/4-20x1-1/2`, `#10-24x3/4`, `5/16x2`, `none`.
Head types: `hex`, `socket_cap`, `carriage`, `flat`, `button`.
Finishes: `zinc`, `yellow_zinc`, `black_oxide`, `stainless`, `galvanized`, `plain`, `brass`, `nylon`.

Only save when the screen says **board OK**. Check the "rectified" window:
the squares should look square, and the bolt should not be cut off.

**Fine-tune**

```bash
.venv/bin/python train.py --data data/real data/synth_mix data/synth --init models/boltnet.pt \
                          --epochs 6 --lr 1e-4 --out models/boltnet_real.pt
.venv/bin/python export_onnx.py --ckpt models/boltnet_real.pt
.venv/bin/python predict.py --model models/boltnet_real.onnx --camera 0
```

`data/real` goes first: the saved checkpoint is the one that scores best on
your photos. Its validation set holds out **whole objects**. Every shot of a
validation bolt stays out of training, so the score shows how the model does
on bolts it has never seen. Keep the synthetic folders in the mix; dropping
them lets the model forget sizes you didn't photograph.

## 5. Export for the Raspberry Pi

```bash
.venv/bin/python export_onnx.py --ckpt models/boltnet.pt
# -> models/boltnet.onnx
```

Use fp32. The exporter verifies every output against PyTorch for batches of
1 and 2. Post-training int8 quantization is deliberately unavailable: it
breaks this network (about 10% agreement with fp32). Revisit it only with
quantization-aware training.

## Testing on real bolt photos

`tools/` builds a harder test set from real photographs. It downloads
freely licensed bolt and non-bolt photos from Wikimedia Commons, cuts the
objects out, scales each bolt to an exact standard size (picked from its
length-to-diameter ratio), and composites it onto the board under heavy blur,
lens distortion, noise, dim light, glare and shadows:

```bash
.venv/bin/python tools/make_cutouts.py              # needs data/web/candidates.json + raw/
.venv/bin/python tools/make_testset.py --out data/test_web_heavy
.venv/bin/python benchmark.py --model models/boltnet.onnx --data data/test_web_heavy data/test_web_normal data/test_synth_heavy
```

`benchmark.py` reports the accuracy for each output plus per-stage timing,
and writes `results/benchmark.md`. The latest results are in
`results/benchmark_fp32.md`; see **Current results** below.

## 6. Run on the Raspberry Pi

Use a Pi 4 or 5 running 64-bit Raspberry Pi OS. Copy over `bolt_sizer/`,
`predict.py`, `capture.py`, `calibrate.py`, `requirements-pi.txt`, and the
`.onnx` file.

```bash
sudo apt install -y python3-picamera2
python3 -m venv --system-site-packages .venv      # system site packages so picamera2 is visible
.venv/bin/pip install -r requirements-pi.txt

.venv/bin/python predict.py --picamera --calib camera_calib.npz
.venv/bin/python predict.py --picamera --headless          # no display
```

Live mode runs the full checkerboard detection only once every 30 frames,
or when tracking is lost. In between it follows the corners with optical flow,
which is what keeps a frame within budget on slow hardware.

USB webcams work too: use `--camera 0` instead of `--picamera`. On a Pi
without a desktop, use `opencv-python-headless` and `--headless`. Photos and
live video default to one view per prediction, matching the v3 calibration
and benchmark. `--tta 4` averages rotated copies for a steadier answer, but
runs the network four times and requires a separate latency measurement.

## Current results

These are for v1 (synthetic data only, 8 epochs, fp32), measured on a Mac;
see the v1 vs v2 table below for the current model.
"Real photos" are 17 Wikimedia bolt photos and 46 non-bolt photos,
composited onto the board. Bolt sizes in that set come from measuring each
photo, which can be about 10% off, so exact-length scores there are a lower bound.

| | Real photos, heavy degradation | Real photos, normal | Synthetic, heavy |
|---|---|---|---|
| Checkerboard found | 95.7% | 98.7% | 96.0% |
| Bolt recognised as bolt | 79.6% | 84.5% | 91.0% |
| Non-bolt rejected | 62.1% | 71.7% | 87.4% |
| Diameter right (either system) | 50.0% | 69.2% | 62.7% |
| Mean diameter error | 0.76 mm | 0.65 mm | 0.61 mm |
| Length exactly right | 9.0% | 4.1% | 39.5% |
| Mean length error | 6.0 mm | 7.1 mm | 4.1 mm |
| Head type right | 19.2% | 29.0% | 66.5% |
| Metric/imperial right | 42.9% | 63.9% | 59.3% |
| **Time per photo, mean / p95** | 43 / 75 ms | 50 / 83 ms | 47 / 79 ms |
| Photos under 100 ms | 98.3% | 97.8% | 98.2% |

Live video with the board tracker: **14.8 ms per frame on average, 100% of
frames under 100 ms** (about 14 ms per tracked frame, 46 ms when it re-detects
the board).

**Catalog coverage test** (`tools/make_testset.py --source catalog`): every
active size x head type at 3 lengths (225 bins) plus 56 non-bolts, rendered.
Per-type and per-size tables are in `results/benchmark_catalog.md`, and a
labelled sample is in `results/gallery_catalog.jpg`.

| | Rendered, normal | Rendered, heavy | Real photos, normal | Real photos, heavy |
|---|---|---|---|---|
| Head type right | 91% | 68% | 29% | 19% |
| Diameter right | 89% | 65% | 69% | 50% |
| Sent to a size bin | 62% | 22% | 33% | 19% |
| **...of those, the right bin** | **59%** | 24% | 1% | 0% |
| Sent to REVIEW | 16% | 57% | 27% | 46% |
| Bolts wrongly rejected | 3% | 4% | 11% | 13% |
| Time per photo (mean) | 33 ms | 33 ms | 50 ms | 43 ms |

Small sizes (M3, #6, #8) are the weakest. On real photos the model is often
*confidently* wrong, so the REVIEW bin doesn't catch those mistakes.

**Bolt-shaped junk, v1 vs v2.** v1 rejected obvious non-bolts (nuts,
washers, coins: 98%) but put most bolt-shaped junk in size bins. v2
(`models/boltnet.onnx`) was fine-tuned from v1 with `data/synth_junk`:
double-headed pieces, headless threaded rod, snapped bolts, and bolts with a
nut still on. Full table: `results/v1_vs_v2.md` (`tools/compare_models.py`).

| | v1 | v2 |
|---|---|---|
| AI fake bolts put in a size bin (normal / heavy) | 67% / 22% | **2% / 0%** |
| Rendered junk put in a size bin (normal / heavy) | 50% / 16% | **10% / 4%** |
| Rendered bolts fully right (normal / heavy) | 52% / 13% | **58% / 23%** |
| Rendered bolts: right size bin, of those sent | 59% / 24% | **66% / 39%** |
| **Real-photo bolts recognised as bolts** (normal / heavy) | **85% / 76%** | 34% / 42% |

v2 is much safer against junk and better on rendered bolts, but it rejects
most of the Wikimedia bolt photos as junk, because they look unfamiliar to
it. v1 also got almost none of those photos fully right, so neither model is
usable on real bolts yet. Training on `capture.py` photos is what fixes
this. v1 is kept as `models/boltnet_v1.onnx` (use `--model` to switch).

The network sizes real bolts reasonably well, but reads lengths about 17%
short and mostly gets head types wrong on real photos. Training on
`capture.py` photos from your own camera is the fix (step 4). The Pi has not
been benchmarked yet; expect it to be several times slower than a Mac.

## Building v3

`models/boltnet.onnx` remains the v2 baseline. Use `--model models/boltnet_v3.onnx`
when the separately named v3 model has passed the comparison below.

The optional decoder combines MobileNet features at strides 2/4/8/16/32 and
returns 3-class logits at 256x256. The first four heads retain their v2
parameter names and class order. Training uses class-weighted cross entropy
plus foreground dice loss, and reports foreground mean IoU.

Re-render training data with masks, then create a deterministic split of the
Wikimedia photos. `split.json` groups every cutout from the same source photo;
no held-out photo enters `data/train_web`. Single-photo head classes stay in
the held-out set. Web masks are approximate measurements from GrabCut cutouts;
synthetic masks come directly from the bolt's axial coordinates. Carriage
necks belong to the shank.

```bash
.venv/bin/python make_synthetic.py --n 20000 --out data/synth --workers 4
.venv/bin/python make_synthetic.py --n 12000 --out data/synth_mix --neg-frac .5 --heavy-frac .5 --seed 1 --workers 4
.venv/bin/python make_synthetic.py --n 10000 --out data/synth_junk --neg-frac .5 --junk-frac .6 --heavy-frac .4 --seed 2 --workers 4
.venv/bin/python tools/prepare_web.py --n 4000 --workers 2
.venv/bin/python tools/make_testset.py --split heldout --out data/test_webhold_normal --normal --workers 2
.venv/bin/python tools/make_testset.py --split heldout --out data/test_webhold_heavy --workers 2
.venv/bin/python train.py --v3 --init models/boltnet.pt --data data/synth data/synth_mix data/synth_junk data/train_web --split-by-object data/train_web --select mean --out models/boltnet_v3.pt
.venv/bin/python export_onnx.py --ckpt models/boltnet_v3.pt
.venv/bin/python -m unittest discover -s tests -v
```

For a decoder warm-up, add `--decoder-only` before joint training. Each epoch
writes an atomic `.last.pt` checkpoint. V3 selects using the calibrated, fused
size answer on validation canvases, averaged by folder with `--select mean`;
it also reports the original regression-only score. The history is saved as
`.history.json`. The decoder uses 3x the backbone learning rate by default;
v3 gives the two scaled size errors equal weight so length is not starved
by the classification losses. `--teacher models/boltnet.pt` adds frozen v2
size/system/type targets to reduce forgetting during joint training; the bolt
classifier and outline still learn their ground-truth labels. The teacher
is used only during training and adds no Pi dependencies or inference work.
V3 checkpoints record the image and photo/object identities used for training.
Later stages reject any validation identity previously used for training, and
export verifies the fixed validation partition before fitting calibration.
Unverified preliminary v3 checkpoints cannot initialize a production run.

The runtime measures the principal axis with weighted PCA, uses sub-pixel
crossings of the soft shank outline for width/length, and measures flat-head
length overall. Export fits a robust linear correction on **validation
canvases only** and stores it in ONNX metadata, with sample count and a hash
of the validation filenames. One blend weight per dimension is fitted from those same validation errors;
the weights and regression/fused errors are also stored in metadata. Disagreement beyond half a local standard step,
or an unusable outline, sends a predicted bolt to REVIEW. Uncalibrated v3
exports also send predicted bolts to REVIEW.

`rectify(..., return_matrix=True)` returns the canvas and its canvas-to-frame
matrix. `frame_to_canvas(..., return_matrix=True)` returns `(canvas, frame_used,
matrix)`, at the camera's native resolution (undistorted when calibration is
provided). Pitch uses FFTs of lines sampled in that frame. It can override the
system head only with a strong, resolved peak that clearly favors one coarse
metric/UNC candidate. Blurry or undersampled threads retain the network answer.
Live predictions use the current frame by default. `--smooth N` can average
the four original heads while keeping the current mask, but only use it for a
stationary bolt: averaging successive bolts can carry the previous bolt's
answer into the next one.

The comparison reports correct-bin coverage **and** precision. Board failures
remain in the all-bolt denominator and route to REVIEW; non-bolt rejection
counts actual REJECT routing. This definition is stricter than older tables
that counted every missing board as a rejected non-bolt. Exact real-photo
length scores still have roughly 10% label noise. Pi latency must be measured
on the target hardware; Mac timing cannot establish a Pi budget.

```bash
.venv/bin/python tools/compare_models.py --model models/boltnet.onnx models/boltnet_v3.onnx --data data/test_catalog_normal data/test_catalog_heavy data/test_junk_normal data/test_junk_heavy data/test_ai_normal data/test_ai_heavy data/test_webhold_normal data/test_webhold_heavy --out results/v2_vs_v3.md
.venv/bin/python benchmark.py --model models/boltnet.onnx models/boltnet_v3.onnx --data data/test_catalog_normal data/test_catalog_heavy data/test_junk_normal data/test_junk_heavy data/test_ai_normal data/test_ai_heavy data/test_webhold_normal data/test_webhold_heavy --threads 2 --out results/benchmark_v3.md
```

V3 was trained with a fixed split: 8 frozen-decoder epochs, followed by 24
joint-training epochs with early stopping. Epoch 16 was selected by mean
validation score. ONNX matches all five PyTorch outputs within 0.00004.
All 46,000 training masks passed the dataset audit. Preliminary snapshot
checkpoints with overlapping validation exposure were discarded.

**Acceptance is not met.** The requested 99% automatic-bin precision is not
demonstrated. V3 remains experimental and the default model is still v2.

| Test set | Model | Fully right / bolts | Correct automatic bins / bolts | Automatic-bin precision | Bolts recognised | Mean / p95 ms |
|---|---|---|---|---|---|---|
| test_catalog_normal | v2 | 131/225 (58.2%) | 117/225 (52.0%) | 117/177 (66.1%) | 215/225 (95.6%) | 34.4 / 54.2 |
| test_catalog_normal | v3 | 144/225 (64.0%) | 90/225 (40.0%) | 90/108 (83.3%) | 215/225 (95.6%) | 39.9 / 57.7 |
| test_catalog_heavy | v2 | 51/225 (22.7%) | 26/225 (11.6%) | 26/66 (39.4%) | 202/225 (89.8%) | 33.8 / 54.0 |
| test_catalog_heavy | v3 | 52/225 (23.1%) | 17/225 (7.6%) | 17/29 (58.6%) | 196/225 (87.1%) | 39.1 / 55.6 |
| test_junk_normal | v2 | — | — | 0/19 (0.0%) | — | 36.6 / 63.7 |
| test_junk_normal | v3 | — | — | 0/4 (0.0%) | — | 38.1 / 55.6 |
| test_junk_heavy | v2 | — | — | 0/8 (0.0%) | — | 34.2 / 58.3 |
| test_junk_heavy | v3 | — | — | 0/4 (0.0%) | — | 38.4 / 64.4 |
| test_ai_normal | v2 | — | — | 0/1 (0.0%) | — | 33.7 / 50.8 |
| test_ai_normal | v3 | — | — | — | — | 38.4 / 55.9 |
| test_ai_heavy | v2 | — | — | — | — | 33.5 / 51.9 |
| test_ai_heavy | v3 | — | — | — | — | 37.7 / 72.9 |
| test_webhold_normal | v2 | 0/120 (0.0%) | 0/120 (0.0%) | 0/27 (0.0%) | 37/120 (30.8%) | 33.9 / 55.1 |
| test_webhold_normal | v3 | 1/120 (0.8%) | 0/120 (0.0%) | 0/6 (0.0%) | 92/120 (76.7%) | 38.9 / 59.4 |
| test_webhold_heavy | v2 | 0/120 (0.0%) | 0/120 (0.0%) | 0/10 (0.0%) | 49/120 (40.8%) | 33.3 / 49.2 |
| test_webhold_heavy | v3 | 1/120 (0.8%) | 0/120 (0.0%) | 0/2 (0.0%) | 93/120 (77.5%) | 37.4 / 53.5 |

V3 latency is measured on this Mac with two CPU threads and one view. 5/1642 frames
reached or exceeded 100 ms; the maximum was 164.0 ms. Mean and p95 timings
were below 100 ms on every set. Raspberry Pi latency remains unmeasured.

The normal/heavy catalog correct-bin coverage regressed because v3 diverted
more cases to REVIEW. Held-out real-bolt recognition improved from 31%/41%
to 77%/78%, but none of the remaining automatic real-photo assignments was
correct. Junk sent to size bins fell from 10%/4% to 2%/2%. AI fake size-bin
assignments fell to zero; more AI fakes moved to REVIEW, reducing actual
REJECT routing. These are material limitations, not a 99% routing policy.

Detailed counts, rejection rates and acceptance checks are in
`results/v3_acceptance.md`; per-stage timing and size/head breakdowns are in
`results/benchmark_v3.md`. `results/v3_failure_audit.md` shows high-confidence
errors and fixed confidence cutoffs. Increasing a confidence threshold alone
does not establish the requested accuracy.

### Connecting the vibrating feeder

The benchmark measures vision processing after frame capture; it does not
include camera buffering, exposure, bolt settling, actuator travel or bin
movement. It reports p95/p99, maximum latency and frames exceeding 100 ms
alongside the mean. Set the feed interval from the measured end-to-end cycle
on the assembled machine, with time for the actuator to complete its motion.

Present one separated bolt per inspection. Touching or overlapping bolts need
another pass through the feeder. A REVIEW result needs a physical bypass or
holding bin so uncertainty does not accumulate at the camera. Missing or stale
decisions must never reuse the previous bolt's bin. `predict.py` is a live
display; its headless text is throttled to one update per second and is not an
actuator protocol. Machine integration still needs a per-bolt trigger, a
decision deadline, an actuator acknowledgement and a bounded queue that pauses
the feeder when it is full. Test those against actual feed rate and mechanics.

The requested machine target is **99% correct automatic bin assignments**,
with a bypass/REVIEW bin allowed. Report that precision together with the share
of all incoming bolts correctly sent to a size bin and the share diverted to
REVIEW. A 99% network confidence does not establish 99% sorting accuracy. The
acceptance report checks the 99% precision target separately for normal/heavy
catalog and held-out-photo conditions. Passing composite-image tests would
still require validation on labeled bolts from the actual camera, lighting
and feed speed. Wikimedia size labels have roughly 10% measurement noise and
cannot certify a 1% physical sorting error rate. Even 99% permits about one
wrong decision per 100 assignments. The mechanism needs a bypass, obstruction
detection and a feeder stop independent of the model. This project currently
emits inspection results and has no actuator or jam-sensor integration.

## Self-hosting the site on a Raspberry Pi

`pi_web/` serves the inspection page, USB camera preview and v3 inference from
the Pi. Other computers on the same Ethernet/LAN open the Pi network URL;
viewers need no ChatGPT account, installation, SSH tunnel, model download or
camera permission. See `pi_web/README.md`.

```bash
python3 tools/deploy_pi.py USER@PI_HOST
# Open http://PI_LAN_IP:8080 from other computers on the same LAN
```

The server reports candidate bins for inspection and locks actual routing to
REVIEW while the 99% target is unverified. The deployer requires a reachable
SSH account with working authentication for deployment only. The page listens
on the Pi LAN; router forwarding and public internet exposure are not configured.
The current camera mode expects the USB camera on the Pi.

## Tips for accuracy

- Lay the bolt **flat** and **near the middle of the view**, with clean checkerboard visible around it.
- Get close enough that the bolt fills a good part of the frame, but the board must still show at least a 6x6-square patch.
- Even, diffuse light. Avoid hard glare on shiny bolts.
- **Look-alike sizes:** M8 vs 5/16" (0.06 mm apart) and M6 vs 1/4" (0.35 mm) can't be told apart by diameter. The metric/imperial head has to judge from the thread pitch and head shape. When it's unsure, it shows the alternative. If you mostly use one system, train on that system only.
- Thread pitch is only a few pixels per thread at 4 px/mm, so a sharper camera, or getting closer, helps more than anything else.

## Files

| File | Purpose |
|---|---|
| `bolt_sizer/catalog.py` | The bolt catalog: all types, sizes, factors and sorting rules |
| `bolt_sizer/standards.py` | Size tables built from the catalog, label parsing, snapping to nearest size |
| `bolt_sizer/board.py` | Checkerboard detection, lens undistortion, top-down rectification |
| `bolt_sizer/synth.py` | Synthetic bolt renderer + lens / camera-noise simulation |
| `bolt_sizer/model.py` | BoltNet (PyTorch, training only) |
| `bolt_sizer/infer.py` | ONNX runtime + decoding (Pi-side, no torch) |
| `bolt_sizer/measure.py` | Sub-pixel outline dimensions and native-frame pitch FFT (Pi-side, no torch) |
| `tools/prepare_web.py` | Source-photo split, approximate photo masks, web training canvases |
| `tools/calibrate_measurement.py` | Validation-only geometric calibration and fusion stored in ONNX metadata |
| `tools/summarize_v3.py` | Acceptance report with counts, coverage, precision and timing |
| `tools/make_cutouts.py`, `tools/make_testset.py`, `benchmark.py` | Real-photo test set and accuracy/speed benchmark |
| `make_board.py`, `make_synthetic.py`, `calibrate.py`, `capture.py`, `train.py`, `export_onnx.py`, `predict.py` | Scripts for each step above |

### V3 refinement experiment

`models/boltnet_v3_refined.onnx` is an optional metadata refinement of the same
five-output fp32 network. `tools/refine_measurement.py` fits correction to both
regression and outline sizes using the fixed synthetic validation subset, then
combines network thread-system evidence with distance to metric/imperial
standards. A conflict always goes to REVIEW. Strong native-frame pitch evidence
retains priority. Original v2 and v3 model files are preserved.

OpenCV random state could change board rectification for identical images. Board
acquisition now resets the OpenCV seed; an integration test checks repeatability.
Both models were rerun on all eight legacy sets and 800 fresh synthetic frames
using this common acquisition fix. See `results/v3_refinement.md` for exact
counts, precision, coverage, latency tails and the fresh renderer seeds.

This candidate remains experimental: the 99% routing target is not met, and a
validation-fitted bypass rule failed its reserved-subset check. The Pi server
continues to lock every decision to REVIEW. Select the candidate for diagnostic
viewing with `--model models/boltnet_v3_refined.onnx`; the original v3 file is
still the Pi server default. No Site deployment changed in this iteration.
