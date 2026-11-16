from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def create_charts(frames,meta,output):
    output=Path(output)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    currency=FuncFormatter(lambda x,pos:f'£{x:,.0f}')
    def finish(fig,name,note):
        fig.text(.02,.02,note+'\nSource: UCI Online Retail, Chen (2015); cleaned historical records.',fontsize=8,color='#475569')
        fig.tight_layout(rect=(0,.12,1,.96));fig.savefig(output/name,dpi=170,facecolor='white');plt.close(fig)
    k=frames['overall_kpis'].iloc[0]
    fig,ax=plt.subplots(figsize=(10,5.6))
    values=[k.GrossPence/100,k.CancellationPence/100,k.NetPence/100]
    bars=ax.bar(['Gross recorded sales','Recorded cancellations','Net recorded value'],values,color=['#2563eb','#ea580c','#0f766e'])
    ax.bar_label(bars,labels=[f'£{v:,.0f}' for v in values],padding=5)
    ax.set_ylim(0,max(values)*1.2);ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:f'£{x/1e6:.1f}m'))
    ax.set_title('Sales value after recorded cancellations',loc='left',fontweight='bold')
    finish(fig,'01_sales_and_cancellations.png','Net = gross minus recorded cancellations. Includes nonstandard codes; not profit or audited recognized revenue.')
    d=frames['monthly_performance'];fig,ax=plt.subplots(figsize=(11,5.6))
    x=list(range(len(d)));ax.plot(x,d.GrossPence/100,marker='o',label='Gross',color='#2563eb')
    ax.plot(x,d.NetPence/100,marker='o',label='Net',color='#0f766e')
    for i,r in enumerate(d.itertuples()):
        if r.BoundaryPartialMonth:ax.axvspan(i-.4,i+.4,color='#fed7aa',alpha=.6);ax.annotate('Partial month',(i,r.NetPence/100),xytext=(-90,25),textcoords='offset points',fontsize=9)
    ax.set_xticks(x,d.Month,rotation=45,ha='right');ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:f'£{x/1000:,.0f}k'));ax.legend()
    ax.set_title('Monthly sales | incomplete boundary periods flagged',loc='left',fontweight='bold')
    finish(fig,'02_monthly_performance.png',f"Observed records: {meta['first_timestamp'][:10]} to {meta['last_timestamp'][:10]}. Do not compare partial December 2011 with full months.")
    d=frames['product_performance'].head(10).sort_values('NetPence');fig,ax=plt.subplots(figsize=(11,6.6))
    labels=d.StockCode.astype(str)+' | '+d.Description.str.slice(0,36)
    bars=ax.barh(labels,d.NetPence/100,color='#0f766e');ax.bar_label(bars,labels=[f'£{v/100:,.0f}' for v in d.NetPence],padding=4,fontsize=9)
    ax.set_xlim(min(0,d.NetPence.min()/100*1.2) if len(d) else 0,max(d.NetPence.max()/100*1.25,1) if len(d) else 1);ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f'£{x/1000:,.0f}k'))
    if d.empty:ax.text(.5,.5,'No qualifying merchandise codes in this input.',ha='center',transform=ax.transAxes)
    ax.set_title('Top products by net recorded value',loc='left',fontweight='bold')
    finish(fig,'03_top_products.png','Grouped by StockCode. Five-digit codes with optional letter suffixes are treated as merchandise; other codes are reported separately.')
    d=frames['country_performance'].query('Country != "United Kingdom"').head(10).sort_values('NetPence')
    fig,ax=plt.subplots(figsize=(10,6));bars=ax.barh(d.Country,d.NetPence/100,color='#2563eb')
    ax.bar_label(bars,labels=[f'£{v/100:,.0f}' for v in d.NetPence],padding=4,fontsize=9)
    ax.set_xlim(0,max(d.NetPence.max()/100*1.25,1) if len(d) else 1);ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f'£{x/1000:,.0f}k'))
    ax.set_title('Largest markets outside the UK | net value',loc='left',fontweight='bold')
    finish(fig,'04_international_markets.png','UK excluded from this chart for readability; all countries remain in the exported table. No market-size adjustment.')
    d=frames['customer_segments'];fig,ax=plt.subplots(figsize=(10,5.6));bars=ax.bar(d.Segment,d.Customers,color=['#2563eb','#0f766e','#94a3b8'][:len(d)])
    ax.bar_label(bars,padding=4);ax.set_ylim(0,max(d.Customers.max()*1.2,1) if len(d) else 1);ax.set_ylabel('Identified customers')
    ax.set_title('Customer purchase frequency | observed window only',loc='left',fontweight='bold')
    finish(fig,'05_customer_segments.png','Repeat = at least two distinct positive-sales invoices. Missing CustomerID excluded here, retained in sales totals. Not a retention rate.')
