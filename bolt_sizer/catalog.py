"""The bolt catalog: every bolt type, size, and sorting factor the sorter knows
about, in one dictionary. This is the single source of truth: standards.py,
the synthetic data generator, the network's labels, and the sorting bins are
all built from it.

    python -m bolt_sizer.catalog          # print a readable summary
    python -m bolt_sizer.catalog --json   # dump the whole catalog as JSON

"active": True marks what the sorter currently handles; the current model
was trained on exactly those entries. To add a size, length or head type,
set it active, regenerate the synthetic data and retrain. Head types are
used in their order here, so add new ones at the end of the list.

Dimensions are typical maximums from the named standards, for checking
measurements and rendering training images. Check them against your
supplier's spec sheets before relying on them for anything critical.
"""
import json
import sys

INCH = 25.4

CATALOG = {
    "version": 1,

    # What the camera measures against.
    "reference": {
        "board": "printed checkerboard",
        "square_in": 0.25,
        "square_mm": 6.35,
        "canvas_px_per_mm": 4.0,
        "canvas_mm": 128.0,
        "max_length_in": 4,          # longest bolt that fits the canvas (4" shank + head)
    },

    # ---------------------------------------------------------------------------
    # Thread systems and sizes
    # ---------------------------------------------------------------------------
    "systems": {
        "metric": {
            "standard": "ISO 261/262 metric thread; coarse pitch is the default",
            "name_format": "M{size}",            # e.g. M6
            "length_unit": "mm",
            "threads": {
                # size: diameter (mm), coarse / fine pitch (mm per thread)
                "M2":   {"diameter_mm": 2.0,  "pitch_coarse_mm": 0.40, "pitch_fine_mm": 0.25, "active": False},
                "M2.5": {"diameter_mm": 2.5,  "pitch_coarse_mm": 0.45, "pitch_fine_mm": 0.35, "active": False},
                "M3":   {"diameter_mm": 3.0,  "pitch_coarse_mm": 0.50, "pitch_fine_mm": 0.35, "active": True},
                "M4":   {"diameter_mm": 4.0,  "pitch_coarse_mm": 0.70, "pitch_fine_mm": 0.50, "active": True},
                "M5":   {"diameter_mm": 5.0,  "pitch_coarse_mm": 0.80, "pitch_fine_mm": 0.50, "active": True},
                "M6":   {"diameter_mm": 6.0,  "pitch_coarse_mm": 1.00, "pitch_fine_mm": 0.75, "active": True},
                "M8":   {"diameter_mm": 8.0,  "pitch_coarse_mm": 1.25, "pitch_fine_mm": 1.00, "active": True},
                "M10":  {"diameter_mm": 10.0, "pitch_coarse_mm": 1.50, "pitch_fine_mm": 1.25, "active": True},
                "M12":  {"diameter_mm": 12.0, "pitch_coarse_mm": 1.75, "pitch_fine_mm": 1.25, "active": True},
                "M14":  {"diameter_mm": 14.0, "pitch_coarse_mm": 2.00, "pitch_fine_mm": 1.50, "active": False},
                "M16":  {"diameter_mm": 16.0, "pitch_coarse_mm": 2.00, "pitch_fine_mm": 1.50, "active": False},
                "M20":  {"diameter_mm": 20.0, "pitch_coarse_mm": 2.50, "pitch_fine_mm": 1.50, "active": False},
            },
            "standard_lengths_mm": [3, 4, 5, 6, 8, 10, 12, 14, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60,
                                    65, 70, 75, 80, 90, 100, 110, 120, 130, 140, 150],
            "active_lengths_mm": [8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100],
        },
        "imperial": {
            "standard": "ASME B1.1 Unified thread: UNC (coarse) is the default, UNF (fine)",
            "name_format": "{size}-{tpi}",       # e.g. 1/4-20 (TPI = threads per inch)
            "length_unit": "in",
            "threads": {
                # size: major diameter (in), coarse / fine threads per inch
                "#4":   {"diameter_in": 0.1120, "tpi_unc": 40, "tpi_unf": 48, "active": False},
                "#6":   {"diameter_in": 0.1380, "tpi_unc": 32, "tpi_unf": 40, "active": True},
                "#8":   {"diameter_in": 0.1640, "tpi_unc": 32, "tpi_unf": 36, "active": True},
                "#10":  {"diameter_in": 0.1900, "tpi_unc": 24, "tpi_unf": 32, "active": True},
                "1/4":  {"diameter_in": 0.2500, "tpi_unc": 20, "tpi_unf": 28, "active": True},
                "5/16": {"diameter_in": 0.3125, "tpi_unc": 18, "tpi_unf": 24, "active": True},
                "3/8":  {"diameter_in": 0.3750, "tpi_unc": 16, "tpi_unf": 24, "active": True},
                "7/16": {"diameter_in": 0.4375, "tpi_unc": 14, "tpi_unf": 20, "active": True},
                "1/2":  {"diameter_in": 0.5000, "tpi_unc": 13, "tpi_unf": 20, "active": True},
                "5/8":  {"diameter_in": 0.6250, "tpi_unc": 11, "tpi_unf": 18, "active": False},
                "3/4":  {"diameter_in": 0.7500, "tpi_unc": 10, "tpi_unf": 16, "active": False},
            },
            "standard_lengths_in": ["1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "1", "1-1/4", "1-1/2",
                                    "1-3/4", "2", "2-1/4", "2-1/2", "2-3/4", "3", "3-1/4", "3-1/2",
                                    "4", "4-1/2", "5", "6"],
            "active_lengths_in": ["1/4", "3/8", "1/2", "5/8", "3/4", "1", "1-1/4", "1-1/2", "1-3/4",
                                  "2", "2-1/4", "2-1/2", "3", "3-1/2", "4"],
        },
    },

    # Sizes that are almost the same diameter in both systems. The camera can't
    # separate these on diameter alone; it has to rely on thread pitch / head size.
    "look_alikes": [
        {"metric": "M3",  "imperial": "#4",   "diameter_gap_mm": 0.16},
        {"metric": "M4",  "imperial": "#8",   "diameter_gap_mm": 0.17},
        {"metric": "M5",  "imperial": "#10",  "diameter_gap_mm": 0.17},
        {"metric": "M6",  "imperial": "1/4",  "diameter_gap_mm": 0.35},
        {"metric": "M8",  "imperial": "5/16", "diameter_gap_mm": 0.06},
        {"metric": "M10", "imperial": "3/8",  "diameter_gap_mm": 0.48},
        {"metric": "M12", "imperial": "1/2",  "diameter_gap_mm": 0.70},
        {"metric": "M16", "imperial": "5/8",  "diameter_gap_mm": 0.12},
    ],

    # ---------------------------------------------------------------------------
    # Head types. The first five are what the network classifies, in this order.
    # "dims": head width (across flats for hex, else diameter) and height, per size.
    # ---------------------------------------------------------------------------
    "head_types": {
        "hex": {
            "active": True,
            "name": "hex bolt",
            "also_called": ["hex cap screw", "hex head screw", "HHCS"],
            "standards": ["ISO 4014 / DIN 931 (partly threaded)", "ISO 4017 / DIN 933 (fully threaded)",
                          "ASME B18.2.1"],
            "drive": "external hex (spanner/wrench)",
            "length_measured": "under the head to the tip",
            "looks_like": "six flat faces on the head; seen side-on, 2-3 flat bands",
            "dims": {
                "metric_mm": {  # width across flats, head height (ISO 4017)
                    "M2": (4.0, 1.4), "M2.5": (5.0, 1.7), "M3": (5.5, 2.0), "M4": (7.0, 2.8),
                    "M5": (8.0, 3.5), "M6": (10.0, 4.0), "M8": (13.0, 5.3), "M10": (16.0, 6.4),
                    "M12": (18.0, 7.5), "M14": (21.0, 8.8), "M16": (24.0, 10.0), "M20": (30.0, 12.5),
                },
                "imperial_in": {  # ASME B18.2.1 (#-sizes: hex head machine screws)
                    "#4": (0.1875, 0.060), "#6": (0.2500, 0.093), "#8": (0.2500, 0.110),
                    "#10": (0.3125, 0.120), "1/4": (0.4375, 0.163), "5/16": (0.5000, 0.211),
                    "3/8": (0.5625, 0.243), "7/16": (0.6250, 0.291), "1/2": (0.7500, 0.323),
                    "5/8": (0.9375, 0.403), "3/4": (1.1250, 0.483),
                },
            },
        },
        "socket_cap": {
            "active": True,
            "name": "socket head cap screw",
            "also_called": ["SHCS", "Allen bolt", "cap screw"],
            "standards": ["ISO 4762 / DIN 912", "ASME B18.3"],
            "drive": "hex socket (Allen key)",
            "length_measured": "under the head to the tip",
            "looks_like": "tall round head with straight sides, about 1.5x the thread diameter",
            "dims": {
                "metric_mm": {  # head diameter, head height (= thread diameter)
                    "M2": (3.8, 2.0), "M2.5": (4.5, 2.5), "M3": (5.5, 3.0), "M4": (7.0, 4.0),
                    "M5": (8.5, 5.0), "M6": (10.0, 6.0), "M8": (13.0, 8.0), "M10": (16.0, 10.0),
                    "M12": (18.0, 12.0), "M14": (21.0, 14.0), "M16": (24.0, 16.0), "M20": (30.0, 20.0),
                },
                "imperial_in": {
                    "#4": (0.183, 0.112), "#6": (0.226, 0.138), "#8": (0.270, 0.164), "#10": (0.312, 0.190),
                    "1/4": (0.375, 0.250), "5/16": (0.469, 0.312), "3/8": (0.562, 0.375),
                    "7/16": (0.656, 0.438), "1/2": (0.750, 0.500), "5/8": (0.938, 0.625),
                    "3/4": (1.125, 0.750),
                },
            },
        },
        "carriage": {
            "active": True,
            "name": "carriage bolt",
            "also_called": ["coach bolt", "round head square neck bolt"],
            "standards": ["DIN 603", "ASME B18.5"],
            "drive": "none (square neck locks into wood)",
            "length_measured": "under the head to the tip (includes the square neck)",
            "looks_like": "low smooth dome, much wider than the thread, then a short square neck",
            "dims": {
                "metric_mm": {  # head diameter, head height (DIN 603)
                    "M5": (13.55, 3.3), "M6": (16.55, 3.88), "M8": (20.65, 4.88), "M10": (24.65, 5.38),
                    "M12": (30.65, 6.95), "M16": (38.8, 8.95), "M20": (46.8, 11.05),
                },
                "imperial_in": {
                    "#10": (0.469, 0.114), "1/4": (0.594, 0.156), "5/16": (0.719, 0.187),
                    "3/8": (0.844, 0.219), "7/16": (0.969, 0.250), "1/2": (1.094, 0.281),
                    "5/8": (1.344, 0.344), "3/4": (1.594, 0.406),
                },
            },
        },
        "flat": {
            "active": True,
            "name": "flat head (countersunk)",
            "also_called": ["countersunk screw", "FHCS", "flat head socket cap screw"],
            "standards": ["ISO 10642 / DIN 7991 (90 degree head)", "ASME B18.3 (82 degree head)"],
            "drive": "hex socket (also Phillips/slotted/Torx)",
            "length_measured": "overall, including the head",
            "looks_like": "cone-shaped head that sits flush; metric 90 deg, imperial 82 deg",
            "dims": {
                "metric_mm": {  # head diameter, head height
                    "M3": (6.72, 1.86), "M4": (8.96, 2.48), "M5": (11.2, 3.1), "M6": (13.44, 3.72),
                    "M8": (17.92, 4.96), "M10": (22.4, 6.2), "M12": (26.88, 7.44), "M16": (33.6, 8.8),
                    "M20": (40.32, 10.16),
                },
                "imperial_in": {
                    "#4": (0.255, 0.083), "#6": (0.307, 0.097), "#8": (0.359, 0.115), "#10": (0.411, 0.127),
                    "1/4": (0.531, 0.161), "5/16": (0.656, 0.198), "3/8": (0.781, 0.234),
                    "1/2": (1.031, 0.311), "5/8": (1.281, 0.384), "3/4": (1.531, 0.456),
                },
            },
        },
        "button": {
            "active": True,
            "name": "button head",
            "also_called": ["button head socket cap screw", "BHCS"],
            "standards": ["ISO 7380", "ASME B18.3"],
            "drive": "hex socket (also Torx)",
            "length_measured": "under the head to the tip",
            "looks_like": "low rounded dome, wider than a socket cap but much flatter",
            "dims": {
                "metric_mm": {  # head diameter, head height (ISO 7380)
                    "M3": (5.7, 1.65), "M4": (7.6, 2.2), "M5": (9.5, 2.75), "M6": (10.5, 3.3),
                    "M8": (14.0, 4.4), "M10": (17.5, 5.5), "M12": (21.0, 6.6), "M16": (28.0, 8.8),
                },
                "imperial_in": {
                    "#4": (0.213, 0.059), "#6": (0.270, 0.080), "#8": (0.312, 0.090), "#10": (0.375, 0.110),
                    "1/4": (0.437, 0.132), "5/16": (0.562, 0.165), "3/8": (0.656, 0.198),
                    "1/2": (0.875, 0.264), "5/8": (1.000, 0.330),
                },
            },
        },
        # Not handled yet: add images/renders for these, set active, retrain.
        "flange_hex": {
            "active": False, "name": "hex flange bolt", "standards": ["ISO 4162", "ASME B18.2.1"],
            "drive": "external hex", "length_measured": "under the flange",
            "looks_like": "hex head with a round washer-like flange underneath", "dims": None,
        },
        "pan": {
            "active": False, "name": "pan head machine screw", "standards": ["ISO 7045", "ASME B18.6.3"],
            "drive": "Phillips / slotted / Torx", "length_measured": "under the head",
            "looks_like": "flat-topped low cylinder with rounded edge", "dims": None,
        },
        "oval": {
            "active": False, "name": "oval head (raised countersunk)", "standards": ["ISO 2010", "ASME B18.6.3"],
            "drive": "Phillips / slotted", "length_measured": "overall, excluding the raised dome",
            "looks_like": "countersunk cone with a domed top", "dims": None,
        },
        "shoulder": {
            "active": False, "name": "shoulder bolt", "standards": ["ISO 7379", "ASME B18.3"],
            "drive": "hex socket", "length_measured": "shoulder length (under head to thread)",
            "looks_like": "socket head, smooth wider shoulder, then a shorter, narrower thread", "dims": None,
        },
        "set_screw": {
            "active": False, "name": "set screw (grub screw)", "standards": ["ISO 4026-4029", "ASME B18.3"],
            "drive": "hex socket", "length_measured": "overall",
            "looks_like": "no head at all: thread along the whole length", "dims": None,
        },
    },

    # Anything on the board that is NOT one of the bolts above goes to the reject bin.
    "not_a_bolt": {
        "examples": ["nuts (hex, wing, cap, T-nuts)", "washers (flat, spring, toothed)",
                     "wood / drywall / self-tapping screws (pointed tip, no machine thread)",
                     "lag screws", "rivets", "pins and dowels", "coins", "batteries", "anything else"],
        "note": "Lag screws have hex heads but wood threads; they are rejected as not a bolt.",
    },

    # ---------------------------------------------------------------------------
    # Other properties of a bolt. The camera can't (or doesn't yet) sort by
    # these, but they are listed so they can be added as factors later.
    # ---------------------------------------------------------------------------
    "finishes": {
        "zinc":        {"name": "zinc plated (clear/blue)", "looks_like": "bright silver, slight blue tint"},
        "yellow_zinc": {"name": "yellow zinc", "looks_like": "gold / brassy, rainbow sheen"},
        "black_oxide": {"name": "black oxide", "looks_like": "matte to satin black"},
        "stainless":   {"name": "stainless steel (A2/304, A4/316)", "looks_like": "grey silver, no tint"},
        "galvanized":  {"name": "hot-dip galvanized", "looks_like": "dull grey, rough spangled coating"},
        "plain":       {"name": "plain / uncoated steel", "looks_like": "dark grey, often oily or rusty"},
        "brass":       {"name": "brass", "looks_like": "yellow metal, no sheen variation"},
        "nylon":       {"name": "nylon / plastic", "looks_like": "white or black, matte, translucent edges"},
    },
    "grades": {
        "metric": {  # property class, stamped on top of the head
            "4.6": "low strength, often unmarked",
            "8.8": "medium strength, the common default",
            "10.9": "high strength",
            "12.9": "very high strength, usually black socket screws",
            "A2-70": "stainless 304",
            "A4-80": "stainless 316",
        },
        "imperial": {  # SAE grade, shown by radial lines on top of the head
            "grade 2": "no marks",
            "grade 5": "3 radial lines",
            "grade 8": "6 radial lines",
            "18-8": "stainless, marked 18-8",
        },
    },
    "drives": ["external hex", "hex socket (Allen)", "Torx / 6-lobe", "Phillips", "Pozidriv",
               "slotted", "square (Robertson)", "none"],

    # ---------------------------------------------------------------------------
    # Sorting factors. "camera": can one camera looking down at a bolt lying on
    # the board see it? "in_model": does the current network output it?
    # ---------------------------------------------------------------------------
    "sorting_factors": [
        {"id": "is_bolt", "question": "Is it one of the catalog's bolts at all?",
         "camera": "yes", "in_model": True,
         "how": "classifier head; trained on nuts, washers, coins, pins, wood screws, empty board"},
        {"id": "system", "question": "Metric or imperial?",
         "camera": "partly", "in_model": True,
         "how": "thread pitch and head proportions; unreliable for look-alike sizes (see look_alikes)"},
        {"id": "diameter", "question": "Thread size (M6, 1/4...)",
         "camera": "yes", "in_model": True,
         "how": "measured in mm on the rectified board image, snapped to the nearest active size"},
        {"id": "length", "question": "Nominal length",
         "camera": "yes", "in_model": True,
         "how": "measured per head type's length convention, snapped to the nearest active length"},
        {"id": "head_type", "question": "Which head style?",
         "camera": "yes", "in_model": True,
         "how": "classifier head over the active head types"},
        {"id": "pitch", "question": "Coarse or fine thread?",
         "camera": "partly", "in_model": False,
         "how": "needs ~6+ px per thread: only for larger sizes, close-up or a sharper camera"},
        {"id": "thread_length", "question": "Fully or partly threaded?",
         "camera": "yes", "in_model": False,
         "how": "visible along the shank; not trained yet"},
        {"id": "finish", "question": "Coating / material (zinc, black oxide, stainless...)",
         "camera": "yes", "in_model": False,
         "how": "colour under even lighting; not trained yet"},
        {"id": "grade", "question": "Strength grade (8.8, 10.9, SAE 5, SAE 8...)",
         "camera": "no", "in_model": False,
         "how": "stamped on top of the head, which faces sideways when the bolt lies flat"},
        {"id": "drive", "question": "Drive type (hex socket, Torx, Phillips...)",
         "camera": "no", "in_model": False,
         "how": "on top of the head; same problem as grade"},
        {"id": "condition", "question": "Rusty, bent or damaged?",
         "camera": "partly", "in_model": False,
         "how": "not trained yet"},
    ],

    # ---------------------------------------------------------------------------
    # How a result becomes a bin.
    # ---------------------------------------------------------------------------
    "sorting_rules": {
        "bin_key": ["system", "thread", "length", "head_type"],   # one bin per combination
        "reject_bin": "REJECT: not a bolt",
        "review_bin": "REVIEW: check by hand",
        # Below these confidences the bolt goes to the review bin instead of a size bin.
        "min_bolt_conf": 0.7,
        "min_system_conf": 0.6,
        "min_type_conf": 0.6,
    },
}


