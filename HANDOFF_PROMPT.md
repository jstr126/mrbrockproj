# Task: build v3 of a camera-based bolt sorter (precise measurement upgrade)

You are taking over an existing Python project. I will upload the repository
(or paste files when you ask for them). Read `README.md`,
`bolt_sizer/catalog.py`, `bolt_sizer/synth.py`, `bolt_sizer/model.py`,
`bolt_sizer/infer.py`, `bolt_sizer/board.py` and `train.py` before changing
anything. Ask me for any file you need instead of guessing its contents.

## What the system does

One medium-quality camera looks down at a bolt lying flat on a printed
checkerboard with 0.25" (6.35 mm) squares. The pipeline:

1. `board.py`: find the checkerboard (OpenCV `findChessboardCornersSBWithMeta`
   with `CALIB_CB_LARGER`), then warp the frame to a top-down 512x512 "canvas"
   at exactly 4 px/mm (128 mm square). Optional lens calibration
   (`calibrate.py`) and optical-flow corner tracking for live video.
2. `model.py`: MobileNetV3-Small CNN, four heads:
   - size regression: diameter and length in mm, scaled by /10 and /50
   - metric vs imperial
   - head type: hex, socket_cap, carriage, flat, button. **This order is
     baked into the trained weights; don't reorder it.**
   - bolt / not-a-bolt
   ImageNet normalisation happens inside the model, so the input is RGB 0-1.
3. `infer.py`: torch-free ONNX runtime for the Raspberry Pi. It snaps the
   regressed sizes to the nearest standard size and assigns a sorting bin:
   the size label, `REJECT: not a bolt`, or `REVIEW: check by hand` when a
   confidence falls below the thresholds in the catalog's `sorting_rules`.
4. `catalog.py`: the single source of truth for thread sizes, pitches,
   lengths, head types and dimensions, finishes, grades, sorting factors and
   bin rules. `standards.py` builds its tables from the catalog's
   `"active": True` entries.

Requirements: under 100 ms per frame (currently ~33-50 ms per still photo and
~15 ms per tracked video frame on a Mac). It has to run on a Raspberry Pi
with only numpy, OpenCV and onnxruntime. Use fp32 ONNX: post-training int8
quantisation collapses this model (about 10% agreement with fp32, whatever
calibration method), so don't use it unless you do quantisation-aware training.

## Data and tools that already exist

- `make_synthetic.py`: renders training canvases (`data/synth` 20k bolts,
  `data/synth_mix` 12k with non-bolts and heavy degradation, `data/synth_junk`
  10k with bolt-shaped junk). Synthetic bolts are shaded surfaces of
  revolution with threads, in five head types and five finishes. The
  simulated camera adds random tilt, Brown-Conrady lens distortion, chromatic
  aberration, vignetting, blur, noise, JPEG, glare and shadows. Each
  `labels.csv` has columns
  `file,label,is_bolt,system,diameter_mm,length_mm,head_type,finish,source`.
- `tools/make_cutouts.py`: 17 real bolt photos and 46 non-bolt photos from
  Wikimedia Commons, cut out with colour-seeded GrabCut. Each bolt's
  length/diameter ratio is measured from the photo (about 10% label noise).
- `tools/make_testset.py`: builds raw camera-frame test sets with sources
  `web`, `synth`, `catalog` (every active size x head type x 3 lengths) and
  `junk`.
- `benchmark.py`: accuracy plus per-stage timing, broken down by head type
  and by size.
- `tools/compare_models.py`: runs several models on identical frames and
  reports where each object ends up (size bin right or wrong, REVIEW, REJECT).
- `capture.py`: labels real photos from the user's own camera, including
  non-bolts and an object id per physical object. `train.py
  --split-by-object` holds out whole objects for validation.
- Models: `models/boltnet_v1.*` (synthetic only) and `models/boltnet.*` (v2,
  fine-tuned with bolt-shaped junk).

## Current results (v2)

On rendered bolts in normal conditions, 58% are fully right (exact thread,
length and head type). The first error, when there is one:

| Error | Share |
|---|---|
| Length off by one standard step | 15% |
| Metric/imperial mixed up | 11% |
| Diameter off by one size | 8% |
| Rejected as not a bolt | 4% |
| Head type wrong | 3% |

