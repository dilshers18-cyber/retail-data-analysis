"""Independently verify report tables from the workbook, without production imports or pandas."""
import csv,json,math,random
from collections import Counter,defaultdict
from datetime import datetime
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
from openpyxl import load_workbook
import re

ROOT=Path(__file__).resolve().parents[1]

def main():
    wb=load_workbook(ROOT/'data/Online_Retail.xlsx',read_only=True,data_only=True)
    rows=wb.active.iter_rows(values_only=True);headers=next(rows)
    seen=set();raw_count=0;retained=0;invoices=set();customer_invoices=defaultdict(set)
    totals=[0,0,0,0];groups={name:defaultdict(lambda:[0,0,0,0]) for name in ['monthly_performance','product_performance','country_performance','nonstandard_codes','customers']}
    labels=defaultdict(Counter);rng=random.Random(42);reservoir=defaultdict(list);month_count=Counter()
    def add(a,g,c):a[0]+=g;a[1]+=c;a[2]+=g-c;a[3]+=1
    def text(v):
        if v is None:return ''
        if isinstance(v,(int,float)) and float(v).is_integer():return str(int(v))
        return str(v).strip()
    for values in rows:
        raw_count+=1;r=dict(zip(headers,values))
        date=r['InvoiceDate']
        if isinstance(date,datetime):
            m=date.strftime('%Y-%m');month_count[m]+=1
            if len(reservoir[m])<100:reservoir[m].append(values)
            else:
                j=rng.randrange(month_count[m])
                if j<100:reservoir[m][j]=values
        if values in seen:continue
        seen.add(values)
        inv=text(r['InvoiceNo']).upper();code=text(r['StockCode']).upper();country=text(r['Country'])
        if not inv or not code or not country or not isinstance(date,datetime):continue
        try:q=float(r['Quantity']);price=float(r['UnitPrice'])
        except (TypeError,ValueError):continue
        if not math.isfinite(q) or not math.isfinite(price) or not q.is_integer() or q==0 or price<=0:continue
        if inv.startswith('C')!=(q<0):continue
        amount=int((Decimal(str(price))*int(q)*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        gross=max(amount,0);cancel=max(-amount,0);retained+=1
        add(totals,gross,cancel)
        add(groups['monthly_performance'][date.strftime('%Y-%m')],gross,cancel)
        add(groups['country_performance'][country],gross,cancel)
        typ='product_performance' if re.fullmatch(r'\d{5}[A-Z]*',code) else 'nonstandard_codes'
        add(groups[typ][code],gross,cancel)
        if text(r['Description']):labels[code][text(r['Description'])]+=1
        customer=text(r['CustomerID'])
        if customer:add(groups['customers'][customer],gross,cancel)
        if q>0:
            invoices.add(inv)
            if customer:customer_invoices[customer].add(inv)
    wb.close()
    segment=defaultdict(lambda:[0,0,0,0])
    for customer,a in groups['customers'].items():
        n=len(customer_invoices[customer]);key='Repeat purchaser' if n>=2 else 'One-invoice purchaser' if n==1 else 'Cancellation only'
        dest=segment[key];dest[0]+=a[0];dest[1]+=a[1];dest[2]+=a[2];dest[3]+=1
    groups['customer_segments']=segment
    keycols={'monthly_performance':'Month','product_performance':'StockCode','country_performance':'Country',
             'nonstandard_codes':'StockCode','customer_segments':'Segment'}
    checks=0
    for table,keycol in keycols.items():
        with (ROOT/'reports'/f'{table}.csv').open(newline='',encoding='utf-8') as f:actual=list(csv.DictReader(f))
        assert len(actual)==len(groups[table]),(table,'row count')
        for r in actual:
            expected=groups[table][r[keycol]]
            columns=['GrossPence','CancellationPence','NetPence','Customers' if table=='customer_segments' else 'LineCount']
            for col,value in zip(columns,expected):assert int(r[col])==value,(table,r[keycol],col);checks+=1
            if 'CancellationValuePct' in r:
                if expected[0]:assert math.isclose(float(r['CancellationValuePct']),expected[1]/expected[0]*100,abs_tol=1e-7)
                else:assert r['CancellationValuePct']==''
                checks+=1
    with (ROOT/'reports/overall_kpis.csv').open(newline='') as f:k=next(csv.DictReader(f))
    for col,v in zip(['GrossPence','CancellationPence','NetPence'],totals[:3]):assert int(k[col])==v;checks+=1
    purchasers={c:s for c,s in customer_invoices.items() if s}
    expected={'SalesInvoices':len(invoices),'AverageGrossInvoiceGBP':totals[0]/100/len(invoices),
              'CancellationValuePct':totals[1]/totals[0]*100,'IdentifiedPurchasingCustomers':len(purchasers),
              'RepeatPurchasingCustomers':sum(len(s)>=2 for s in purchasers.values()),
              'RepeatCustomerPct':sum(len(s)>=2 for s in purchasers.values())/len(purchasers)*100,
              'IdentifiedGrossCoveragePct':sum(a[0] for a in groups['customers'].values())/totals[0]*100}
    for col,value in expected.items():assert math.isclose(float(k[col]),value,abs_tol=1e-7);checks+=1
    meta=json.loads((ROOT/'reports/run_metadata.json').read_text())
    assert meta['audit']['raw_rows']==raw_count and meta['audit']['retained_rows']==retained
    report={'status':'passed','method':'Independent openpyxl/Decimal aggregation, no pandas or production imports',
            'tables_checked':6,'numeric_checks':checks,'raw_rows':raw_count,'retained_rows':retained,
            'integer_pence_checks':'exact','percentage_tolerance':1e-7}
    (ROOT/'reports/verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (ROOT/'data/sample.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(headers)
        for month in sorted(reservoir):w.writerows(reservoir[month])
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
