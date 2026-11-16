import argparse,hashlib,json,platform
from pathlib import Path
import pandas as pd
from pipeline.clean import clean_data
from pipeline.analyze import analyze
from pipeline.visualize import create_charts
ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description='Audit sales and cancellations, then build retail reports.')
    parser.add_argument('--data',type=Path,default=ROOT/'data/Online_Retail.xlsx')
    parser.add_argument('--output',type=Path,default=ROOT/'reports')
    args=parser.parse_args()
    if not args.data.is_file(): parser.error('Input missing. See data/README.md for the source and sample instructions.')
    raw=pd.read_excel(args.data) if args.data.suffix.lower()=='.xlsx' else pd.read_csv(args.data,dtype={'InvoiceNo':'string','StockCode':'string','CustomerID':'string'})
    clean,audit,rejected=clean_data(raw)
    frames=analyze(clean);args.output.mkdir(parents=True,exist_ok=True)
    for name,frame in frames.items():frame.to_csv(args.output/f'{name}.csv',index=False,float_format='%.8f')
    meta={'source_sha256':hashlib.sha256(args.data.read_bytes()).hexdigest(),'python':platform.python_version(),
          'pandas':pd.__version__,'first_timestamp':str(clean.InvoiceDate.min()),'last_timestamp':str(clean.InvoiceDate.max()),
          'currency':'GBP','rounding':'Each signed line to integer pence, ROUND_HALF_UP','audit':audit}
    (args.output/'run_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    pd.DataFrame([{'Rule':k,'Rows':v} for k,v in audit.items()]).to_csv(args.output/'cleaning_audit.csv',index=False)
    # Rejects remain local, ignored by Git; identifiers are not portfolio deliverables.
    rejected.to_csv(args.output/'excluded_rows.csv',index=False)
    create_charts(frames,meta,args.output)
    print(json.dumps(meta,indent=2));print(frames['overall_kpis'].to_string(index=False))

if __name__=='__main__':main()
