---
name: Guardian NY DBL PFL Filing
description: Fill out Guardian's quarterly New York State Disability Benefits (NY DBL) and Paid Family Leave (NY PFL) premium report from a QuickBooks payroll report. Use this whenever the user shares a Guardian premium report / statement PDF and a payroll spreadsheet, asks to "do the Guardian filing," "file NY DBL and PFL," "fill out the disability/paid family leave premium report," or wants to repeat this quarterly process. Also trigger if the user mentions Guardian policy 00903942 or the NYGQSEP form.
---

# Guardian NY DBL + PFL Premium Filing

Fills in Guardian's "NY State Mandated DISABILITY BENEFIT and PAID FAMILY
LEAVE — PREMIUM REPORT - QUARTERLY" (form code NYGQSEP, bottom of page 1)
for J Cameron Brands LLC, policy 00903942-0000, from a QuickBooks payroll
report export.

The work is done by `scripts/fill_guardian_ny_dbl_pfl.py`. Don't recreate
its logic inline; call it as-is.

## Inputs

1. **The Guardian statement PDF** for the billing period. Prefer Guardian's
   **blank statement**, which is a fillable PDF form. The script puts the
   values into its fields, so they can still be edited in Acrobat or
   Preview afterward. It matches fields by box position, because Guardian's
   field names aren't reliable (the female premium field is named "DBL
   Premium Due Male ..."). A statement that was filled in before and
   flattened also works: the old values are stripped and the new ones are
   drawn as text. The script reads everything that changes each quarter
   from the PDF itself:
   - period begin/end dates and the payment due date
   - DBL rates per employee per month (male and female)
   - the DBL minimum quarterly premium
   - the DBL wage cap per employee per quarter
   - the PFL wage cap per employee per year
   - the PFL rate
2. **The QuickBooks payroll report (.xlsx).** It has one row per employee,
   **already summed across all pay runs in the billing period**, plus an
   "All" totals row that the script skips. The script uses these columns:
   - `Employee`
   - `Employee gross pay`: the wages for the period. Use this and not net
     pay or employer cost. A past filing went wrong by using the wrong pay
     column.
   - `Start date`: **this is the employee's HIRE DATE**, not a pay-period
     start. It drives every headcount on the form.
   - `Identified gender` (falls back to `Legal gender`)
   - A year-to-date gross pay column (optional). Any header containing
     "year to date" or "YTD" plus "gross" is picked up. It must be YTD as of
     the period end, so it includes this period's pay. The script uses it to
     apply the PFL annual cap. If the column is missing, the script warns and
     caps period wages only. That's fine for now, since no one is near the
     cap yet.

Ignore the `Snapshot Date` column.

## Calculation rules (what the script does)

- **Monthly headcount (NY DBL):** the form shows three months. Months that
  end before the period begins are pre-printed N/A on the form and left
  blank. For every other month, an employee counts if their hire date is
  on or before the last day of that month. Males and females are counted
  separately.
- **DBL premium:**
  - Line A is (sum of monthly male counts × male rate) + (sum of monthly
    female counts × female rate).
  - Line B is the greater of line A and the minimum quarterly premium.
- **DBL statutory payroll** (the box at the top): each employee's period
  gross pay, capped at the quarterly DBL cap ($1,750 on the current form),
  summed.
- **PFL employee data:** employees hired on or before the period end,
  counted by gender.
- **Line C:** covered wages, which is period gross pay limited by the room
  left under the annual PFL cap.
- **Line E:** C × PFL rate.
- **Line F:** B + E.

## Process

1. **Save both files** to a scratch folder. They contain payroll data, so
   don't commit them to the repo.
2. **Run the script:**

   ```bash
   python3 scripts/fill_guardian_ny_dbl_pfl.py STATEMENT.pdf PAYROLL.xlsx \
       --out Guardian_NY_DBL_PFL_<period>.pdf \
       --preparer "Larry Leibowitz" --email "leibowitzle@gmail.com" \
       --preview preview.png
   ```

   It prints the rates it parsed, how many form fields it filled (18 on
   the current blank form, 0 on a flattened one), each employee's gender,
   hire date and wages, the monthly headcounts, and every line from A
   through F.
3. **Open `preview.png` with the Read tool** and check that every value sits
   in its box and nothing from an earlier fill is still showing.
4. **Report to the user:**
   - the total due (line F) and the payment due date
   - the monthly headcount table, and lines A/B, C, E and F
   - anything the script flagged (missing YTD column, cap reached, employees
     hired after the period)
   - anything that looks off in the data, for example an employee with zero
     wages who was counted in the headcount
5. **Send the filled PDF** to the user. It's submitted at guardianlife.com
   (Billing → Make a Payment), or mailed with a check to Guardian – State
   Paid Leave, PO Box 824418, Philadelphia, PA 19182-4418, with the 12-digit
   policy number on the memo line.

## Prerequisites

Python packages: `pypdf`, `openpyxl`, `reportlab`, plus `pypdfium2` for
`--preview`. If pypdf fails with `No module named '_cffi_backend'`, also
install `cffi`:

```bash
pip install pypdf openpyxl reportlab pypdfium2 cffi
```

## If the form layout changes

The entry-box positions (`POS`, `MONTH_COL_X`, `M_ROW_Y`, `F_ROW_Y` at the
top of the script) match form NYGQSEP. If Guardian changes the form:
1. Render page 1 and compare it against the preview.
2. Re-measure the box positions. The flattened fill layer in a previously
   filled statement (a form XObject with `/Tx BMC` children) gives exact
   coordinates.
3. On a fillable form, `pypdf.PdfReader(pdf).pages[0]['/Annots']` gives
   each widget's `/Rect`. Its lower-left corner is what `POS` must match
   (within 3pt).
4. If the script can't parse a rate or date, it exits and names the
   missing item. Update that regex in `parse_statement`.
5. The current form has fields for months 2 and 3 only, because month 1
   (JUL) is pre-printed N/A. On a full-quarter form, check that the
   month-1 box sits at `MONTH_COL_X[0]`. If no field matches, the value is
   drawn as text there instead.
