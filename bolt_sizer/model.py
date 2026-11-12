"""BoltNet: four classification/regression heads and an optional outline decoder.
Training-side only
(needs torch); the Pi runs the exported ONNX file through bolt_sizer/infer.py."""
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision

from .standards import HEAD_TYPES, SYSTEM_NAMES

DIAM_SCALE, LEN_SCALE = 10.0, 50.0       # regression targets are mm / scale
MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

# mobilenet_v3_small: ~1.5M params, a few hundred ms per frame on a Pi 4, fast on a Pi 5.
# resnet18: more accurate if you have the compute (desktop / Jetson).
ARCHS = ["mobilenet_v3_small", "mobilenet_v3_large", "resnet18"]


def _backbone(arch, pretrained):
    if arch == "resnet18":
        net = torchvision.models.resnet18(
            weights=torchvision.models.ResNet18_Weights.DEFAULT if pretrained else None)
        feat, net.fc = net.fc.in_features, nn.Identity()
    elif arch == "mobilenet_v3_small":
        net = torchvision.models.mobilenet_v3_small(
            weights=torchvision.models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None)
        feat, net.classifier = net.classifier[0].in_features, nn.Identity()
    elif arch == "mobilenet_v3_large":
        net = torchvision.models.mobilenet_v3_large(
            weights=torchvision.models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None)
        feat, net.classifier = net.classifier[0].in_features, nn.Identity()
    else:
        raise ValueError(f"unknown arch {arch}; choose from {ARCHS}")
    return net, feat


class OutlineDecoder(nn.Module):
    """Small top-down pyramid at strides 32, 16, 8, 4 and 2."""
    def __init__(self, channels=(16, 16, 24, 48, 576), width=24):
        super().__init__()
        self.lateral = nn.ModuleList(nn.Conv2d(c, width, 1) for c in channels)
        self.refine = nn.ModuleList(nn.Sequential(
            nn.Conv2d(width, width, 3, padding=1, groups=width), nn.ReLU(inplace=True),
            nn.Conv2d(width, width, 1), nn.ReLU(inplace=True)) for _ in channels)
        self.output = nn.Conv2d(width, 3, 1)

    def forward(self, features):
        h = self.refine[-1](self.lateral[-1](features[-1]))
        for i in range(len(features) - 2, -1, -1):
            h = self.refine[i](self.lateral[i](features[i]) +
                               F.interpolate(h, size=features[i].shape[-2:],
                                             mode="bilinear", align_corners=False))
        return self.output(h)


class BoltNet(nn.Module):
    def __init__(self, arch="mobilenet_v3_small", pretrained=False, segmentation=False):
        super().__init__()
        self.arch = arch
        self.segmentation = segmentation
        if segmentation and arch != "mobilenet_v3_small":
            raise ValueError("v3 outline decoder requires mobilenet_v3_small")
        self.backbone, feat = _backbone(arch, pretrained)
        self.shared = nn.Sequential(nn.Linear(feat, 256), nn.ReLU(inplace=True), nn.Dropout(0.2))
        self.size_head = nn.Linear(256, 2)                  # diameter, length
        self.system_head = nn.Linear(256, len(SYSTEM_NAMES))
        self.type_head = nn.Linear(256, len(HEAD_TYPES))
        self.bolt_head = nn.Linear(256, 2)                  # not a bolt, bolt
        if segmentation:
            self.decoder = OutlineDecoder()

    def forward(self, x):
        """x: float tensor (B, 3, H, W), RGB in [0, 1]."""
        x = (x - MEAN.to(x.device)) / STD.to(x.device)
        features = []
        if self.segmentation:
            for i, block in enumerate(self.backbone.features):
                x = block(x)
                if i in (0, 1, 3, 8, 12):
                    features.append(x)
            x = self.backbone.avgpool(x).flatten(1)
        else:
            x = self.backbone(x)
        h = self.shared(x)
        out = self.size_head(h), self.system_head(h), self.type_head(h), self.bolt_head(h)
        return (*out, self.decoder(features)) if self.segmentation else out


def to_tensor(canvas_bgr):
    rgb = canvas_bgr[:, :, ::-1].astype(np.float32) / 255.0
    return torch.from_numpy(np.ascontiguousarray(rgb.transpose(2, 0, 1)))


def save(model, path, extra=None):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save({"state_dict": model.state_dict(), "arch": model.arch,
                "segmentation": model.segmentation, **(extra or {})}, temporary)
    temporary.replace(path)


def load(path, device="cpu", segmentation=None):
    ckpt = torch.load(path, map_location=device)
    has_mask = ckpt.get("segmentation", any(k.startswith("decoder.") for k in ckpt["state_dict"]))
    segmentation = has_mask if segmentation is None else segmentation
    model = BoltNet(ckpt.get("arch", "resnet18"), segmentation=segmentation)
    result = model.load_state_dict(ckpt["state_dict"], strict=False)
    if result.unexpected_keys or any(not k.startswith("decoder.") for k in result.missing_keys):
        raise ValueError(f"incompatible checkpoint: {result}")
    return model.to(device).eval(), ckpt