The length regression has about ±2.5 mm of spread, while adjacent standard
lengths are 5-6 mm apart. Small sizes (M3, #6, #8) are weakest.

Under heavy degradation, 23% are fully right. AI-generated fake bolts land in
a size bin 2% of the time (v1: 67%). On the real Wikimedia photos v2 is poor:
it recognises only 34-42% of real bolts as bolts (v1: 85%), and almost none
end up fully right. It treats unfamiliar-looking real bolts as junk.

## What to build: v3

1. **Outline (segmentation) output.** Add a light FPN/U-Net decoder to the
   MobileNetV3-Small backbone, using features at strides 2, 4, 8, 16 and 32.
   It outputs 3-class logits (background, head, shank) at 256x256, which is
   stride 2 on the 512 canvas. Initialise everything else from v2's weights
   (`load_state_dict(strict=False)`). Keep the existing four heads.
2. **Pixel-exact outline labels from the renderer.** In `render_bolt`, head
   pixels are those with axial coordinate below the head height. The
   carriage-bolt square neck counts as shank. Carry a 2-channel (head, shank)
   mask through every warp the image goes through:
   - sprite to board (`warpAffine`)
   - board to camera (`warpPerspective`)
   - the lens remap, with the green-channel maps (no chromatic aberration
     and no vignetting)
   - `rectify` with the fitted homography
   Store the masks as 256x256 class-index PNGs with a `mask` column in
   labels.csv. Non-bolts and junk get an all-background mask. Re-render the
   three training folders with masks.
3. **Geometric measurement in `infer.py`.** This must stay numpy/OpenCV
   only. From the soft head and shank probabilities:
   - find the bolt's principal axis by weighted PCA
   - diameter: width profile across the shank, using a high percentile so it
     reads the thread crests (the nominal size is the major diameter)
   - length: from where head meets shank to the tip, except flat heads,
     which are measured overall
   Find the endpoints with sub-pixel interpolation. Fit a linear calibration
   on validation canvases and store it in the ONNX `metadata_props`. Fuse
   the result with the regression head. If the two disagree by more than
   half a standard step, the bin is REVIEW.
4. **Thread pitch for metric vs imperial.** Sample intensity along lines
   parallel to the axis inside the threaded shank, in the **original camera
   frame** at native resolution. Map canvas coordinates to the frame with
   the rectification matrix; refactor `rectify` to return it. Take the
   dominant period with an FFT. For the measured diameter, compare it with
   the metric coarse pitch and the UNC pitch, and override the network's
   system output only when the peak is strong. Note: M8 vs 5/16" differ by
   only 0.06 mm in diameter (see the catalog's `look_alikes`), so pitch is the
   only way to separate them.
5. **Real photos in training.** Split the Wikimedia cutouts by photo, about
   half for training and half held out. Build head/shank masks for the
   training cutouts by extending `measure_bolt` in `tools/make_cutouts.py`.
   Composite them through the same camera simulator into a `data/train_web`
   training folder. Rebuild the real-photo test sets from **held-out photos
   only** (`data/test_webhold_*`), and re-evaluate v2 on those too, so the
   comparison is fair.
6. **Train v3** to convergence on all folders. `train.py --select mean`
   picks the checkpoint with the best average validation score. Add
   mask-IoU to validation. Use CE plus dice loss on the mask, with class
   weights, because background dominates.
7. **Export and benchmark.** Re-export v3 to ONNX with the `mask` output,
   checking ONNX against torch. Then run `tools/compare_models.py` and
   `benchmark.py` for v2 vs v3 on every test set: catalog normal/heavy,
   junk, AI fakes, and the held-out real photos.

## Pitfalls already found (don't reintroduce them)

- OpenCV's `CALIB_CB_LARGER` corner ordering can't be trusted, and it
  sometimes returns only every other corner along one axis. `board.py`
  rebuilds the grid by walking neighbouring corners (`_lattice`), then picks
  the stride with a black/white parity check (`_fit_stride`). Keep that.
- Clip corners inside the image before `cornerSubPix`.
- With strong uncalibrated barrel distortion, a homography fitted to a
  corner patch far from the image centre extrapolates badly. Lens
  calibration is the real fix.
- This Mac slows down 10-20x when macOS runs updates. Check `uptime` before
  trusting any timing, and save a checkpoint every epoch.
- Real-photo test labels carry about 10% length noise, so treat
  exact-length scores there as a lower bound.

## How I want you to work

- Make changes in small, testable steps. After each step, show evidence it
  works: a rendered mask overlay, a unit check, or a short training run.
- Keep the code style: short docstrings, no dead code, and everything
  Pi-side free of torch.
- Report real measured numbers, including regressions. Don't call it done
  or perfect without benchmark evidence. Some cases (look-alike sizes on
  blurry images) are physically limited; say so rather than hiding it.
- Done means: v3 beats v2 on fully-right rate and right-size-bin rate on the
  rendered catalog sets, doesn't regress junk rejection, and recognises
  clearly more held-out real bolts as bolts than v2. Still under 100 ms per
  frame, and the README results tables are updated.
