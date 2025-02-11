#!/usr/bin/env python

# System
import os
import json
import random

# Mongo
from pymongo import MongoClient

# Flask
from flask_bootstrap import Bootstrap5
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import Form, validators, StringField, DecimalField, IntegerField, SelectField, SubmitField 
from wtforms.validators import DataRequired, Length

# Local
from portfolio import Portfolio, Stock, Position
from alpha import AlphaAPI

# Config

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.secret_key = 'f4h5WR77S6w_pnvzZAwMHGuTW-1vDc2C'

bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

client = MongoClient("mongo:27017")


api = AlphaAPI('./local/local_config.json')


class LoginForm(FlaskForm):
    uname  = StringField('Username')    # JSON 
    submit = SubmitField('Login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        form = LoginForm()
        return render_template('login.jinja', form=form)
    if request.method == 'POST':
        session['name'] = request.form.get('name')
        return redirect(url_for('index'))
    
@app.route('/', methods=['GET'])
def index():
    form = LoginForm()
    tab_div_header = render_template("tab_div_header.jinja")

    return render_template('index.jinja', header=tab_div_header), 200, {'ContentType':'text/html; charset=utf-8'} 

@app.route('/search', methods=['POST'])
def search():
    symbol = request.form.get('symbol')
    
    if 'POST' == request.method:
        
        overview = alpha.getOverview(symbol)
        
        # Page header
        tab_div_header = render_template("tab_div_header.jinja")

        # No records returned, error out
        if {} == overview:
            return render_template('error.jinja', value=symbol, header=tab_div_header)

        # Record found, fetch all data, build form
        else:
            quote     = alpha.getQuote(symbol)
            dividends = alpha.getDividendHistory(symbol)
            dividend  = dividends['data'][0]
            
            # Init config defaults
            model = {
                "stock_symbol"  : symbol,
                "share_price"   : quote['Global Quote']['05. price'],  
                "shares_owned"  : 1000,                 # Initial position
                "distribution"  : dividend['amount'],   # Dividend payout
                "term"          : 48,                  # Number of iterations  
                "contribution"  : 0.00,                    # Term contribution
                "volatility"    : overview['Beta'],                 
                "frequency"     : "Quarterly",
                "purchase_mode" : "Fractional",
            }
        
            tab_div_profile = render_template('tab_div_profile.jinja', quote=quote, dividend=dividend, overview=overview)
            tab_div_metrics = render_template('tab_div_metrics.jinja', quote=quote, dividend=dividend, overview=overview)
            tab_div_config  = render_template('tab_div_config.jinja',  model=model, quote=quote, dividend=dividend, overview=overview)

            return render_template('search.jinja', header=tab_div_header, profile=tab_div_profile, metrics=tab_div_metrics, config=tab_div_config, quote=quote, overview=overview, dividend=dividend), 200, {'ContentType':'text/html; charset=utf-8'}

@app.route('/report', methods=['GET','POST'])
def report():

    if 'POST' == request.method:

        tab_div_header = render_template("tab_div_header.jinja")
        
        # Update changes
        model = {
            "stock_symbol"  : request.form.get('stock_symbol'),
            "share_price"   : request.form.get('share_price'),  
            "shares_owned"  : request.form.get('shares_owned'),  # Initial position
            "distribution"  : request.form.get('dividend'),      # Dividend payout
            "term"          : int(request.form.get('term')),     # Number of iterations  
            "contribution"  : request.form.get('contribution'),  # Term contribution
            "volatility"    : request.form.get('volatility'),    # Default: Beta
            "frequency"     : request.form.get('frequency'),
            "purchase_mode" : request.form.get('purchase_mode'),
        }
       
        symbol    = request.form.get('stock_symbol')
        overview  = alpha.getOverview(symbol)
        quote     = alpha.getQuote(symbol)
        dividends = alpha.getDividendHistory(symbol)
        dividend  =  dividends['data'][0]
       
        tab_div_profile = render_template('tab_div_profile.jinja', dividend=dividend, quote=quote, overview=overview)
        tab_div_metrics = render_template('tab_div_metrics.jinja', dividend=dividend, quote=quote, overview=overview)
        tab_div_config = render_template('tab_div_config.jinja', model=model, overview=overview, dividend=dividend, quote=quote)        

        rows = []
        report = []
        summary = ''

        # Init summary data 
        totals = {
            "months":0,
            "value":0.00,
            "shares_owned":0,
            "last_dividend":0.00,
            "total_dividends":0.00,
            "contributions":0.00,
            "pct_growth":0.00
        }

        # Config parameters    
        contribution = float(model['contribution'])     
        shares_owned = float(model['shares_owned'])   
        share_price  = float(model['share_price'])   
        volatility   = float(model['volatility'])      
        distribution = float(model['distribution'])  
        
        # Initial balance
        balance = float('0.00')

        # Calculate 
        for m in range(1, 1 + model['term']):

            #Calculate volatile price 
            if volatility > 0:
                v1 = share_price + (share_price * (volatility / 100))
                v2 = share_price - (share_price * (volatility / 100))
                share_price = random.uniform(v1, v2)
            
            # Calculate dividend
            dividend = shares_owned * distribution
            if volatility > 0:
                v1 = distribution + (distribution * (volatility / 100))
                v2 = distribution - (distribution * (volatility / 100))
                distribution = random.uniform(v1, v2)
                dividend = shares_owned * distribution
            
            #Purchase power
            balance += dividend + contribution

            # Define allocation of shares to purchase
            if 'Fractional' == model['purchase_mode']:
                shares_purchased = balance / share_price  # Simple division if fractional purchase allowed. Need fees adjustment
            else:
                shares_purchased = balance // share_price # Whole shares only

            # Update data for term (row)
            if shares_purchased >= 1.0:
                shares_owned += shares_purchased
                balance = balance - (shares_purchased * share_price)
            
            row_data = {
                "period":       m,
                "balance":      balance,
                "shares_owned": shares_owned,
                "price":        f'${share_price:,.2f}',
                "asset_value":  shares_owned * share_price,
                "dividend":     f'${distribution:,.2f}',
                "income":       f'${(distribution * shares_owned):,.2f}',
                "contribution": f'${contribution:,.2f}',
                "purchased":    shares_purchased,
            }
            totals['months'] = m
            totals['value'] = shares_owned * share_price
            totals['contributions'] += contribution
            totals['last_dividend'] = dividend
            totals['total_dividends'] += dividend
            totals['shares_owned'] = shares_owned

            if shares_owned > 0:
                totals['pct_growth'] = dividend / totals['value']

            report.append(row_data)
            rows.append(render_template('dividend_row.jinja', **row_data))
            summary = render_template('dividend_totals.jinja', **totals)
# Roll up chart data    
        i = len(report)
        cols = [i for i in range(1, i +1)]
        income = [float(r.get('income').replace('$','').replace(',','')) for r in report]
        assets =  [r.get('asset_value')/100 for r in report]
        tab_div_chart = render_template('tab_div_chart.jinja',
                                labels=cols, 
                                income=income,
                                assets=assets,
                                        )        
# Roll up report
        return render_template('report.jinja', 
                                header=tab_div_header, 
                                profile=tab_div_profile, 
                                metrics=tab_div_metrics, 
                                config=tab_div_config, 
                                rows=rows, 
                                summary=summary,
                                chart=tab_div_chart,
                                ticker=quote['Global Quote']['01. symbol']
                                ), 200, {'ContentType':'text/html; charset=utf-8'}
        
    #except Exception as e:
    #    return e, 200, {'ContentType':'text/html; charset=utf-8'}

@app.route('/history', methods=['GET','POST'])
def history():
    return f'TODO: Add chart/data visual from alpha.getDividendHistory()'

@app.route('/export/pdf', methods=['GET','POST'])
def pdfExport(mode, rows):

    return render_template('report_pdf.jinja', rows=rows,), 200, {'ContentType':'text/json; charset=utf-8'}

@app.route('/export/csv', methods=['GET','POST'])
def csv(rows):

    return render_template('report_csv.jinja', rows=rows,), 200, {'ContentType':'text/json; charset=utf-8'}


@app.route('/export/json', methods=['GET','POST'])
def jsn(rows):

    return render_template('report_json.jinja', rows=rows,), 200, {'ContentType':'text/json; charset=utf-8'}



@app.route('/export/data', methods=['GET'])
def download():
    d = request.args.get('d')
    j = json.loads(d)
    return j


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
