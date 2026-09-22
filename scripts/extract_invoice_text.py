#!/usr/bin/env python3
"""
extract_invoice_text.py

Pulls raw text out of every PDF in a folder (invoices, W9s, whatever) so it
can be read and turned into vendor rows -- either by a human, or by Claude
Code running as an agent over the folder.

Requires: poppler-utils (pdftotext, pdffonts, pdftoppm) on PATH.
  - Windows: install poppler and add its \bin folder to PATH
  - Mac: brew install poppler
  - Linux: apt install poppler-utils

Usage:
    python extract_invoice_text.py "C:\path\to\Invoices2026\Lookbook"
    python extract_invoice_text.py "C:\path\to\Invoices2026\Lookbook" --out extracted.json

For image-based PDFs (no embedded text layer), this script rasterizes page 1
to a .png next to the output so you (or an LLM with vision) can read it
directly -- pdftotext alone will return nothing useful for those.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def has_text_layer(pdf_path: Path) -> bool:
    """Return True if pdffonts reports at least one embedded font."""
    try:
        result = subprocess.run(
            ["pdffonts", str(pdf_path)],
            capture_output=True, text=True, timeout=30
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        # header + separator = 2 lines when there are no fonts
        return len(lines) > 2
    except FileNotFoundError:
        print("ERROR: poppler-utils not found on PATH. See script docstring.", file=sys.stderr)
        sys.exit(1)


def extract_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout


def rasterize_first_page(pdf_path: Path, out_dir: Path) -> str:
    """For image-based PDFs: render page 1 to PNG for visual/manual reading."""
    stem = pdf_path.stem
    out_prefix = out_dir / f"{stem}_page1"
    subprocess.run(
        ["pdftoppm", "-png", "-r", "150", "-f", "1", "-l", "1", str(pdf_path), str(out_prefix)],
        capture_output=True, timeout=60
    )
    candidates = list(out_dir.glob(f"{stem}_page1*.png"))
    return str(candidates[0]) if candidates else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", help="Folder of PDFs to extract")
    parser.add_argument("--out", default="extracted_text.json", help="Output JSON file")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Not a folder: {folder}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out)
    image_dir = out_path.parent / "rasterized_pages"
    image_dir.mkdir(parents=True, exist_ok=True)

    results = []
    pdfs = sorted(folder.glob("*.pdf")) + sorted(folder.glob("*.PDF"))
    for pdf in pdfs:
        entry = {"file": pdf.name, "path": str(pdf)}
        if has_text_layer(pdf):
            entry["text"] = extract_text(pdf)
            entry["needs_visual_read"] = False
        else:
            entry["text"] = ""
            entry["needs_visual_read"] = True
            entry["rasterized_image"] = rasterize_first_page(pdf, image_dir)
        results.append(entry)
        flag = "OCR/visual needed" if entry["needs_visual_read"] else "text extracted"
        print(f"  {pdf.name} -> {flag}")

    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {len(results)} entries to {out_path}")
    needs_visual = [r["file"] for r in results if r["needs_visual_read"]]
    if needs_visual:
        print(f"\n{len(needs_visual)} file(s) had no text layer and were rasterized to "
              f"{image_dir}/ for visual reading:")
        for f in needs_visual:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