def lengths_in_mm(system, key="active"):
    """Lengths for a system in mm; key is "active" or "standard"."""
    s = CATALOG["systems"][system]
    if system == "metric":
        return [float(x) for x in s[f"{key}_lengths_mm"]]
    return [_inches(x) * INCH for x in s[f"{key}_lengths_in"]]


def _inches(text):
    from fractions import Fraction
    if "-" in text:
        whole, frac = text.split("-", 1)
        return float(int(whole) + Fraction(frac))
    return float(Fraction(text))


def summary():
    lines = []
    for sys_name, s in CATALOG["systems"].items():
        lines.append(f"{sys_name.upper()}  ({s['standard']})")
        for size, t in s["threads"].items():
            if sys_name == "metric":
                info = f"{t['diameter_mm']:5.2f} mm  pitch {t['pitch_coarse_mm']} coarse / {t['pitch_fine_mm']} fine"
            else:
                info = f"{t['diameter_in'] * INCH:5.2f} mm  {t['tpi_unc']} TPI coarse / {t['tpi_unf']} fine"
            lines.append(f"  {'*' if t['active'] else ' '} {size:<5} {info}")
        unit = "mm" if sys_name == "metric" else "in"
        lines.append(f"  lengths ({unit}), active: {', '.join(str(x) for x in s[f'active_lengths_{unit}'])}")
    lines.append("HEAD TYPES")
    for key, h in CATALOG["head_types"].items():
        lines.append(f"  {'*' if h['active'] else ' '} {key:<11} {h['name']:<32} length: {h['length_measured']}")
    lines.append("SORTING FACTORS (camera can see / model outputs it)")
    for f in CATALOG["sorting_factors"]:
        lines.append(f"  {f['id']:<14} camera: {f['camera']:<7} model: {'yes' if f['in_model'] else 'no ':<4} {f['question']}")
    lines.append("* = active (the sorter handles it today)")
    return "\n".join(lines)


if __name__ == "__main__":
    print(json.dumps(CATALOG, indent=1) if "--json" in sys.argv else summary())
