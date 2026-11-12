"""Train BoltNet.

    # synthetic only (to get started)
    python train.py --data data/synth_mix data/synth --epochs 10 --pretrained   # MobileNetV3 by default

    # fine-tune on your own photos, keeping synthetic in the mix
    # (data/real first: its validation score picks the saved model)
    python train.py --data data/real data/synth_mix data/synth --init models/boltnet.pt \
                    --epochs 6 --lr 1e-4 --out models/boltnet_real.pt
"""
import argparse
import cv2
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import ConcatDataset, DataLoader, Subset, WeightedRandomSampler

from bolt_sizer.data import FolderDataset
from bolt_sizer.model import ARCHS, BoltNet, DIAM_SCALE, LEN_SCALE, save, load
from bolt_sizer.standards import HEAD_TYPES, snap
from bolt_sizer.measure import outline_size
from tools.calibrate_measurement import fit_linear, fit_fusion


def pick_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def split(folder, val_frac, seed, by_object=False, seen=frozenset()):
    """Train/val split. by_object holds out whole objects (all shots of one
    bolt), so validation measures bolts the model has never seen; objects in
    seen (trained on by the initializer) never go to validation."""
    full = FolderDataset(folder, train=True)
    rng = np.random.default_rng(seed)
    if by_object:
        groups = {}
        for i, row in enumerate(full.rows):
            groups.setdefault(row.get("source") or row["label"], []).append(i)
        val = []
        for key in rng.permutation(sorted(groups)):
            if key in seen:
                continue
            if len(val) >= val_frac * len(full):
                break
            val += groups[key]
        train = sorted(set(range(len(full))) - set(val))
    else:
        idx = rng.permutation(len(full)).tolist()
        n_val = max(1, int(len(full) * val_frac))
        val, train = idx[:n_val], idx[n_val:]
    return Subset(full, train), Subset(FolderDataset(folder, train=False), val)


def initializer_sources(init):
    """Photo/object sources a checkpoint trained on; they stay out of validation."""
    if not init:
        return frozenset()
    keys = torch.load(init, map_location="cpu", weights_only=False).get("training_keys", [])
    return frozenset(k[len("source:"):] for k in keys if k.startswith("source:"))


def exposure_keys(subsets):
    """Track images and whole photo/object sources across training stages."""
    keys = set()
    for subset in subsets:
        family = subset.dataset.folder.name
        for i in subset.indices:
            row = subset.dataset.rows[i]
            keys.add(f"image:{family}/{Path(row['file']).name}")
            if row.get('source'):
                keys.add('source:' + row['source'])
    return keys


def verify_partition(trains, vals, checkpoint=None):
    train_keys, val_keys = exposure_keys(trains), exposure_keys(vals)
    if train_keys & val_keys:
        raise ValueError('Train/validation share images or photo sources; use --split-by-object for photo folders')
    previous = set((checkpoint or {}).get('training_keys', []))
    if checkpoint and checkpoint.get('segmentation') and not previous:
        raise ValueError('V3 initializer has no training provenance; start from v2 or a verified v3 checkpoint')
    overlap = previous & val_keys
    if overlap:
        raise ValueError(f'Initializer trained on {len(overlap)} current validation identities; keep its original split')
    digest = hashlib.sha256('\n'.join(sorted(val_keys)).encode()).hexdigest()
    return sorted(train_keys | previous), digest


def mask_loss(logits, target):
    valid = target != 255
    if not valid.any():
        return logits.sum() * 0
    ce = F.cross_entropy(logits, target, weight=logits.new_tensor([0.15, 2.0, 1.0]),
                         ignore_index=255)
    truth = F.one_hot(target.clamp_max(2), 3).permute(0, 3, 1, 2) * valid[:, None]
    prob = logits.softmax(1) * valid[:, None]
    dims = (0, 2, 3)
    dice = (2 * (prob * truth).sum(dims) + 1) / (prob.sum(dims) + truth.sum(dims) + 1)
    return ce + 1 - dice[1:].mean()


