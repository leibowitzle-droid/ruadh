---
name: Create Quickbooks Vendor
description: Turn a supplier/vendor PDF invoice (e.g. a foreign proforma invoice, purchase invoice, or bill) into a QuickBooks Online vendor-import CSV. Use this whenever the user shares one or more vendor/supplier PDFs and wants them turned into QuickBooks vendors, wants a "vendor CSV," wants to import a new supplier into QuickBooks, or asks to repeat the "create quickbooks vendor" / "pdf to quickbooks csv" process. Also trigger if the user mentions extracting vendor bank/tax details from an invoice PDF for bookkeeping purposes, even without saying "QuickBooks" explicitly.
---

# Create QuickBooks Vendor

Turns one or more vendor/supplier invoice PDFs into a CSV ready for QuickBooks
Online's vendor import (Settings gear icon -> Import Data -> Vendors).

The two scripts this skill drives already exist in `scripts/`:

- `scripts/extract_invoice_text.py` — pulls the text layer out of every PDF in
  a folder into a JSON file. For scanned PDFs with no text layer, it instead
  rasterizes page 1 to a PNG so it can be read visually.
- `scripts/build_vendor_csv.py` — takes a JSON list of already-identified
  vendor dicts and writes the QBO vendor-import CSV. It does no PDF reading or
  judgment of its own — that's this skill's job.

Don't recreate either script's logic inline; call them as-is.

## Prerequisites

`pdftotext`, `pdffonts`, and `pdftoppm` (poppler-utils) must be on PATH. If
`extract_invoice_text.py` fails with a "not found" error, install with:

```bash
apt-get update && apt-get install -y poppler-utils
```

## Process

1. **Get the PDF(s).** Put every invoice to process into one folder (a
   scratch/temp directory is fine — they don't need to live in the repo).

2. **Extract text.**

   ```bash
   python3 scripts/extract_invoice_text.py <folder-of-pdfs> --out extracted.json
   ```

   Read the resulting JSON. For any entry with `"needs_visual_read": true`,
   open the rasterized PNG (`rasterized_pages/<name>_page1-1.png` next to the
   output) with the Read tool and read the invoice visually instead — the
   text layer is empty for those.

3. **Identify the vendor, per invoice.** Read the extracted text (or image)
   like a human bookkeeper would. The "vendor" is whoever is *issuing/selling*
   on the invoice — not the customer receiving it. Watch for company
   letterheads/logos that only render as an image even when the rest of the
   page has a text layer (as with an Italian mill's PONTOGLIO S.P.A. logo) —
   rasterize page 1 and eyeball it if the vendor's actual name isn't obviously
   present in the extracted text.

   Pull out, when present:
   - Legal company name (goes in both `Name` and `Company`)
   - Email, phone
   - Full address: street, city, state/province, ZIP/postal code, country
   - Tax ID (VAT number, Partita IVA, EIN, etc.)
   - Bank payment details: account number or IBAN goes in `Bank Account`; a US
     ABA routing number goes in `Bank Routing (ABA)`; an international SWIFT/BIC
     code goes in `SWIFT`. If several banks are listed as valid options, pick
     one (the first listed is a reasonable default) rather than leaving it
     blank — note in your summary to the user that alternates exist.
   - An `Opening Balance` and `Date`, if the invoice represents an amount
     owed (e.g. an unpaid proforma or bill). Use the invoice total and its
     date. Skip these fields if the invoice doesn't represent a balance due
     (e.g. it's already paid, or it's just a spec sheet).

   Leave any field you can't find blank rather than guessing — `build_vendor_csv.py`
   writes missing keys as empty cells.

4. **Write the vendor JSON.** One dict per vendor, matching this exact shape
   (all keys optional except you should try to fill `Name`):

   ```json
   [
     {
       "Name": "...", "Company": "...", "Email": "...", "Phone": "...",
       "Mobile": "", "Fax": "", "Website": "",
       "Street": "...", "City": "...", "State": "...", "ZIP": "...", "Country": "...",
       "Opening Balance": 0.00, "Date": "YYYY-MM-DD",
       "Tax ID": "...", "Bank Account": "...", "Bank Routing (ABA)": "", "SWIFT": "..."
     }
   ]
   ```

5. **Build the CSV.**

   ```bash
   python3 scripts/build_vendor_csv.py --json vendors.json --out vendors.csv
   ```

6. **Deliver and flag caveats.** Send the CSV to the user. Always call out:
   - **Foreign currency amounts.** QuickBooks Online's `Opening Balance`
     column has no currency label — it's read in whatever currency the
     vendor/company is set to. If the invoice was in EUR (or any non-home
     currency), tell the user to set the vendor up as multi-currency in QBO
     *before* importing, or the number will be misread as their home currency.
   - **Fields you left blank** because the invoice didn't have the info
     (missing tax ID, no bank details, etc.) — these need manual follow-up
     before import.
   - **Multiple bank accounts** on the invoice, if you had to pick one.
   - Any invoice that needed a visual/rasterized read rather than clean text
     extraction, in case something got misread.

## Notes

- This is a judgment-heavy extraction task, not a pure script pipeline —
  that's why steps 3 and 6 are done by reading the invoice yourself rather
  than by a script. Don't try to fully automate vendor identification; a
  misread bank account or tax ID is expensive to get wrong.
- Multiple invoices for the same vendor across separate PDFs can go into one
  `vendors.json` as separate entries, or be merged into one vendor entry if
  the user wants a single opening balance — ask if it's ambiguous.
