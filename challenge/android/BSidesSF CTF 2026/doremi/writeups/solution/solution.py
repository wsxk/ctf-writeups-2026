#!/usr/bin/env python3
"""
AI generated solution 

doremi_extract_combine_to_svg.py

End-to-end pipeline in ONE Python script:

1) Run apktool (jar) to decode doremi.apk
2) Locate and copy these VectorDrawable XMLs:
     res/**/aria.xml, tempo.xml, sonnet.xml, lyra.xml, cadence.xml
3) Combine them into ONE VectorDrawable XML (combined.xml)
4) Convert that combined VectorDrawable -> SVG using `npx vector-drawable-svg`
   (because Inkscape can't import VectorDrawable XML on macOS in practice)

Requirements:
- Java (to run apktool jar)
- apktool_2.12.1.jar present (or specify --apktool-jar)
- Node + npx (install via: brew install node)
- Internet not required after first npx run; it caches packages.

Usage:
  python3 doremi_extract_combine_to_svg.py \
    --apk ../distfiles/doremi.apk \
    --apktool-jar apktool_2.12.1.jar \
    --workdir ./work \
    --out-svg combined.svg

Outputs:
- work/vectors/aria.xml ... cadence.xml (copied from decoded APK)
- work/combined.xml
- combined.svg (or chosen output path)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path

ANDROID_NS = "http://schemas.android.com/apk/res/android"
AAPT_NS = "http://schemas.android.com/aapt"

ET.register_namespace("android", ANDROID_NS)
ET.register_namespace("aapt", AAPT_NS)


NAMES = ["aria", "tempo", "sonnet", "lyra", "cadence"]


def localname(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def qname(ns: str, name: str) -> str:
    return f"{{{ns}}}{name}"


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    try:
        subprocess.run(cmd, check=True, cwd=str(cwd) if cwd else None)
    except FileNotFoundError:
        raise SystemExit(f"Command not found: {cmd[0]}")
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"Command failed ({' '.join(cmd)}): exit {e.returncode}")


def decode_apk(apk: Path, apktool_jar: Path, decoded_dir: Path) -> None:
    if decoded_dir.exists():
        shutil.rmtree(decoded_dir)
    decoded_dir.parent.mkdir(parents=True, exist_ok=True)

    # java -jar apktool_2.12.1.jar d doremi.apk -o decoded
    cmd = ["java", "-jar", str(apktool_jar), "d", str(apk), "-o", str(decoded_dir)]
    run(cmd)


def find_resource_xml(decoded_dir: Path, name: str) -> Path:
    # Search under decoded_dir/res/** for name.xml; return first match
    res_dir = decoded_dir / "res"
    if not res_dir.exists():
        raise SystemExit(f"Decoded APK missing res/ directory: {res_dir}")

    hits = sorted(res_dir.rglob(f"{name}.xml"))
    if not hits:
        raise SystemExit(f"Could not find {name}.xml under {res_dir}")
    return hits[0]


def copy_vectors(decoded_dir: Path, vectors_dir: Path) -> dict[str, Path]:
    vectors_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for n in NAMES:
        src = find_resource_xml(decoded_dir, n)
        dst = vectors_dir / f"{n}.xml"
        shutil.copy2(src, dst)
        out[n] = dst
        print(f"✔ extracted {n}.xml  <-  {src}")
    return out


def parse_vector(path: Path) -> ET.Element:
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise SystemExit(f"XML parse error in {path}: {e}") from e
    root = tree.getroot()
    if localname(root.tag) != "vector":
        raise SystemExit(f"{path} root is <{localname(root.tag)}>, expected <vector>.")
    return root


def prefix_group_names(elem: ET.Element, prefix: str) -> None:
    """
    Prefix android:name on <group> elements to reduce collisions when combining.
    """
    if localname(elem.tag) == "group":
        name_attr = qname(ANDROID_NS, "name")
        if name_attr in elem.attrib:
            elem.attrib[name_attr] = f"{prefix}_{elem.attrib[name_attr]}"
    for child in list(elem):
        prefix_group_names(child, prefix)


def combine_vectors_to_xml(xml_paths: dict[str, Path], combined_xml: Path) -> None:
    # Use aria.xml as base root so width/height/viewport remain consistent.
    base_name = "aria"
    base_root = parse_vector(xml_paths[base_name])

    for n in NAMES:
        if n == base_name:
            continue
        src_root = parse_vector(xml_paths[n])
        for child in list(src_root):
            child_copy = deepcopy(child)
            prefix_group_names(child_copy, n)
            base_root.append(child_copy)

    tree = ET.ElementTree(base_root)
    combined_xml.parent.mkdir(parents=True, exist_ok=True)
    tree.write(combined_xml, encoding="utf-8", xml_declaration=True)
    print(f"✔ wrote combined VectorDrawable XML: {combined_xml}")


def convert_vectordrawable_to_svg(combined_xml: Path, out_svg: Path) -> None:
    # npx --yes vector-drawable-svg combined.xml combined.svg
    cmd = ["npx", "--yes", "vector-drawable-svg", str(combined_xml), str(out_svg)]
    run(cmd)
    print(f"✔ wrote SVG: {out_svg}")


def add_svg_background(svg_path: Path, color: str = "#8DC63F") -> None:
    """
    Inserts a background rectangle as the first drawable element in an SVG.
    """
    SVG_NS = "http://www.w3.org/2000/svg"
    ET.register_namespace("", SVG_NS)

    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Create background rect
    rect = ET.Element(f"{{{SVG_NS}}}rect", {
        "x": "0",
        "y": "0",
        "width": "100%",
        "height": "100%",
        "fill": color,
    })

    # Insert as the very first element (behind everything)
    root.insert(0, rect)

    tree.write(svg_path, encoding="utf-8", xml_declaration=True)
    print(f"✔ added background {color} to {svg_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apk", default="../distfiles/doremi.apk", type=Path, help="Path to doremi.apk")
    ap.add_argument("--apktool-jar", default="apktool_2.12.1.jar", type=Path, help="Path to apktool jar")
    ap.add_argument("--workdir", default="./work", type=Path, help="Working directory")
    ap.add_argument("--out-svg", default="combined.svg", type=Path, help="Output SVG path")
    ap.add_argument("--keep-decoded", action="store_true", help="Do not delete decoded directory between runs")
    args = ap.parse_args()

    apk = args.apk.resolve()
    apktool_jar = args.apktool_jar.resolve()
    workdir = args.workdir.resolve()

    if not apk.exists():
        raise SystemExit(f"Missing APK: {apk}")
    if not apktool_jar.exists():
        raise SystemExit(f"Missing apktool jar: {apktool_jar}")

    decoded_dir = workdir / "decoded"
    vectors_dir = workdir / "vectors"
    combined_xml = workdir / "combined.xml"
    out_svg = args.out_svg.resolve()

    # Decode
    if args.keep_decoded and decoded_dir.exists():
        print(f"[*] Using existing decoded dir: {decoded_dir}")
    else:
        print(f"[*] Decoding APK -> {decoded_dir}")
        decode_apk(apk, apktool_jar, decoded_dir)

    # Extract
    print("[*] Extracting VectorDrawable XMLs")
    xml_paths = copy_vectors(decoded_dir, vectors_dir)

    # Combine -> combined.xml
    print("[*] Combining vectors -> combined.xml")
    combine_vectors_to_xml(xml_paths, combined_xml)

    # Convert -> combined.svg
    print("[*] Converting combined.xml -> SVG")
    convert_vectordrawable_to_svg(combined_xml, out_svg)
    add_svg_background(out_svg, "#8DC63F")


if __name__ == "__main__":
    main()