def loss_fn(out, size_t, sys_t, type_t, bolt_t, mask_t=None, teacher_out=None):
    size_p, sys_p, type_p, bolt_p = out[:4]
    loss = F.cross_entropy(bolt_p, bolt_t)
    pos = bolt_t == 1                     # size/system/type only for real bolts
    if pos.any():
        reg = F.smooth_l1_loss(size_p[pos], size_t[pos], reduction="none", beta=0.05)
        size_weights = [4.0, 4.0 if len(out) == 5 else 1.0]
        reg = (reg * torch.tensor(size_weights, device=reg.device)).mean()
        loss = loss + reg + F.cross_entropy(sys_p[pos], sys_t[pos]) + F.cross_entropy(type_p[pos], type_t[pos])
    if teacher_out is not None and pos.any():
        preservation = F.smooth_l1_loss(size_p[pos], teacher_out[0][pos], beta=.05, reduction='none')
        loss = loss + 2 * (preservation * size_p.new_tensor([4., 4.])).mean()
        for pred, teacher in zip((sys_p, type_p), teacher_out[1:3]):
            loss = loss + .25 * F.kl_div(pred[pos].log_softmax(1), teacher[pos].softmax(1), reduction='batchmean')
    if len(out) == 5 and mask_t is not None:
        loss = loss + mask_loss(out[4], mask_t)
    return loss


@torch.no_grad()
def evaluate(model, loader, device, collect_geometry=False):
    model.eval()
    d_err, l_err, sys_ok, type_ok, exact, bolt_ok = [], [], [], [], [], []
    intersection, union = np.zeros(3), np.zeros(3)
    records = []
    for x, size_t, sys_t, type_t, bolt_t, mask_t in loader:
        out = [o.cpu() for o in model(x.to(device))]
        size_p, sys_p, type_p, bolt_p = out[:4]
        if len(out) == 5:
            pred, valid = out[4].argmax(1), mask_t != 255
            for k in range(3):
                intersection[k] += ((pred == k) & (mask_t == k) & valid).sum().item()
                union[k] += (((pred == k) | (mask_t == k)) & valid).sum().item()
        if collect_geometry:
            probs = out[4].softmax(1).numpy()
            for j in range(len(x)):
                geometry = outline_size(probs[j], HEAD_TYPES[int(type_p[j].argmax())])
                records.append({"bolt": int(bolt_t[j]), "pred_bolt": int(bolt_p[j].argmax()),
                                "size": size_p[j].numpy() * [DIAM_SCALE, LEN_SCALE],
                                "truth": size_t[j].numpy() * [DIAM_SCALE, LEN_SCALE],
                                "system": int(sys_p[j].argmax()), "type": int(type_p[j].argmax()),
                                "true_system": int(sys_t[j]), "true_type": int(type_t[j]),
                                "geometry": geometry})
        b_hat = bolt_p.argmax(1)
        bolt_ok += (b_hat == bolt_t).tolist()
        neg = bolt_t == 0
        exact += (b_hat[neg] == 0).tolist()
        pos = bolt_t == 1
        if not pos.any():
            continue
        size_p, sys_p, type_p, b_hat = size_p[pos], sys_p[pos], type_p[pos], b_hat[pos]
        size_t, sys_t, type_t = size_t[pos], sys_t[pos], type_t[pos]
        d_p, l_p = size_p[:, 0] * DIAM_SCALE, size_p[:, 1] * LEN_SCALE
        d_t, l_t = size_t[:, 0] * DIAM_SCALE, size_t[:, 1] * LEN_SCALE
        d_err += (d_p - d_t).abs().tolist()
        l_err += (l_p - l_t).abs().tolist()
        s_hat, t_hat = sys_p.argmax(1), type_p.argmax(1)
        sys_ok += (s_hat == sys_t).tolist()
        type_ok += (t_hat == type_t).tolist()
        for i in range(len(size_t)):
            pred = snap(int(s_hat[i]), float(d_p[i]), float(l_p[i]))
            true = snap(int(sys_t[i]), float(d_t[i]), float(l_t[i]))
            exact.append(int(b_hat[i]) == 1 and pred[0].name == true[0].name
                         and abs(pred[1] - true[1]) < 0.01 and int(t_hat[i]) == int(type_t[i]))
    m = lambda v: float(np.mean(v)) if v else float("nan")
    result = {"bolt_acc": m(bolt_ok), "diam_mae_mm": m(d_err), "len_mae_mm": m(l_err),
            "system_acc": m(sys_ok), "type_acc": m(type_ok), "exact_acc": m(exact),
            "mask_iou": float(np.mean(intersection[1:] / np.maximum(union[1:], 1)))}
    if collect_geometry:
        result['_geometry'] = records
    return result


