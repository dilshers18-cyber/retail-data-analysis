import numpy as np
import pandas as pd

def monetary_summary(df,group):
    result=df.groupby(group,dropna=False,as_index=False).agg(
        GrossPence=('GrossPence','sum'),CancellationPence=('CancellationPence','sum'),
        NetPence=('NetPence','sum'),LineCount=('InvoiceNo','size'))
    result['CancellationValuePct']=np.where(result.GrossPence>0,result.CancellationPence/result.GrossPence*100,np.nan)
    return result

def analyze(df):
    gross=int(df.GrossPence.sum());cancel=int(df.CancellationPence.sum());net=int(df.NetPence.sum())
    sales=df[df.Kind=='sale'];known=df[df.CustomerID.notna()];known_sales=sales[sales.CustomerID.notna()]
    invoice_count=sales.InvoiceNo.nunique()
    freq=known_sales.groupby('CustomerID').InvoiceNo.nunique()
    kpis=pd.DataFrame([dict(GrossPence=gross,CancellationPence=cancel,NetPence=net,
         CancellationValuePct=cancel/gross*100 if gross else np.nan,SalesInvoices=invoice_count,
         AverageGrossInvoiceGBP=gross/100/invoice_count if invoice_count else np.nan,
         IdentifiedPurchasingCustomers=len(freq),RepeatPurchasingCustomers=int((freq>=2).sum()),
         RepeatCustomerPct=float((freq>=2).mean()*100) if len(freq) else np.nan,
         IdentifiedGrossCoveragePct=known_sales.GrossPence.sum()/gross*100 if gross else np.nan)])
    monthly=monetary_summary(df,'Month').sort_values('Month')
    first,last=df.InvoiceDate.min(),df.InvoiceDate.max()
    monthly['BoundaryPartialMonth']=False
    if first.day!=1: monthly.loc[monthly.Month==str(first.to_period('M')),'BoundaryPartialMonth']=True
    if last.day!=last.days_in_month: monthly.loc[monthly.Month==str(last.to_period('M')),'BoundaryPartialMonth']=True
    monthly['NetMoMPct']=monthly.NetPence.pct_change()*100
    period_numbers=pd.PeriodIndex(monthly.Month,freq='M').asi8
    gap=pd.Series(np.r_[False,np.diff(period_numbers)!=1],index=monthly.index)
    monthly.loc[monthly.BoundaryPartialMonth|monthly.BoundaryPartialMonth.shift(1,fill_value=False)|gap|
                monthly.NetPence.shift(1).eq(0),'NetMoMPct']=np.nan
    merchandise=df[df.IsMerchandise]
    products=monetary_summary(merchandise,'StockCode')
    labels=(merchandise.dropna(subset=['Description']).groupby(['StockCode','Description']).size().reset_index(name='n')
            .sort_values(['StockCode','n','Description'],ascending=[True,False,True]).drop_duplicates('StockCode'))
    products=products.merge(labels[['StockCode','Description']],on='StockCode',how='left')
    products['Description']=products.Description.fillna('Description unavailable')
    products=products.sort_values(['NetPence','StockCode'],ascending=[False,True])
    countries=monetary_summary(df,'Country').sort_values(['NetPence','Country'],ascending=[False,True])
    special=monetary_summary(df[~df.IsMerchandise],'StockCode').sort_values('NetPence',ascending=False)
    customers=monetary_summary(known,'CustomerID').merge(freq.rename('PurchaseInvoices'),on='CustomerID',how='left')
    customers['PurchaseInvoices']=customers.PurchaseInvoices.fillna(0).astype(int)
    customers['Segment']=np.select([customers.PurchaseInvoices>=2,customers.PurchaseInvoices==1],
                                   ['Repeat purchaser','One-invoice purchaser'],default='Cancellation only')
    segments=customers.groupby('Segment',as_index=False).agg(Customers=('CustomerID','size'),GrossPence=('GrossPence','sum'),
                                                            CancellationPence=('CancellationPence','sum'),NetPence=('NetPence','sum'))
    return {'overall_kpis':kpis,'monthly_performance':monthly,'product_performance':products,
            'country_performance':countries,'customer_segments':segments,'nonstandard_codes':special}
