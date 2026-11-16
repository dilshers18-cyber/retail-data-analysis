"""Generate the README, standalone visual case study and portfolio cover."""
from pathlib import Path
import json,base64
import pandas as pd
from PIL import Image,ImageDraw,ImageFont
from matplotlib.font_manager import findfont,FontProperties
ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'reports';docs=ROOT/'docs'
    m=json.loads((out/'run_metadata.json').read_text());a=m['audit']
    v=json.loads((out/'verification.json').read_text())
    k=pd.read_csv(out/'overall_kpis.csv').iloc[0]
    product=pd.read_csv(out/'product_performance.csv',dtype={'StockCode':str}).iloc[0]
    def gbp(p):return f'£{p/100:,.2f}'
    findings=[f'Recorded cancellations equal {k.CancellationValuePct:.2f}% of gross value.',
              f'{product.Description} ({product.StockCode}) leads merchandise products by net value: {gbp(product.NetPence)}.',
              f'{int(k.RepeatPurchasingCustomers):,} of {int(k.IdentifiedPurchasingCustomers):,} identified purchasing customers have at least two positive-sales invoices. Customer IDs cover {k.IdentifiedGrossCoveragePct:.2f}% of gross value.']
    readme=f'''# Retail Sales and Cancellation Analysis

A reproducible Python portfolio project that turns invoice lines into clear sales,
cancellation, product and customer reports.

![Portfolio overview](reports/portfolio_cover.png)

## Business question

How much recorded sales value remains after cancellations, which products and
markets contribute most, and how do purchasing patterns vary over the observed
period? The deliverable is an auditable management report, not an accounting
statement or predictive model.

## Verified results

| Metric | Result |
| --- | ---: |
| Source invoice lines | {a['raw_rows']:,} |
| Retained invoice lines | {a['retained_rows']:,} |
| Gross recorded sales | {gbp(k.GrossPence)} |
| Recorded cancellation value | {gbp(k.CancellationPence)} |
| Net recorded value | {gbp(k.NetPence)} |
| Cancellation value / gross | {k.CancellationValuePct:.2f}% |
| Positive-sales invoices | {k.SalesInvoices:,.0f} |
| Average gross invoice | £{k.AverageGrossInvoiceGBP:,.2f} |
| Identified purchasing customers | {k.IdentifiedPurchasingCustomers:,.0f} |
| Repeat share among identified purchasers | {k.RepeatCustomerPct:.2f}% |

Window: **1 December 2010-9 December 2011**. December 2011 is partial.
Overall values include nonstandard stock codes, exported separately. Net recorded
value is gross less recorded cancellations; it is not profit or audited recognized
revenue. Cancellations are not matched to original invoices.

## Findings

'''+''.join('- '+f+'\n' for f in findings)+f'''
![Monthly performance](reports/02_monthly_performance.png)

## Improvements over the original coursework

- Preserve and classify cancellations instead of deleting negative quantities.
- Separate gross, cancellation and net values with exact integer-pence arithmetic.
- Keep anonymous sales in totals while scoping customer metrics to identified records.
- Group products by StockCode, with a consistent description chosen for display.
- Report nonstandard codes separately and flag incomplete boundary months.
- Add meaningful tests, a sequential audit and independent raw-data verification.

## Run locally

Use Python 3.13 with the tested packages in `requirements.txt`.

```bash
python -m venv .venv
```

Activate on Windows PowerShell: `.venv\\Scripts\\Activate.ps1`.
On macOS/Linux: `source .venv/bin/activate`.

```bash
python -m pip install -r requirements.txt
python main.py
python -m pytest -q
python tools/verify_exports.py
python tools/build_portfolio.py
```

The full workbook is retained in the local working copy but excluded from Git
and the publication ZIP. Download it from the [UCI dataset page](https://archive.ics.uci.edu/dataset/352/online+retail)
and save it as `data/Online_Retail.xlsx` to reproduce the published results.
The included sample is a demonstration, not a representative dataset:

```bash
python main.py --data data/sample.csv --output sample_reports
```

Use the separate output directory so the full-data report remains intact.

## Files

| Location | Purpose |
| --- | --- |
| `main.py` | Load, clean, analyze and export |
| `pipeline/clean.py` | Audited data validation and currency rules |
| `pipeline/analyze.py` | Six analytical tables |
| `pipeline/visualize.py` | Five charts |
| `tests/` | Data quality and metric contract tests |
| `tools/verify_exports.py` | Independent workbook-to-report calculations |
| `reports/` | Tables, charts, audit, metadata and cover |
| `docs/Case_Study.html` | Standalone case study with embedded images |
| `docs/UPWORK_LISTING.txt` | Portfolio description and suggested attachments |

## Validation and limitations

20 automated tests passed. An independent openpyxl/Decimal calculation checked
all six analytical tables and {v['numeric_checks']:,} numeric values. Money and counts
match exactly; rate tolerance is 1e-7. See [verification](reports/verification.json).

Exact duplicate removal is an assumption: no unique line ID is available.
Nonpositive-price rows are excluded from financial reporting. Repeat purchases
are not retention; cancellation-value share is not a physical return rate.
Only historical associations are shown. No commercial savings are claimed.
Read [methodology](docs/METHODOLOGY.md) and [data notes](data/README.md).

## Attribution

Original coursework supplied by Dilsher Singh; this edition includes AI-assisted
refactoring, validation and presentation. Credit any original collaborators and
describe personal contributions accurately before publication. No new code
licence has been assigned; confirm ownership before selecting one.

Dataset: Chen, D. (2015). *Online Retail*. UCI Machine Learning Repository.
https://doi.org/10.24432/C5BW33. Dataset licence: CC BY 4.0. The sample and derived
reports are adaptations of this data.
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    charts=[('01_sales_and_cancellations.png','Sales and cancellations','Gross value and cancellations remain visible.'),
            ('02_monthly_performance.png','Monthly performance','December 2011 ends on the 9th. Do not interpret it as a full-month decline.'),
            ('03_top_products.png','Products that contribute most','Group by product code; descriptions are display labels.'),
            ('04_international_markets.png','International markets','UK excluded from this chart for readability, retained in results.'),
            ('05_customer_segments.png','Purchase frequency','Repeat means two or more distinct positive-sales invoices in the observed window.')]
    sections=''
    for file,title,note in charts:
        data=base64.b64encode((out/file).read_bytes()).decode()
        sections+=f'<section><h2>{title}</h2><p>{note}</p><img alt="{title}" src="data:image/png;base64,{data}"></section>'
    html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Retail Analysis | Dilsher Singh</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#eff4f7;color:#13243a;font:16px/1.65 system-ui,sans-serif}}main{{max-width:1080px;margin:32px auto}}header{{background:#13243a;color:white;padding:54px;border-radius:18px}}.eyebrow{{font-size:13px;letter-spacing:2px;color:#7dd3fc}}h1{{font-size:46px;line-height:1.12;margin:20px 0}}h2{{font-size:26px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:24px 0}}.card{{background:white;padding:25px;border-radius:12px;border-top:4px solid #0f766e}}.number{{font-size:32px;color:#0f766e;font-weight:750}}section{{background:white;border-radius:14px;padding:34px;margin:22px 0}}img{{width:100%;height:auto}}li{{margin:10px 0}}footer{{padding:24px;color:#526178;font-size:13px}}a{{color:#2563eb}}@media(max-width:650px){{main{{margin:12px}}header,section{{padding:24px}}h1{{font-size:34px}}.grid{{grid-template-columns:1fr}}}}@media print{{body{{background:white}}main{{margin:0}}section{{break-inside:avoid}}}}</style>
<main><header><div class="eyebrow">DILSHER SINGH / DATA ANALYSIS PORTFOLIO</div><h1>A clearer view<br>of retail performance.</h1><p>Python cleaning, cancellation-aware reporting and customer analysis.</p><p>Historical UCI Online Retail data / December 2010-December 2011</p></header>
<div class="grid"><div class="card"><div class="number">£{k.GrossPence/1e8:.2f}m</div>gross recorded sales</div><div class="card"><div class="number">£{k.CancellationPence/1e8:.2f}m</div>recorded cancellations</div><div class="card"><div class="number">£{k.NetPence/1e8:.2f}m</div>net recorded value</div></div>
<section><h2>The problem</h2><p>Deleting negative quantities hides cancellations. Inconsistent descriptions split product totals. Dropping missing customer IDs can remove valid sales.</p><h2>The work</h2><p>Processed {a['raw_rows']:,} invoice lines, audited {a['exact_duplicate_rows_removed']:,} exact-duplicate removals and excluded {a['nonpositive_price_removed']:,} nonpositive-price rows. Retained {a['retained_rows']:,} lines and separated sales from C-invoice cancellations.</p><h2>What the results show</h2><ul>{''.join('<li>'+f+'</li>' for f in findings)}</ul></section>
{sections}
<section><h2>Suggested investigation priorities</h2><ul><li>Review large cancellation invoices and their original transactions before attributing the cause to stock or fulfilment problems.</li><li>Combine the top-product results with margin, inventory and lead-time data before changing stock levels.</li><li>Improve customer identification coverage before using repeat-purchase patterns to guide customer strategy.</li></ul><p>These are investigation priorities, not measured business improvements.</p></section>
<section><h2>Quality and scope</h2><p>20 tests passed. An independent workbook calculation verified six analytical tables and {v['numeric_checks']:,} numeric values without pandas or production-code imports.</p><p>Historical data include wholesalers. Exact de-duplication is an assumption. Cancellations are not matched to original sales. Net recorded value includes nonstandard codes and is not accounting revenue, cash or profit. Repeat purchasing is not retention. December 2011 is partial.</p><p>Deliverables: six CSV tables, five charts, audit records and reproducible Python code.</p></section>
<footer>Academic / personal example. Original coursework supplied by Dilsher Singh; AI-assisted refactoring and review. No paid client engagement or commercial savings claimed.<br>Dataset: Chen (2015), <a href="https://doi.org/10.24432/C5BW33">UCI Online Retail</a>, CC BY 4.0.</footer></main></html>'''
    (docs/'Case_Study.html').write_text(html,encoding='utf-8')
    canvas=Image.new('RGB',(1600,1000),'#eff4f7');draw=ImageDraw.Draw(canvas)
    def font(size,bold=False):return ImageFont.truetype(findfont(FontProperties(family='DejaVu Sans',weight='bold' if bold else 'normal')),size)
    draw.rectangle((0,0,1600,330),fill='#13243a')
    draw.text((64,48),'DILSHER SINGH / DATA ANALYSIS PORTFOLIO',font=font(23),fill='#7dd3fc')
    draw.text((60,112),'Retail Sales & Cancellations',font=font(58,True),fill='white')
    draw.text((65,210),'Python cleaning. Clear metrics. Verifiable reporting.',font=font(29),fill='#dbeafe')
    draw.text((65,270),'UCI Online Retail | 2010-2011 historical data',font=font(23),fill='white')
    for x,value,label in [(60,f'£{k.GrossPence/1e8:.2f}m','gross recorded sales'),(570,f'£{k.CancellationPence/1e8:.2f}m','recorded cancellations'),(1080,f'£{k.NetPence/1e8:.2f}m','net recorded value')]:
        draw.rounded_rectangle((x,365,x+455,520),radius=16,fill='white');draw.text((x+24,386),value,font=font(43,True),fill='#0f766e');draw.text((x+24,460),label,font=font(22),fill='#334155')
    chart=Image.open(out/'02_monthly_performance.png').convert('RGB');chart.thumbnail((920,440));canvas.paste(chart,(30,550))
    draw.text((1000,590),'AUDITABLE ANALYSIS',font=font(23,True),fill='#13243a')
    for y,line in [(650,'6 independently checked tables'),(700,'5 presentation-ready charts'),(750,'20 automated tests passed'),(800,'Sales + products + customers')]:draw.text((1000,y),line,font=font(21),fill='#334155')
    draw.text((1000,895),'Public-data portfolio example.',font=font(19),fill='#526178')
    draw.text((1000,930),'Net value is not profit.',font=font(19),fill='#526178')
    canvas.save(out/'portfolio_cover.png')
    print('Created README, standalone case study and portfolio cover.')

if __name__=='__main__':main()
