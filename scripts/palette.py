#!/usr/bin/env python3
"""Local, deterministic scientific palette extraction and portable exports."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A, "p": P}
ET.register_namespace("a", A)
ET.register_namespace("p", P)
MAX_PIXELS = 160000
DEMO_COLORS = ["#28669B", "#DB7853", "#439B91", "#9274AA", "#D1AA45", "#BA637F"]


def hex_rgb(value):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("Colors must use exactly six HEX digits, for example #28669B.")
    return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))


def to_hex(rgb):
    return "#" + "".join(f"{int(x):02X}" for x in rgb)


def rgb_to_lab(rgb):
    v = np.asarray(rgb, dtype=float) / 255.0
    v = np.where(v <= .04045, v / 12.92, ((v + .055) / 1.055) ** 2.4)
    m1 = np.array([[.4122214708, .5363325363, .0514459929],
                   [.2119034982, .6806995451, .1073969566],
                   [.0883024619, .2817188376, .6299787005]])
    m2 = np.array([[.2104542553, .7936177850, -.0040720468],
                   [1.9779984951, -2.4285922050, .4505937099],
                   [.0259040371, .7827717662, -.8086757660]])
    return np.cbrt(v @ m1.T) @ m2.T


def lab_to_linear(lab):
    l, a, b = np.asarray(lab, dtype=float)
    x = np.array([l + .3963377774*a + .2158037573*b,
                  l - .1055613458*a - .0638541728*b,
                  l - .0894841775*a - 1.2914855480*b]) ** 3
    return np.array([4.0767416621*x[0] - 3.3077115913*x[1] + .2309699292*x[2],
                     -1.2684380046*x[0] + 2.6097574011*x[1] - .3413193965*x[2],
                     -.0041960863*x[0] - .7034186147*x[1] + 1.7076147010*x[2]])


def lab_to_rgb(lab):
    """Keep lightness/hue and reduce chroma to enter the sRGB gamut."""
    lab = np.asarray(lab, dtype=float).copy()
    lab[0] = np.clip(lab[0], 0, 1)
    lin = lab_to_linear(lab)
    if np.any(lin < -1e-7) or np.any(lin > 1 + 1e-7):
        lo, hi = 0., 1.
        for _ in range(24):
            mid = (lo + hi) / 2
            trial = lab_to_linear(lab * [1, mid, mid])
            if np.all(trial >= 0) and np.all(trial <= 1):
                lo = mid
            else:
                hi = mid
        lin = lab_to_linear(lab * [1, lo, lo])
    lin = np.clip(lin, 0, 1)
    srgb = np.where(lin <= .0031308, 12.92*lin, 1.055*lin**(1/2.4)-.055)
    return tuple(np.rint(srgb * 255).astype(int))


def luminance(rgb):
    v = np.asarray(rgb, dtype=float) / 255.
    v = np.where(v <= .04045, v/12.92, ((v+.055)/1.055)**2.4)
    return float(v @ [.2126, .7152, .0722])


def contrast(a, b):
    x, y = sorted([luminance(a), luminance(b)])
    return (y+.05)/(x+.05)


def interpolate(stops, count=257):
    positions = np.array([x[0] for x in stops])
    labs = np.array([rgb_to_lab(hex_rgb(x[1])) for x in stops])
    samples = np.linspace(0, 1, count)
    values = np.stack([np.interp(samples, positions, labs[:, j]) for j in range(3)], axis=1)
    return [to_hex(lab_to_rgb(v)) for v in values]


def monotonic_report(colors, mode):
    light = rgb_to_lab(np.array([hex_rgb(c) for c in colors]))[:, 0]
    # Allow one sRGB quantization step, and report the actual range.
    if mode == "diverging":
        mid = len(light)//2
        ok = np.all(np.diff(light[:mid+1]) >= -.003) and np.all(np.diff(light[mid:]) <= .003)
    else:
        ok = np.all(np.diff(light) <= .003)
    return {"metric": "Oklab L", "quantization_tolerance": .003,
            "monotonic_with_tolerance": bool(ok),
            "minimum": round(float(light.min()), 4), "maximum": round(float(light.max()), 4)}


def make_gradients(main):
    result = []
    for i, c in enumerate(main):
        lab = rgb_to_lab(hex_rgb(c))
        light = to_hex(lab_to_rgb([max(.96, lab[0]), lab[1]*.22, lab[2]*.22]))
        dark = to_hex(lab_to_rgb([min(.25, lab[0]), lab[1]*.55, lab[2]*.55]))
        # The main color is an exact midpoint anchor; do not alter it silently.
        stops = [[0., light], [.5, c], [1., dark]]
        values = interpolate(stops)
        values[128] = c
        result.append({"id": f"tonal-{i+1:02d}", "name": f"Color {i+1:02d}: light to dark",
                       "kind": "sequential", "basis": "derived", "parent_colors": [c],
                       "stops": stops, "colors": values,
                       "lightness": monotonic_report(values, "sequential")})
    # A multihue sequential scale shares the paper's hue family, with an ordered L ramp.
    labs = rgb_to_lab(np.array([hex_rgb(x) for x in main]))
    first, last = labs[0], labs[1 if len(main) > 1 else 0]
    values = []
    for t in np.linspace(0, 1, 257):
        ab = ((1-t)*first[1:] + t*last[1:]) * (.2 + .8*math.sin(math.pi*t))
        values.append(to_hex(lab_to_rgb([.96-.71*t, *ab])))
    result.append({"id": "sequential-multihue", "name": "Multihue sequential",
                   "kind": "sequential", "basis": "derived", "parent_colors": main[:2],
                   "stops": [[float(t), values[int(t*256)]] for t in np.linspace(0, 1, 9)],
                   "colors": values, "lightness": monotonic_report(values, "sequential")})
    # Maximize hue separation, rather than taking neighboring dominant colors.
    unit = labs[:, 1:] / np.maximum(np.linalg.norm(labs[:, 1:], axis=1, keepdims=True), 1e-9)
    distances = np.sum((unit[:, None] - unit[None, :])**2, axis=2)
    a, b = np.unravel_index(np.argmax(distances), distances.shape)
    left = to_hex(lab_to_rgb([.44, *labs[a, 1:]]))
    right = to_hex(lab_to_rgb([.44, *labs[b, 1:]]))
    center = to_hex(lab_to_rgb([.97, 0, 0]))
    stops = [[0., left], [.5, center], [1., right]]
    values = interpolate(stops)
    result.append({"id": "diverging", "name": "Diverging with a neutral center",
                   "kind": "diverging", "basis": "derived", "parent_colors": [main[a], main[b]],
                   "stops": stops, "colors": values,
                   "lightness": monotonic_report(values, "diverging")})
    return result


def audit(main, background):
    labs = rgb_to_lab(np.array([hex_rgb(x) for x in main]))
    pairwise, warnings = [], []
    for i in range(len(main)):
        for j in range(i+1, len(main)):
            distance = float(np.linalg.norm(labs[i]-labs[j]))
            dl = abs(float(labs[i, 0]-labs[j, 0]))
            pairwise.append({"colors": [i+1, j+1], "oklab_distance": round(distance, 4),
                             "lightness_difference": round(dl, 4)})
            if distance < .075:
                warnings.append(f"Colors {i+1} and {j+1} are similar; add markers or line styles.")
            if dl < .045:
                warnings.append(f"Colors {i+1} and {j+1} may merge in grayscale; add markers or line styles.")
    ratios = [round(contrast(hex_rgb(c), hex_rgb(background)), 3) for c in main]
    for i, r in enumerate(ratios):
        if r < 3:
            warnings.append(f"Color {i+1} has only {r}:1 contrast on the background; thin lines need review.")
    return {"background": background, "background_contrast": ratios, "pairwise": pairwise,
            "warnings": warnings, "threshold_basis": "Heuristics, not an accessibility certification",
            "color_vision_deficiency": "Not simulated; no colorblind-safe guarantee",
            "text": "Use dark text on white; choose black/white swatch labels by contrast."}


def build_palette(main, title, provenance, background="#FFFFFF"):
    if not 2 <= len(main) <= 8:
        raise ValueError("Choose 2 to 8 distinct main colors. A grayscale-only image needs explicit neutral extraction or manual colors.")
    main = [to_hex(hex_rgb(x)) for x in main]
    if len(set(main)) != len(main):
        raise ValueError("Duplicate main colors are not allowed.")
    hex_rgb(background)
    return {"schema_version": "1.0", "generator_version": VERSION, "title": title[:160],
            "color_space": "sRGB", "main": [{"id": f"color-{i+1:02d}", "hex": c,
            "rgb": list(hex_rgb(c)), "basis": provenance.get("basis", "manual")}
            for i, c in enumerate(main)], "background": background,
            "gradients": make_gradients(main), "provenance": provenance,
            "audit": audit(main, background),
            "powerpoint": {"accent_colors": (main*3)[:6], "extra_colors": main[6:],
                           "mapping": "First six main colors become Accent 1-6; extra colors remain in the swatch deck."}}


def executable(name, variable):
    configured = os.environ.get(variable)
    if configured:
        if not Path(configured).is_file():
            raise ValueError(f"{variable} points to a missing file.")
        return configured
    found = shutil.which(name)
    if not found:
        raise ValueError(f"{name} is missing. Install Poppler or set {variable}; PDF input is rendered locally.")
    return found


def parse_pages(value, total):
    if total < 1:
        raise ValueError("The PDF contains no pages.")
    if not value:
        return list(range(1, min(total, 6)+1))
    pages = []
    for term in value.split(","):
        if not re.fullmatch(r"\d+(?:-\d+)?", term.strip()):
            raise ValueError("Pages use one-based integers or ranges, such as 2,4-6.")
        start, *end = map(int, term.strip().split("-"))
        finish = end[0] if end else start
        if start < 1 or finish > total or finish < start:
            raise ValueError(f"Page range {term} is outside the PDF (1-{total}).")
        if finish-start+1 > 12:
            raise ValueError("Select at most 12 pages per run.")
        pages.extend(range(start, finish+1))
    pages = sorted(set(pages))
    if len(pages) > 12:
        raise ValueError("Select at most 12 pages per run.")
    return pages


def crop_image(im, crop):
    if crop is None:
        return im
    vals = [float(x) for x in crop.split(",")]
    if len(vals) != 4 or not (0 <= vals[0] < vals[2] <= 1 and 0 <= vals[1] < vals[3] <= 1):
        raise ValueError("Crop is normalized left,top,right,bottom within 0..1, with positive area.")
    box = tuple(round(v*(im.width if i%2 == 0 else im.height)) for i, v in enumerate(vals))
    if box[2] <= box[0] or box[3] <= box[1]:
        raise ValueError("Crop is smaller than one pixel.")
    return im.crop(box)


def normalized_image(path):
    with Image.open(path) as src:
        if src.width * src.height > 80_000_000:
            raise ValueError("Image exceeds 80 million pixels; crop or resize it first.")
        im = ImageOps.exif_transpose(src).copy()
        profile = src.info.get("icc_profile")
        if profile:
            try:
                alpha = im.getchannel("A") if "A" in im.getbands() else None
                source_mode = im.convert("RGB") if im.mode in ("RGBA", "P", "LA") else im
                im = ImageCms.profileToProfile(source_mode, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                                               ImageCms.createProfile("sRGB"), outputMode="RGB")
                if alpha is not None:
                    im.putalpha(alpha)
            except Exception as exc:
                raise ValueError("Embedded ICC profile could not be converted to sRGB.") from exc
        if "A" in im.getbands() or im.mode == "P":
            rgba = im.convert("RGBA")
            base = Image.new("RGBA", rgba.size, "white")
            im = Image.alpha_composite(base, rgba).convert("RGB")
        return im.convert("RGB")


def load_sources(paths, pages=None, crop=None, dpi=180):
    arrays, sources = [], []
    if not 72 <= dpi <= 300:
        raise ValueError("PDF DPI must be in 72..300.")
    for path in paths:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"Input does not exist: {path}")
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        record = {"filename": path.name, "sha256": sha, "crop": crop,
                  "mode": "rendered PDF" if path.suffix.lower() == ".pdf" else "raster image"}
        with tempfile.TemporaryDirectory(prefix="scientific-palette-") as staging:
            inputs = [path]
            if path.suffix.lower() == ".pdf":
                info = subprocess.run([executable("pdfinfo", "PALETTE_PDFINFO"), str(path)],
                                      capture_output=True, text=True, timeout=45, check=True)
                match = re.search(r"^Pages:\s+(\d+)", info.stdout, re.M)
                if not match:
                    raise ValueError("Could not determine PDF page count.")
                selected = parse_pages(pages, int(match[1]))
                record.update(pages=selected, dpi=dpi, automatic_page_limit=(pages is None))
                inputs = []
                for page in selected:
                    stem = Path(staging)/f"page-{page}"
                    subprocess.run([executable("pdftoppm", "PALETTE_PDFTOPPM"), "-f", str(page), "-l", str(page),
                                    "-singlefile", "-scale-to", "2400", "-r", str(dpi), "-png", str(path), str(stem)],
                                   capture_output=True, timeout=90, check=True)
                    inputs.append(stem.with_suffix(".png"))
            elif pages:
                raise ValueError("--pages only applies to PDF input.")
            for image_path in inputs:
                im = crop_image(normalized_image(image_path), crop)
                # Sample original pixels, without inventing resize-blended colors.
                a = np.asarray(im)
                stride = max(1, int(math.ceil(math.sqrt(a.shape[0]*a.shape[1]/MAX_PIXELS))))
                arrays.append(a[::stride, ::stride].reshape(-1, 3))
            sources.append(record)
    if not arrays:
        raise ValueError("No source images were selected.")
    pixels = np.concatenate(arrays)
    if len(pixels) > MAX_PIXELS:
        pixels = pixels[::int(math.ceil(len(pixels)/MAX_PIXELS))]
    return pixels, sources


def extract_colors(pixels, count=6, include_neutrals=False):
    if not 2 <= count <= 8:
        raise ValueError("Request 2 to 8 main colors.")
    unique, counts = np.unique(pixels, axis=0, return_counts=True)
    labs = rgb_to_lab(unique)
    keep = (labs[:, 0] > .12) & (labs[:, 0] < .97)
    if not include_neutrals:
        keep &= np.linalg.norm(labs[:, 1:], axis=1) >= .025
    retained = int(counts[keep].sum())
    unique, counts, labs = unique[keep], counts[keep], labs[keep]
    if len(unique) < 2 or retained < 8:
        raise ValueError("Too few colored pixels. Select a figure crop, use --include-neutrals for grayscale, or supply manual HEX colors.")
    # Bin nearby RGB pixels to stop JPEG/antialias fringes dominating clustering.
    bins = (unique//8) @ np.array([1024, 32, 1])
    order = np.lexsort((-counts, bins))
    sorted_bins = bins[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_bins))+1]
    representatives = order[starts]
    weights = np.add.reduceat(counts[order], starts)
    rgb = unique[representatives]
    lab = labs[representatives]
    first = int(np.argmax(weights))
    chosen = [first]
    distance = np.sum((lab-lab[first])**2, axis=1)
    for _ in range(min(count, len(rgb))-1):
        score = distance*np.sqrt(weights)
        candidate = int(np.argmax(score))
        if distance[candidate] < .035**2:
            break
        chosen.append(candidate)
        distance = np.minimum(distance, np.sum((lab-lab[candidate])**2, axis=1))
    if len(chosen) < 2:
        raise ValueError("Only one distinct hue was found. Supply a second color or a different crop.")
    centers = lab[chosen].copy()
    for _ in range(16):
        labels = np.argmin(np.sum((lab[:, None]-centers[None])**2, axis=2), axis=1)
        updated = centers.copy()
        for k in range(len(centers)):
            hit = labels == k
            if hit.any():
                updated[k] = np.average(lab[hit], axis=0, weights=weights[hit])
        if np.max(np.abs(updated-centers)) < 1e-7:
            break
        centers = updated
    labels = np.argmin(np.sum((lab[:, None]-centers[None])**2, axis=2), axis=1)
    result = []
    for k in range(len(centers)):
        hit = np.flatnonzero(labels == k)
        if not len(hit):
            continue
        # Return an observed representative, never a synthetic centroid.
        delta = np.sum((lab[hit]-centers[k])**2, axis=1)
        index = hit[np.argmin(delta)]
        result.append((to_hex(rgb[index]), int(weights[hit].sum())))
    result.sort(key=lambda x: (-x[1], x[0]))
    colors = list(dict.fromkeys(x[0] for x in result))
    coverage = [{"hex": c, "fraction_of_retained_pixels": round(w/retained, 6)} for c, w in result]
    return colors, {"sampled_pixels": len(pixels), "retained_pixels": retained,
                    "colored_fraction": round(retained/len(pixels), 6),
                    "requested_main_count": count, "actual_main_count": len(colors),
                    "include_neutrals": include_neutrals, "coverage": coverage,
                    "method": "deterministic weighted Oklab clustering; observed RGB representatives"}


def pal_text(colors):
    if not 1 <= len(colors) <= 256:
        raise ValueError("JASC PAL needs 1..256 entries.")
    return "JASC-PAL\r\n0100\r\n" + str(len(colors)) + "\r\n" + "".join(
        "%d %d %d\r\n" % hex_rgb(c) for c in colors)


def gradient_256(colors):
    return [colors[round(i*(len(colors)-1)/255)] for i in range(256)]


def theme_colors(palette):
    main = [c["hex"] for c in palette["main"]]
    accents = (main*3)[:6]
    return {"dk1": "#182533", "lt1": "#FFFFFF", "dk2": "#445465", "lt2": "#F1F4F7",
            **{f"accent{i+1}": c for i, c in enumerate(accents)}, "hlink": main[0], "folHlink": main[-1]}


def color_scheme(palette):
    colors = theme_colors(palette)
    node = ET.Element(f"{{{A}}}clrScheme", {"name": palette["title"]})
    for role, color in colors.items():
        child = ET.SubElement(node, f"{{{A}}}{role}")
        ET.SubElement(child, f"{{{A}}}srgbClr", {"val": color[1:]})
    return node


def xml_bytes(node):
    return ET.tostring(node, encoding="utf-8", xml_declaration=True)


def write_zip(path, parts):
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(parts.items()):
            # Fixed timestamps make package hashes reproducible.
            entry = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(entry, data)


def themed_xml(data, palette):
    root = ET.fromstring(data)
    elements = root.find("a:themeElements", NS)
    if elements is None:
        raise ValueError("PPT theme has no themeElements.")
    old = elements.find("a:clrScheme", NS)
    elements.remove(old)
    elements.insert(0, color_scheme(palette))
    root.set("name", palette["title"])
    return xml_bytes(root)


def theme_parts(palette):
    baseline = (ROOT/"assets/base-theme.xml").read_bytes()
    return {
        "[Content_Types].xml": b'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/theme/themeManager.xml" ContentType="application/vnd.openxmlformats-officedocument.themeManager+xml"/><Override PartName="/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/></Types>',
        "_rels/.rels": b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="theme/themeManager.xml"/></Relationships>',
        "theme/themeManager.xml": f'<a:themeManager xmlns:a="{A}"/>'.encode(),
        "theme/_rels/themeManager.xml.rels": b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme1.xml"/></Relationships>',
        "theme/theme1.xml": themed_xml(baseline, palette)
    }


def set_text(shape, text):
    nodes = shape.findall(".//a:t", NS)
    if nodes:
        nodes[0].text = text
        for node in nodes[1:]:
            node.text = ""


def set_fill(shape, color):
    props = shape.find("p:spPr", NS)
    if props is None:
        return
    for kind in ("solidFill", "gradFill", "noFill", "pattFill", "blipFill"):
        for node in props.findall(f"a:{kind}", NS):
            props.remove(node)
    fill = ET.Element(f"{{{A}}}solidFill")
    ET.SubElement(fill, f"{{{A}}}srgbClr", {"val": color[1:]})
    # Fill follows geometry and precedes the outline in CT_ShapeProperties.
    pos = next((i for i, x in enumerate(props) if x.tag in {f"{{{A}}}ln", f"{{{A}}}effectLst"}), len(props))
    props.insert(pos, fill)


def set_gradient(shape, gradient):
    props = shape.find("p:spPr", NS)
    for kind in ("solidFill", "gradFill", "noFill", "pattFill", "blipFill"):
        for node in props.findall(f"a:{kind}", NS):
            props.remove(node)
    fill = ET.Element(f"{{{A}}}gradFill", {"rotWithShape": "1"})
    stops = ET.SubElement(fill, f"{{{A}}}gsLst")
    # 17 native stops approximate the same perceptual interpolation; full 257 samples are in JSON/SVG.
    for i in range(0, 257, 16):
        stop = ET.SubElement(stops, f"{{{A}}}gs", {"pos": str(round(i/256*100000))})
        ET.SubElement(stop, f"{{{A}}}srgbClr", {"val": gradient["colors"][i][1:]})
    ET.SubElement(fill, f"{{{A}}}lin", {"ang": "0", "scaled": "1"})
    pos = next((i for i, x in enumerate(props) if x.tag in {f"{{{A}}}ln", f"{{{A}}}effectLst"}), len(props))
    props.insert(pos, fill)


def pptx_parts(palette):
    with zipfile.ZipFile(ROOT/"assets/palette-template.pptx") as z:
        parts = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
    main = [c["hex"] for c in palette["main"]]
    for name in list(parts):
        if re.fullmatch(r"ppt/theme/theme\d+.xml", name):
            parts[name] = themed_xml(parts[name], palette)
        if not re.fullmatch(r"ppt/slides/slide\d+.xml", name):
            continue
        root = ET.fromstring(parts[name])
        tree = root.find("p:cSld/p:spTree", NS)
        for shape in list(tree):
            prop = shape.find("p:nvSpPr/p:cNvPr", NS)
            if prop is None:
                continue
            tag = prop.get("name", "")
            match = re.fullmatch(r"(MAIN|HEX|RGB|TONAL|TONE_LABEL|SHADE)-(\d+)(?:-(\d+))?", tag)
            if match:
                kind, number, sub = match.groups()
                index = int(number)
                if index >= len(main):
                    tree.remove(shape)
                    continue
                c = main[index]
                if kind == "MAIN":
                    set_fill(shape, c)
                elif kind == "HEX":
                    set_text(shape, f"{index+1:02d}  {c}")
                elif kind == "RGB":
                    set_text(shape, "RGB " + " / ".join(map(str, hex_rgb(c))))
                elif kind == "TONAL":
                    set_gradient(shape, palette["gradients"][index])
                elif kind == "TONE_LABEL":
                    set_text(shape, f"{index+1:02d}  {c}")
                elif kind == "SHADE":
                    set_fill(shape, palette["gradients"][index]["colors"][round(int(sub)/6*256)])
            elif tag == "PALETTE_TITLE":
                set_text(shape, palette["title"])
            elif tag == "PALETTE_BASIS":
                set_text(shape, f"{len(main)} main colors · {palette['provenance'].get('basis', 'manual')} · sRGB")
            elif tag == "SEQUENTIAL":
                set_gradient(shape, palette["gradients"][-2])
            elif tag == "DIVERGING":
                set_gradient(shape, palette["gradients"][-1])
        parts[name] = xml_bytes(root)
    # Template preview is not a preview of this edited palette.
    thumb = "docProps/thumbnail.jpeg"
    if thumb in parts:
        parts.pop(thumb)
        for name in ["[Content_Types].xml", "_rels/.rels"]:
            root = ET.fromstring(parts[name])
            for child in list(root):
                if child.get("PartName") == "/"+thumb or child.get("Target") == thumb:
                    root.remove(child)
            parts[name] = xml_bytes(root)
    return parts


def font(size, bold=False):
    override = os.environ.get("PALETTE_FONT")
    candidates = [override] if override else []
    candidates += ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in candidates:
        if path and Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def swatch_card(palette, path):
    main = [x["hex"] for x in palette["main"]]
    width, height = 1500, 360+90*len(main)+300
    im = Image.new("RGB", (width, height), "#F9FAFC")
    d = ImageDraw.Draw(im)
    d.text((64, 38), "SCIENTIFIC PALETTE STUDIO", fill="#43556A", font=font(22, True))
    d.text((64, 82), palette["title"][:52], fill="#162A3B", font=font(42, True))
    d.text((64, 150), "Main colors / exact RGB values", fill="#43556A", font=font(25))
    cell = (width-128)/len(main)
    for i, c in enumerate(main):
        left, right = round(64+i*cell), round(64+(i+1)*cell-12)
        d.rectangle((left, 198, right, 275), fill=c)
        d.text((left, 287), c, fill="#162A3B", font=font(22, True))
    d.text((64, 337), "Tonal gradients / each main color stays at the midpoint", fill="#43556A", font=font(25))
    for i, g in enumerate(palette["gradients"][:-2]):
        y = 392+i*90
        d.text((64, y+12), main[i], fill="#162A3B", font=font(23, True))
        arr = np.array([hex_rgb(c) for c in g["colors"]], dtype=np.uint8)[None, :, :]
        strip = Image.fromarray(arr).resize((1080, 46), Image.Resampling.NEAREST)
        im.paste(strip, (285, y))
    y = 414+90*len(main)
    for offset, g in enumerate(palette["gradients"][-2:]):
        yy = y+offset*94
        d.text((64, yy), g["name"], fill="#43556A", font=font(23))
        arr = np.array([hex_rgb(c) for c in g["colors"]], dtype=np.uint8)[None, :, :]
        im.paste(Image.fromarray(arr).resize((1300, 42), Image.Resampling.NEAREST), (64, yy+36))
    d.text((64, height-45), "sRGB  |  Main colors: "+palette["provenance"].get("basis", "manual")+"  |  Gradients: derived", fill="#43556A", font=font(19))
    im.save(path)


def svg_gradient(gradient):
    stops = "".join(f'<stop offset="{i/256*100:.5f}%" stop-color="{c}"/>' for i, c in enumerate(gradient["colors"]))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="100" viewBox="0 0 1200 100"><defs><linearGradient id="g">{stops}</linearGradient></defs><rect width="1200" height="100" fill="url(#g)"/></svg>'


def export_bundle(palette, output):
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise ValueError("Output already exists. Use a new directory to preserve previous work.")
    output.mkdir(parents=True)
    for folder in ("origin", "gradients", "powerpoint"):
        (output/folder).mkdir()
    (output/"palette.json").write_text(json.dumps(palette, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    (output/"audit.json").write_text(json.dumps(palette["audit"], indent=2)+"\n", encoding="utf-8")
    main = [c["hex"] for c in palette["main"]]
    (output/"origin/main-colors.pal").write_bytes(pal_text(main).encode("ascii"))
    with (output/"colors.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "name", "position", "hex", "red", "green", "blue"])
        for i, c in enumerate(main):
            writer.writerow(["main", f"color-{i+1:02d}", i+1, c, *hex_rgb(c)])
        for g in palette["gradients"]:
            for i, c in enumerate(g["colors"]):
                writer.writerow([g["kind"], g["id"], i/256, c, *hex_rgb(c)])
    for g in palette["gradients"]:
        (output/f"origin/{g['id']}.pal").write_bytes(pal_text(gradient_256(g["colors"])).encode("ascii"))
        (output/f"gradients/{g['id']}.svg").write_text(svg_gradient(g), encoding="utf-8")
    swatch_card(palette, output/"color-card.png")
    tp = theme_parts(palette)
    write_zip(output/"powerpoint/palette.thmx", tp)
    (output/"powerpoint/theme-colors.xml").write_bytes(xml_bytes(color_scheme(palette)))
    pp = pptx_parts(palette)
    write_zip(output/"powerpoint/palette-toolkit.pptx", pp)
    payload = {"palette": palette,
               "themeParts": {n: v.decode("utf-8") for n, v in tp.items()},
               "pptxParts": {n: list(v) if not (n.endswith(".xml") or n.endswith(".rels")) else v.decode("utf-8")
                             for n, v in pp.items()}}
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = (ROOT/"assets/workbench.html").read_text(encoding="utf-8")
    (output/"palette-workbench.html").write_text(template.replace("__PALETTE_PAYLOAD__", data), encoding="utf-8")
    usage = (ROOT/"references/using-exports.md").read_text(encoding="utf-8")
    (output/"HOW-TO-USE.md").write_text(usage, encoding="utf-8")
    inventory = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(output.rglob("*")) if p.is_file()}
    (output/"manifest.json").write_text(json.dumps({"generator": VERSION, "files": inventory}, indent=2)+"\n", encoding="utf-8")
    return output


def load_palette(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0":
        raise ValueError("Unsupported palette schema; expected 1.0.")
    main = [c["hex"] for c in data["main"]]
    provenance = data.get("provenance", {"basis": "manual"}).copy()
    provenance["reexported_from_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    prior = [g.get("parent_colors", [None])[0] for g in data.get("gradients", [])[:len(main)]]
    if len(prior) == len(main) and prior != main:
        provenance["basis"] = "user-edited"
        provenance.setdefault("original_main_colors", prior)
    # Recompute every derived output so a edited main color cannot leave stale gradients.
    return build_palette(main, data.get("title", "Scientific palette"), provenance, data.get("background", "#FFFFFF"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract", help="Extract observed figure colors from local PDF/images.")
    p.add_argument("--input", nargs="+", required=True)
    p.add_argument("--pages")
    p.add_argument("--crop")
    p.add_argument("--dpi", type=int, default=180)
    p.add_argument("--count", type=int, default=6)
    p.add_argument("--include-neutrals", action="store_true")
    p.add_argument("--title", default="Paper-derived scientific palette")
    p.add_argument("--output", required=True)
    p = sub.add_parser("from-colors", help="Create a bundle from explicit main colors.")
    p.add_argument("--colors", nargs="+", required=True)
    p.add_argument("--title", default="Scientific palette")
    p.add_argument("--background", default="#FFFFFF")
    p.add_argument("--output", required=True)
    p = sub.add_parser("export", help="Rebuild all exports from an edited palette JSON.")
    p.add_argument("--palette", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("demo", help="Build an original demonstration without a source paper.")
    p.add_argument("--output", required=True)
    sub.add_parser("doctor", help="Report optional PDF tools and portable export assets.")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps({"python": sys.version.split()[0], "version": VERSION,
                  "numpy": np.__version__, "poppler": {n: bool(os.environ.get(v) or shutil.which(n)) for n, v in
                  [("pdftoppm", "PALETTE_PDFTOPPM"), ("pdfinfo", "PALETTE_PDFINFO")]},
                  "assets": {n: (ROOT/"assets"/n).is_file() for n in
                             ["palette-template.pptx", "base-theme.xml", "workbench.html"]}}, indent=2))
            return 0
        if args.command == "extract":
            pixels, sources = load_sources(args.input, args.pages, args.crop, args.dpi)
            colors, extraction = extract_colors(pixels, args.count, args.include_neutrals)
            palette = build_palette(colors, args.title, {"basis": "extracted", "sources": sources, "extraction": extraction})
        elif args.command == "from-colors":
            palette = build_palette(args.colors, args.title, {"basis": "manual"}, args.background)
        elif args.command == "export":
            palette = load_palette(args.palette)
        else:
            palette = build_palette(DEMO_COLORS, "Mineral & molecular colors", {"basis": "original demonstration", "note": "Not extracted from a paper."})
        output = export_bundle(palette, args.output)
        print(json.dumps({"output": str(output), "main_colors": len(palette["main"]),
                          "gradients": len(palette["gradients"]), "warnings": len(palette["audit"]["warnings"])}, indent=2))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
