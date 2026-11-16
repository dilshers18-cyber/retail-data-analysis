from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd

COLUMNS = ['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']

def line_pence(quantity, price):
    """Round each signed line to pennies with an explicit half-up convention."""
    return int((Decimal(str(price))*Decimal(str(int(quantity)))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def clean_data(raw):
    missing=sorted(set(COLUMNS)-set(raw.columns))
    if missing: raise ValueError(f'Missing required columns: {missing}')
    df=raw[COLUMNS].copy()
    audit={'raw_rows':len(df)}
    df=df.drop_duplicates()
    audit['exact_duplicate_rows_removed']=len(raw)-len(df)
    for col in ['InvoiceNo','StockCode','Description','CustomerID','Country']:
        df[col]=df[col].astype('string').str.strip().replace('',pd.NA)
    # Excel can represent integer identifiers as floating point numbers.
    for col in ['InvoiceNo','StockCode','CustomerID']:
        df[col]=df[col].str.replace(r'^(\d+)\.0$',r'\1',regex=True)
    df['InvoiceNo']=df.InvoiceNo.str.upper()
    df['StockCode']=df.StockCode.str.upper()
    df['Quantity']=pd.to_numeric(df.Quantity,errors='coerce')
    df['UnitPrice']=pd.to_numeric(df.UnitPrice,errors='coerce')
    df['InvoiceDate']=pd.to_datetime(df.InvoiceDate,errors='coerce')
    excluded=[]
    def retain(mask,reason):
        nonlocal df
        mask=mask.fillna(False)
        rejected=df.loc[~mask].copy();rejected['ExclusionReason']=reason
        excluded.append(rejected)
        audit[reason]=len(rejected)
        df=df.loc[mask].copy()
    retain(df[['InvoiceNo','StockCode','Country','InvoiceDate']].notna().all(axis=1),'missing_essential_fields_removed')
    retain(np.isfinite(df[['Quantity','UnitPrice']]).all(axis=1),'invalid_numeric_removed')
    retain((df.Quantity!=0)&(df.Quantity%1==0),'zero_or_fractional_quantity_removed')
    retain(df.UnitPrice>0,'nonpositive_price_removed')
    cancellation=df.InvoiceNo.str.startswith('C')
    retain(~(cancellation&(df.Quantity>0)),'cancellation_sign_conflict_removed')
    retain(~((df.Quantity<0)&~df.InvoiceNo.str.startswith('C')),'unclassified_negative_quantity_removed')
    if df.empty: raise ValueError('No usable sales or cancellation records remain.')
    df['Quantity']=df.Quantity.astype('int64')
    df['Kind']=np.where(df.Quantity<0,'cancellation','sale')
    df['LinePence']=[line_pence(q,p) for q,p in zip(df.Quantity,df.UnitPrice)]
    df['GrossPence']=df.LinePence.clip(lower=0)
    df['CancellationPence']=(-df.LinePence).clip(lower=0)
    df['NetPence']=df.GrossPence-df.CancellationPence
    df['Month']=df.InvoiceDate.dt.to_period('M').astype(str)
    # Analytical identifier rule; unusual codes are reported separately, never silently deleted.
    df['IsMerchandise']=df.StockCode.str.fullmatch(r'\d{5}[A-Z]*',na=False)
    audit['retained_rows']=len(df)
    audit['sale_rows']=int((df.Kind=='sale').sum())
    audit['cancellation_rows']=int((df.Kind=='cancellation').sum())
    audit['missing_customer_rows_retained']=int(df.CustomerID.isna().sum())
    audit['missing_description_rows_retained']=int(df.Description.isna().sum())
    audit['nonstandard_code_rows_retained']=int((~df.IsMerchandise).sum())
    return df.reset_index(drop=True),audit,pd.concat(excluded,ignore_index=True)
