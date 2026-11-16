# Methodology and analytical limits

## Cleaning and scope

The raw workbook is unchanged. Cleaning operates on a copy and records sequential
exclusion counts in `reports/cleaning_audit.csv` and `run_metadata.json`.

1. Validate required columns and remove exact duplicate rows across the eight
   source columns. With no unique line-item ID, identical rows could conceivably
   be valid repeated entries: de-duplication is an explicit assumption, not proof
   that the source was wrong. Retain the original for sensitivity checks.
2. Trim text and normalize integer-like identifier strings. Keep identifiers as
   text and uppercase invoice and stock codes.
3. Parse timestamps and numeric fields. Exclude missing essential dimensions,
   invalid or infinite numbers, zero/fractional quantities and nonpositive prices.
4. Require negative quantity on cancellation invoices and positive quantity on
   other invoices. Quarantine conflicting signs and negative non-C records rather
   than guessing whether they are returns or stock adjustments.
5. Retain missing CustomerID and Description when financial fields are usable.
   Exclude missing CustomerID only from customer analysis. Description is not the
   product key.

The exclusion audit is sequential: each row is counted under its first applicable
rule. Local `excluded_rows.csv` retains rejected records for inspection but is
excluded from the publication package.

## Currency and calculations

Each line value is Quantity x UnitPrice, rounded to integer pence using decimal
ROUND_HALF_UP. This makes aggregate arithmetic exact and the rounding policy
explicit. It is an analytical convention; the source does not establish the
retailer's accounting rounding rules.

- **Gross recorded sales:** sum of positive line values.
- **Recorded cancellation value:** absolute sum of negative C-invoice line values.
- **Net recorded value:** gross minus cancellation value.
- **Cancellation-value percentage:** cancellation value / gross x 100. This is
  not a product return rate; quantities and individual sales are not matched.
- **Average gross invoice:** gross / distinct positive-sales InvoiceNo values.
  It is not net value divided by both sales and credit-note counts.
- **Repeat purchaser:** an identified customer with at least two distinct
  positive-sales invoices during the observed window. Multiple lines within one
  invoice are not repeat purchases. This is not a cohort retention measure.
- **Customer coverage:** positive-sales value carrying a CustomerID / gross.
  Customer findings apply to this identified subset, not the anonymous portion.

All exported money columns end in `Pence`. Divide by 100 for GBP. Chart labels
and case-study figures are in GBP; source percentages are retained at higher
precision in the CSVs.

## Product and customer segmentation

Merchandise uses the analyst-defined StockCode pattern: five digits followed by
zero or more letters. This accommodates common product codes but is not a
verified universal product dictionary. Codes outside that pattern (for example
POST and manual/fee codes) remain in overall, monthly and country totals and are
reported separately in `nonstandard_codes.csv`; they are excluded from the top
merchandise-products chart. Such codes can include legitimate items, not only fees.

Products are grouped by code; the most frequent nonmissing description is used
as a label, with alphabetical tie-breaking. Descriptions do not create separate
products. Identified customers with cancellations but no positive-sales invoice
in the window form a separate cancellation-only segment. Their purchases may
have occurred outside the extract.

## Interpretation

This is historical UK retailer data, including wholesalers. It does not represent
today's market or all online businesses. December 2011 is partial, ending on the
9th; its month-over-month comparison is suppressed. No growth comparison is
made across nonconsecutive months or from a zero-valued prior month.

Recorded net value is not audited revenue, cash received, margin, profit or a
tax calculation. The extract does not establish all accounting adjustments, cost
of goods, tax treatment or links between original sales and cancellations.
Unusual large records are not removed solely because they are large. Recommendations
are investigation priorities, not proven savings or causal effects.

## Verification

Unit tests cover actual nulls, invalid numbers, signs, duplicates, currency
rounding, code-based products, anonymous sales, invoice-level repeat purchases,
special codes and partial periods. `tools/verify_exports.py` uses openpyxl and
Python's Decimal/collections modules to independently recompute and compare all
six analytical tables. It imports neither pandas nor the production pipeline.
Money and counts must match exactly; percentage tolerance is 1e-7.