def fused_validation(records_by_folder):
    """Select on the deployed size answer, with validation-only calibration."""
    usable = [r for rows in records_by_folder for r in rows
              if r['bolt'] and r['geometry'] is not None and r['geometry']['quality'] >= .7]
    calibration = None
    if len(usable) >= 20:
        geo = np.array([[r['geometry']['diameter_mm'], r['geometry']['length_mm']] for r in usable])
        truth = np.array([r['truth'] for r in usable])
        reg = np.array([r['size'] for r in usable])
        calibration = fit_linear(geo, truth)
        corrected = geo * calibration['gain'] + calibration['offset']
        calibration['fusion_weights'] = fit_fusion(corrected, reg, truth)
    scores = []
    for rows in records_by_folder:
        correct = []
        for r in rows:
            if not r['bolt']:
                correct.append(not r['pred_bolt'])
                continue
            size = r['size']
            if calibration is not None and r['geometry'] is not None:
                g = r['geometry']
                geo = np.array([g['diameter_mm'], g['length_mm']])
                geo = geo * calibration['gain'] + calibration['offset']
                weight = np.array(calibration['fusion_weights'])
                size = geo * weight + size * (1 - weight)
            pred = snap(r['system'], *size)
            true = snap(r['true_system'], *r['truth'])
            correct.append(bool(r['pred_bolt'] and pred[0].name == true[0].name and
                                abs(pred[1] - true[1]) < .01 and r['type'] == r['true_type']))
        scores.append(float(np.mean(correct)))
    return scores, calibration


