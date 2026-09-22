#!/usr/bin/env python3
"""
build_vendor_csv.py

Writes vendor rows into a CSV formatted for QuickBooks Online's vendor
import (Name, Company, Email, Phone, Mobile, Fax, Website, Street, City,
State, ZIP, Country, Opening Balance, Date, Tax ID, Bank Account,
Bank Routing (ABA), SWIFT).

This script does NOT read PDFs or figure out who a vendor is -- it just
takes already-identified vendor data and writes a clean, QBO-ready CSV.
Fill in VENDORS below (or point --json at a JSON file with the same shape),
one dict per vendor.

Usage:
    python build_vendor_csv.py --out vendors.csv
    python build_vendor_csv.py --json my_vendors.json --out vendors.csv
"""

import argparse
import csv
import json
import sys

HEADERS = [
    "Name", "Company", "Email", "Phone", "Mobile", "Fax", "Website",
    "Street", "City", "State", "ZIP", "Country", "Opening Balance", "Date",
    "Tax ID", "Bank Account", "Bank Routing (ABA)", "SWIFT",
]

# Fill this in per project, or pass --json pointing at a file shaped like this list.
# Any missing key is written as blank.
VENDORS = [
    # {
    #     "Name": "Isaac Schell",
    #     "Company": "",
    #     "Email": "isaac.schell@gmail.com",
    #     "Phone": "",
    #     "Street": "71 Ocean Pkwy Apt 6A",
    #     "City": "Brooklyn",
    #     "State": "NY",
    #     "ZIP": "11218",
    #     "Country": "United States",
    #     "Opening Balance": 1275.00,
    #     "Date": "2026-09-18",
    #     "Tax ID": "87-4738198",
    #     "Bank Account": "8137521444",
    #     "Bank Routing (ABA)": "031207607",
    #     "SWIFT": "PNCCUS33",
    # },
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="JSON file containing a list of vendor dicts")
    parser.add_argument("--out", default="vendors.csv", help="Output CSV path")
    args = parser.parse_args()

    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            vendors = json.load(f)
    else:
        vendors = VENDORS

    if not vendors:
        print("No vendor data provided. Edit VENDORS in this script, or pass --json.",
              file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS, extrasaction="ignore")
        writer.writeheader()
        total = 0.0
        for v in vendors:
            row = {h: v.get(h, "") for h in HEADERS}
            writer.writerow(row)
            try:
                total += float(row["Opening Balance"] or 0)
            except (TypeError, ValueError):
                pass

    print(f"Wrote {len(vendors)} vendor(s) to {args.out}")
    print(f"Total Opening Balance: ${total:,.2f}")


if __name__ == "__main__":
    main()
