# Source data

Chen, D. (2015). **Online Retail** [Dataset]. UCI Machine Learning Repository.
DOI: https://doi.org/10.24432/C5BW33

- Dataset and download: https://archive.ics.uci.edu/dataset/352/online+retail
- Dataset licence: Creative Commons Attribution 4.0 International (CC BY 4.0).
- Original filename: `Online Retail.xlsx`; saved locally as `Online_Retail.xlsx`.
- 541,909 invoice-line records, 1 December 2010 through 9 December 2011.
- Units: UnitPrice in pounds sterling (GBP); Quantity in units.
- An InvoiceNo beginning with C identifies a cancellation in the source documentation.

The local workbook was supplied with the original coursework. Its hash is recorded
in `reports/run_metadata.json`. The data have not been re-downloaded to prove an
exact byte match with the current UCI download.

Place the original workbook at `data/Online_Retail.xlsx` for full reproduction.
It is retained in the local working project but excluded from the publication ZIP
and Git tracking. Download it from the UCI page above if required.

`sample.csv` is a deterministic reservoir sample of 100 raw rows per observed
month, seed 42. It is for exercising the pipeline only; it does not preserve full
invoices, customer histories or matched cancellations and must not be used to
reproduce full-data KPIs. Attribution and the source licence apply to this sample.

```bash
python main.py --data data/sample.csv --output sample_reports
```

| Field | Use |
| --- | --- |
| InvoiceNo | Count distinct positive-sales invoices; C prefix identifies cancellations |
| StockCode | Product aggregation key; preserve as text |
| Description | Display label only; most frequent nonmissing label per code |
| Quantity | Signed integer units |
| InvoiceDate | Transaction timestamp and month |
| UnitPrice | GBP price per unit |
| CustomerID | Anonymous customer identifier; optional for sales totals |
| Country | Country as supplied; no geographic enrichment |