def fmt(r):
    return (f"bolt/not {r['bolt_acc']:.1%}  diam ±{r['diam_mae_mm']:.2f}mm  len ±{r['len_mae_mm']:.2f}mm  "
            f"system {r['system_acc']:.1%}  type {r['type_acc']:.1%}  fully correct {r['exact_acc']:.1%}  "
            f"mask IoU {r['mask_iou']:.1%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True, help="folders with labels.csv")
    ap.add_argument("--decoder-only", action="store_true", help="warm up decoder with frozen v2 features and heads")
    ap.add_argument("--v3", action="store_true", help="train the outline decoder as well as the four heads")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--patience", type=int, default=8, help="stop after this many epochs without improvement; 0 disables")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--decoder-lr-mult", type=float, default=3., help="decoder learning rate relative to the pretrained backbone")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--split-by-object", nargs="*", default=["data/real"],
                    help="folders whose validation holds out whole objects (your own photos)")
    ap.add_argument("--steps-per-epoch", type=int, default=0, help="0 = one pass over the data")
    ap.add_argument("--arch", default="mobilenet_v3_small", choices=ARCHS,
                    help="mobilenet_v3_small runs well on a Raspberry Pi")
    ap.add_argument("--pretrained", action="store_true", help="start from ImageNet weights")
    ap.add_argument("--teacher", help="preserve a frozen model's size/system/type outputs while learning the new tasks")
    ap.add_argument("--init", help="checkpoint to fine-tune from")
    ap.add_argument("--select", choices=["first", "mean"], default="first",
                    help="keep the checkpoint that scores best on the first folder, or on the average")
    ap.add_argument("--out", help="default: models/boltnet_v3.pt for v3, models/boltnet.pt for legacy")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--device", default=pick_device())
    a = ap.parse_args()
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    cv2.setNumThreads(1)

    seen = initializer_sources(a.init)
    trains, vals = zip(*(split(f, a.val_frac, seed=0, by_object=f.rstrip("/") in
                               [g.rstrip("/") for g in a.split_by_object], seen=seen) for f in a.data))
    train_ds = ConcatDataset(trains)
    # Each folder contributes equally per epoch, so 200 real photos aren't
    # drowned out by 20,000 synthetic ones.
    weights = np.concatenate([np.full(len(t), 1.0 / len(t)) for t in trains])
    n_steps = a.steps_per_epoch or len(train_ds) // a.batch
    sampler = WeightedRandomSampler(weights, n_steps * a.batch, replacement=True)
    train_dl = DataLoader(train_ds, a.batch, sampler=sampler, num_workers=a.workers, drop_last=True)
    val_dls = [DataLoader(v, a.batch, num_workers=a.workers) for v in vals]

    checkpoint = None
    if a.init:
        model, checkpoint = load(a.init, a.device, segmentation=True if a.v3 else None)
        model.train()
    else:
        model = BoltNet(a.arch, a.pretrained, segmentation=a.v3).to(a.device)
    training_keys, validation_digest = verify_partition(trains, vals, checkpoint)
    print(f'fixed validation identities: {validation_digest}', flush=True)
    if a.out is None:
        a.out = "models/boltnet_v3.pt" if model.segmentation else "models/boltnet.pt"
    teacher = load(a.teacher, a.device)[0].requires_grad_(False) if a.teacher else None
    if a.decoder_only:
        if not model.segmentation:
            raise ValueError('--decoder-only requires --v3')
        for name, parameter in model.named_parameters():
            parameter.requires_grad_(name.startswith('decoder.'))
    if model.segmentation and not a.decoder_only:
        groups = [dict(params=[p for name, p in model.named_parameters() if not name.startswith('decoder.')], lr=a.lr),
                  dict(params=list(model.decoder.parameters()), lr=a.lr * a.decoder_lr_mult)]
        max_lr = [a.lr, a.lr * a.decoder_lr_mult]
    else:
        groups = [p for p in model.parameters() if p.requires_grad]
        max_lr = a.lr
    opt = torch.optim.AdamW(groups, lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr, total_steps=a.epochs * n_steps, pct_start=0.1)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)

    best, stale = -1.0, 0
    history = []
    start = time.perf_counter()
    for epoch in range(1, a.epochs + 1):
        model.train()
        if a.decoder_only:
            model.backbone.eval()
            model.shared.eval()
        total = 0.0
        for step, (x, size_t, sys_t, type_t, bolt_t, mask_t) in enumerate(train_dl, 1):
            x, size_t = x.to(a.device), size_t.to(a.device)
            teacher_out = None
            if teacher is not None:
                with torch.no_grad():
                    teacher_out = teacher(x)
            loss = loss_fn(model(x), size_t, sys_t.to(a.device), type_t.to(a.device),
                           bolt_t.to(a.device), mask_t.to(a.device), teacher_out)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            total += loss.item()
            if step % 50 == 0:
                print(f"  epoch {epoch} step {step}/{n_steps} loss {total / step:.4f}", flush=True)

        print(f"epoch {epoch}: train loss {total / max(1, n_steps):.4f}")
        scores, metrics, geometry_records = [], {}, []
        for folder, dl in zip(a.data, val_dls):
            r = evaluate(model, dl, a.device, collect_geometry=model.segmentation)
            if model.segmentation:
                geometry_records.append(r.pop("_geometry"))
            scores.append(r["exact_acc"])
            metrics[folder] = r
            print(f"  val [{folder}] {fmt(r)}")
        selection_calibration = None
        if model.segmentation:
            scores, selection_calibration = fused_validation(geometry_records)
            for folder, score in zip(a.data, scores):
                metrics[folder]['fused_exact_acc'] = score
                print(f"  val [{folder}] fused fully correct {score:.1%}", flush=True)
        # Model selection: the first folder (put your real data first), or the average.
        score = scores[0] if a.select == "first" else float(np.mean(scores))
        extra = {"epoch": epoch, "val": score, "data": list(a.data), "args": vars(a),
                 "metrics": metrics, "selection_calibration": selection_calibration,
                 "training_keys": training_keys, "validation_keys_sha256": validation_digest,
                 "optimizer": opt.state_dict(), "scheduler": sched.state_dict()}
        save(model, str(Path(a.out).with_suffix(".last.pt")), extra)
        if score > best:
            best, stale = score, 0
            save(model, a.out, extra)
            print(f"  saved {a.out}")
        else:
            stale += 1
        history.append({"epoch": epoch, "loss": total / max(1, n_steps), "score": score,
                        "metrics": metrics, "elapsed_s": time.perf_counter() - start})
        Path(a.out).with_suffix(".history.json").write_text(json.dumps(history, indent=2))
        if a.patience and stale >= a.patience:
            print(f"early stop after {stale} epochs without validation improvement", flush=True)
            break


if __name__ == "__main__":
    main()
