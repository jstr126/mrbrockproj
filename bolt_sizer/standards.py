"""Standard bolt sizes (metric + imperial), label parsing, and snapping
continuous predictions to the nearest real-world size. The tables here are
built from the active entries of the bolt catalog (catalog.py)."""
from dataclasses import dataclass
from fractions import Fraction
import re

from .catalog import CATALOG, INCH, lengths_in_mm

METRIC, IMPERIAL = 0, 1
SYSTEM_NAMES = ["metric", "imperial"]

# Head styles the network classifies, in catalog order (the order is baked into
# the trained model). Length is measured per catalog["head_types"][...]["length_measured"].
HEAD_TYPES = [k for k, h in CATALOG["head_types"].items() if h["active"]]
HEAD_TYPE_NAMES = {k: CATALOG["head_types"][k]["name"] for k in HEAD_TYPES}


@dataclass(frozen=True)
class Thread:
    name: str          # "M6" or "1/4-20"
    system: int
    diameter_mm: float
    pitch_mm: float    # coarse pitch
    head_af_mm: float  # hex head width across flats
    head_k_mm: float   # hex head height


def _threads(system):
    hex_dims = CATALOG["head_types"]["hex"]["dims"]
    out = []
    for size, t in CATALOG["systems"][SYSTEM_NAMES[system]]["threads"].items():
        if not t["active"]:
            continue
        if system == METRIC:
            af, k = hex_dims["metric_mm"][size]
            out.append(Thread(size, system, t["diameter_mm"], t["pitch_coarse_mm"], af, k))
        else:
            af, k = hex_dims["imperial_in"][size]
            out.append(Thread(f"{size}-{t['tpi_unc']}", system, t["diameter_in"] * INCH,
                              INCH / t["tpi_unc"], af * INCH, k * INCH))
    return out


METRIC_THREADS = _threads(METRIC)
IMPERIAL_THREADS = _threads(IMPERIAL)
THREADS = {METRIC: METRIC_THREADS, IMPERIAL: IMPERIAL_THREADS}

# Longest bolt the default 128 mm canvas can hold (4" shank + head).
MAX_LENGTH_MM = CATALOG["reference"]["max_length_in"] * INCH


def lengths_mm(system):
    return lengths_in_mm(SYSTEM_NAMES[system])


def format_inches(value):
    frac = Fraction(value).limit_denominator(16)
    whole, rem = divmod(frac, 1)
    if rem == 0:
        return f"{whole}"
    if whole == 0:
        return f"{rem}"
    return f"{whole}-{rem}"


def format_label(thread, length_mm, head_type=None):
    if thread.system == METRIC:
        size = f"{thread.name} x {length_mm:g}"
    else:
        size = f"{thread.name} x {format_inches(length_mm / INCH)}\""
    return f"{size} {HEAD_TYPE_NAMES[head_type]}" if head_type else size


def parse_head_type(text):
    t = text.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {"hex": "hex", "hex_bolt": "hex", "hhcs": "hex",
               "socket": "socket_cap", "socket_cap": "socket_cap", "shcs": "socket_cap",
               "carriage": "carriage", "flat": "flat", "countersunk": "flat", "fhcs": "flat",
               "button": "button", "bhcs": "button"}
    if t not in aliases:
        raise ValueError(f"unknown head type {text!r}; use one of {HEAD_TYPES}")
    return aliases[t]


def _parse_inches(text):
    text = text.strip().rstrip('"')
    if "-" in text:                      # 1-1/2
        whole, frac = text.split("-", 1)
        return float(int(whole) + Fraction(frac))
    return float(Fraction(text))         # 3/4, 1.5, 2


def parse_label(label):
    """Parse 'M6x30', 'M6 x 1.0 x 30', '1/4-20x1-1/2', '#10-24 x 3/4'.

    Returns (thread, length_mm)."""
    s = label.strip().replace(" ", "").replace("×", "x")
    m = re.fullmatch(r"[mM](\d+)(?:x[\d.]+)?x([\d.]+)(?:mm)?", s)
    if m:
        name = f"M{m.group(1)}"
        thread = next((t for t in METRIC_THREADS if t.name == name), None)
        if thread is None:
            raise ValueError(f"unsupported metric size {name}")
        return thread, float(m.group(2))

    m = re.fullmatch(r"(#?\d+(?:/\d+)?)(?:-(\d+))?x([\d./-]+)\"?", s)
    if m:
        size = m.group(1).lstrip("#")
        for t in IMPERIAL_THREADS:
            t_size = t.name.split("-")[0].lstrip("#")
            if t_size == size and (m.group(2) is None or t.name.endswith("-" + m.group(2))):
                return t, _parse_inches(m.group(3)) * INCH
        raise ValueError(f"unsupported imperial size {m.group(1)}")

    raise ValueError(f"can't parse bolt label {label!r} (try 'M6x30' or '1/4-20x1-1/2')")


def snap(system, diameter_mm, length_mm):
    """Nearest standard (thread, length) within one system."""
    thread = min(THREADS[system], key=lambda t: abs(t.diameter_mm - diameter_mm))
    length = min(lengths_mm(system), key=lambda L: abs(L - length_mm))
    return thread, length
