import pandas as pd
import pytest
from pipeline.clean import clean_data,line_pence
from pipeline.analyze import analyze

def row(**changes):
    r=dict(InvoiceNo='100001',StockCode='12345',Description='Test product',Quantity=2,
           InvoiceDate='2011-01-01 10:00:00',UnitPrice=3.50,CustomerID='12345',Country='United Kingdom')
    r.update(changes);return r

def test_sales_cancellations_and_net_reconcile():
    df,audit,_=clean_data(pd.DataFrame([row(),row(InvoiceNo='C100002',Quantity=-1)]))
    k=analyze(df)['overall_kpis'].iloc[0]
    assert (k.GrossPence,k.CancellationPence,k.NetPence)==(700,350,350)
    assert k.CancellationValuePct==50
    assert audit['retained_rows']==2

@pytest.mark.parametrize('change,reason',[
    ({'InvoiceNo':None},'missing_essential_fields_removed'),
    ({'InvoiceDate':'bad'},'missing_essential_fields_removed'),
    ({'Quantity':'bad'},'invalid_numeric_removed'),
    ({'UnitPrice':float('inf')},'invalid_numeric_removed'),
    ({'Quantity':0},'zero_or_fractional_quantity_removed'),
    ({'Quantity':1.5},'zero_or_fractional_quantity_removed'),
    ({'UnitPrice':0},'nonpositive_price_removed'),
    ({'UnitPrice':-1},'nonpositive_price_removed'),
    ({'InvoiceNo':'C100003'},'cancellation_sign_conflict_removed'),
    ({'Quantity':-2},'unclassified_negative_quantity_removed'),
])
def test_bad_rows_have_explicit_reasons(change,reason):
    df,audit,rejected=clean_data(pd.DataFrame([row(),row(StockCode='99999',**change)]))
    assert len(df)==1 and audit[reason]==1
    assert rejected.ExclusionReason.tolist()==[reason]
    assert sum(v for k,v in audit.items() if k.endswith('_removed'))+len(df)==audit['raw_rows']

def test_anonymous_sales_and_missing_description_are_retained():
    df,audit,_=clean_data(pd.DataFrame([row(CustomerID=None,Description=None),row(InvoiceNo='100002')]))
    result=analyze(df)
    assert result['overall_kpis'].iloc[0].GrossPence==1400
    assert result['overall_kpis'].iloc[0].IdentifiedGrossCoveragePct==50
    assert audit['missing_customer_rows_retained']==1

def test_product_codes_merge_changed_descriptions():
    df,_,_=clean_data(pd.DataFrame([row(),row(InvoiceNo='100002',Description='New description')]))
    assert len(analyze(df)['product_performance'])==1

def test_repeat_customers_use_invoices_not_line_count():
    df,_,_=clean_data(pd.DataFrame([row(),row(StockCode='99999'),row(InvoiceNo='100002',CustomerID='67890')]))
    assert analyze(df)['overall_kpis'].iloc[0].RepeatPurchasingCustomers==0

def test_duplicate_policy():
    df,audit,_=clean_data(pd.DataFrame([row(),row()]))
    assert len(df)==1 and audit['exact_duplicate_rows_removed']==1

def test_pence_rounding_is_half_up_and_signed():
    assert line_pence(1,1.005)==101
    assert line_pence(-1,1.005)==-101
    assert line_pence(2,1.005)==201

def test_special_codes_retained_separately():
    df,_,_=clean_data(pd.DataFrame([row(),row(StockCode='POST',UnitPrice=10)]))
    result=analyze(df)
    assert result['overall_kpis'].iloc[0].GrossPence==2700
    assert result['product_performance'].GrossPence.sum()==700
    assert result['nonstandard_codes'].GrossPence.sum()==2000

def test_partial_month_growth_suppressed():
    df,_,_=clean_data(pd.DataFrame([row(InvoiceDate='2011-01-01'),row(InvoiceNo='100002',InvoiceDate='2011-02-09')]))
    m=analyze(df)['monthly_performance']
    assert m.iloc[-1].BoundaryPartialMonth
    assert pd.isna(m.iloc[-1].NetMoMPct)

def test_missing_schema_and_empty_result_raise():
    with pytest.raises(ValueError,match='Missing required'):clean_data(pd.DataFrame({'x':[1]}))
    with pytest.raises(ValueError,match='No usable'):clean_data(pd.DataFrame([row(UnitPrice=0)]))

def test_growth_not_calculated_across_missing_month():
    df,_,_=clean_data(pd.DataFrame([row(InvoiceDate='2011-01-01'),row(InvoiceNo='100002',InvoiceDate='2011-03-31')]))
    assert pd.isna(analyze(df)['monthly_performance'].iloc[-1].NetMoMPct)
