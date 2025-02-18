#!/usr/bin/env python

# System
import os
import json
import random
import statistics
from decimal import *

# Mongo
from pymongo import MongoClient

# Flask
from flask_bootstrap import Bootstrap5
from flask import Flask, render_template, request, make_response
from flask_session import Session
from flask_wtf import CSRFProtect, FlaskForm
from wtforms.validators import DataRequired, Length    

# Local
from divcalc_api import APIConfiguration, DataModel
from divcalc_forms import SettingsForm, DivCalcForm

# Config
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.secret_key = 'f4h5WR77S6w_pnvzZAwMHGuTW-1vDc2C'

bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)
client = MongoClient("mongo:27017")

api_config = APIConfiguration('./local/local_config.json')
if api_config.config['datasource'] == 'alpha_vantage':
    from divcalc_api import AlphaVantage
    api_functions = AlphaVantage(api_config.config)

@app.route('/', methods=['GET'])
def index():
    tab_div_header = render_template("tab_div_header.jinja")

    return render_template('index.jinja', header=tab_div_header), 200, {'ContentType':'text/html; charset=utf-8'} 

@app.route('/export/<mode>', methods=['GET','POST'])
def export(mode):
    #FIXME
    return render_template('report_csv.jinja'), 200, {'ContentType':'text/json; charset=utf-8'}

@app.route('/help', methods=['GET'])
def help():
    #FIXME
    
    return f'TODO: Add help logic and information after completing design.'

@app.route('/history/', methods=['GET','POST'])
def history():
    #FIXME
    return f'TODO: Add chart/data visual from alpha.getDividendHistory()'

@app.route('/news/<symbol>', methods=['GET','POST'])
def news(symbol):
    news = api_functions.getSentiment(symbol)                
    return render_template('news.jinja', symbol=symbol, news=news), 200, {'ContentType':'text/html; charset=utf-8'} 

@app.route('/report', methods=['GET','POST'])
def report():

    if request.method =='POST': 

        # Lookup search input
        symbol = request.form.get('stock_symbol')
        data_model = DataModel(symbol)
        
        # Init config defaults based on search result and cookie settings
        settings_form = DivCalcForm()
        # Hidden fields. Better way?
        settings_form.stock_symbol.data  = request.form.get('stock_symbol')
        settings_form.share_price.data   = request.form.get('share_price')
        # Mix of company stock data and prefernces
        settings_form.shares_owned.data  = request.form.get('shares_owned')
        settings_form.distribution.data  = request.form.get('distribution')
        settings_form.term.data          = request.form.get('term')
        settings_form.frequency.data     = request.form.get('frequency')
        settings_form.contribution.data  = request.form.get('contribution')
        settings_form.volatility.data    = request.form.get('volatility')
        settings_form.purchase_mode.data = request.form.get('purchase_mode')          

        tab_div_header  = render_template("tab_div_header.jinja")
        tab_div_profile = render_template('tab_div_profile.jinja', 
                                          model = data_model)
        tab_div_finance = render_template('tab_div_financial.jinja', 
                                          model = data_model)
        tab_div_calc    = render_template('tab_div_calc.jinja', 
                                          form  = settings_form, 
                                          data  = data_model)
        
        
        ###########################################################
        #
        # 
        # Data Calculations
        # Notes
        #   Beta is a value relative to the market. 
        #     1.0 = parity 
        #     2.0 = 200% above market
        #    -1.0 = 100% inverse market
        ###########################################################

        ###########################################################
        # VARS
        ###########################################################
        rows = []
        report = []
        summary = ''

        # Dict parameters -> vars for cleaner math
        term          = int(settings_form.term.data)
        contribution  = float(settings_form.contribution.data)     
        shares_owned  = float(settings_form.shares_owned.data)   
        share_price   = float(settings_form.share_price.data)
        volatility    = float(settings_form.volatility.data)   
        distribution  = float(settings_form.distribution.data)
        purchase_mode = settings_form.purchase_mode.data
        frequency     = settings_form.frequency.data

        # Init summary totals
        totals = {
            "months":0,
            "shares_owned":0,
            "last_dividend":0.00,
            "contributions":0.00,
            "asset_growth":0.00,
            "starting_assets":shares_owned * share_price,
            "ending_assets":0.00,
            "starting_distribution":shares_owned * distribution,
            "ending_distribution":0.00,
            "total_reinvested":0.00,
            "distribution_growth":0.00
        }
        
        # Initial balance
        balance = float('0.00')

        ###########################################################
        # MAIN LOOP
        ###########################################################
        
        # Calculate each period
        for p in range(1, 1 + term):

            #Calculate volatile price 
            if volatility > 0:
                v1 = share_price + (share_price * (volatility -1)) / 100
                v2 = share_price - (share_price * (volatility -1)) / 100
                share_price = random.uniform(v1, v2)
            
            dividend = shares_owned * distribution
            # Calculate volatile dividend
            if volatility > 0:
                v1 = distribution + (distribution * (volatility -1)) / 100
                v2 = distribution - (distribution * (volatility -1)) / 100
                distribution = random.uniform(v1, v2)
                dividend = shares_owned * distribution
            
            #Purchase power
            balance += dividend + contribution

            # Define allocation of shares to purchase
            if purchase_mode == 'Fractional':
                shares_purchased = balance / share_price  # Simple division if fractional purchase allowed. Need fees adjustment
            else:
                #Modulus (whole shares only)
                shares_purchased = balance // share_price # Whole shares only

            # Update data for term (row)
            if shares_purchased >= 0:
                shares_owned += shares_purchased
                balance = balance - (shares_purchased * share_price)

            row_data = {
                "period"        : p,
                "balance"       : balance,
                "shares_owned"  : shares_owned,
                "price"         : share_price,
                "asset_value"   : shares_owned * share_price,
                "dividend"      : f'${distribution:,.2f}',
                "income"        : f'${(distribution * shares_owned):,.2f}',
                "contribution"  : f'${contribution:,.2f}',
                "purchased"     : shares_purchased,
            }
            totals['contributions'] += contribution
            totals['total_reinvested'] += dividend

            report.append(row_data)
            rows.append(render_template('dividend_row.jinja', **row_data))
        
        totals['periods'] = p
        totals['shares_owned'] = shares_owned
        
        totals['ending_distribution'] = distribution * shares_owned
        totals['distribution_growth_tot'] =  100 * (totals['ending_distribution'] / totals['starting_distribution'])
        totals['distribution_growth_avg'] = totals['distribution_growth_tot'] / term

        totals['ending_assets'] = shares_owned * share_price
        totals['asset_growth_tot'] = 100 * (totals['ending_assets'] / totals['starting_assets'])
        totals['asset_growth_avg'] = totals['asset_growth_tot'] / term

        match frequency:
            case 'Monthly': 
                totals['years_vested'] = term /12
            case 'Quarterly':
                totals['years_vested'] = term /4
            case 'Semiannual':
                totals['years_vested'] = term /2
            case 'Annual':
                totals['years_vested'] = term
        summary = render_template('tab_div_summary.jinja', totals=totals)

# Roll up chart data    
        i = len(report)
        cols = [i for i in range(1, i +1)]
        income = [float(r.get('income').replace('$','').replace(',','')) for r in report]
        assets = [r.get('asset_value') for r in report]
        price  = [r.get('price') for r in report]
        tab_div_chart = render_template('tab_div_chart.jinja',
                                labels = cols, 
                                income = income,
                                assets = assets,
                                price  = price,
                                        )        
# Roll up report
        return render_template('report.jinja', 
                                header=tab_div_header, 
                                profile=tab_div_profile, 
                                metrics=tab_div_finance, 
                                config=tab_div_calc, 
                                rows=rows, 
                                summary=summary,
                                chart=tab_div_chart,
                                ticker=data_model.profile['stock_symbol']
                                ), 200, {'ContentType':'text/html; charset=utf-8'}
        
    #except Exception as e:
    #    return e, 200, {'ContentType':'text/html; charset=utf-8'}

@app.route('/search', methods=['POST'])
def search():

    if request.method == 'POST':

        # API data filtering key
        symbol = request.form.get('symbol').upper()
        
        # Page header
        tab_div_header = render_template("tab_div_header.jinja")
        
        # Lookup search input
        data_model = DataModel(symbol)
        
        # No records returned, error out
        if data_model == None:
            msg= '''
                <p> No records matched your search term: {symbol}</p>
                <p> Only individual stocks are available for research at this time. ETFs, mutual funds, and the like will not appear.</p>
                <p> If you are unsure, try searching for the company stock with your favorite search engine. Some popular picks include Apple (AAPL), Microsoft (MSFT), and Alphabet (GOOG).</p>            
            '''.format(symbol=symbol)
            return render_template('error.jinja', msg=msg, header=tab_div_header)

        # Record found, fetch all data, build form
        else:
            
            # Init config defaults based on search result and cookie settings
            settings_form = DivCalcForm()
            # Hidden fields. Better way?
            settings_form.stock_symbol.data  = symbol
            settings_form.share_price.data   = data_model.financials['stock_price']
            # Mix of company stock data and prefernces
            settings_form.shares_owned.data  = int(request.cookies.get('shares_owned'))
            settings_form.distribution.data  = Decimal(data_model.financials['dividend'])
            settings_form.term.data          = int(request.cookies.get('term'))
            settings_form.frequency.data     = request.cookies.get('frequency')
            settings_form.contribution.data  = Decimal(request.cookies.get('contribution'))
            settings_form.volatility.data    = Decimal(data_model.financials['beta'])
            settings_form.purchase_mode.data = request.cookies.get('purchase_mode')            
        
            tab_div_profile = render_template('tab_div_profile.jinja',   model=data_model)
            tab_div_finance = render_template('tab_div_financial.jinja', model=data_model)
            tab_div_calc    = render_template('tab_div_calc.jinja',      form=settings_form, data=data_model)

            return render_template('search.jinja', 
                                   header   =tab_div_header, 
                                   profile  =tab_div_profile, 
                                   finance  =tab_div_finance, 
                                   settings =tab_div_calc,
                                   
                                   ), 200, {'ContentType':'text/html; charset=utf-8'}

@app.route('/settings', methods=['GET','POST'])
def settings():
    tab_div_header = render_template("tab_div_header.jinja")

    if request.method == 'GET':

        # Load form, cookies -> fields
        settings_form = SettingsForm()
        settings_form.shares_owned.data  = Decimal(request.cookies.get('shares_owned'))
        settings_form.term.data          = int(request.cookies.get('term'))
        settings_form.frequency.data     = request.cookies.get('frequency')
        settings_form.contribution.data  = Decimal(request.cookies.get('contribution'))
        settings_form.purchase_mode.data = request.cookies.get('purchase_mode')
    
        # render form 
        tab_div_settings = render_template('tab_div_settings.jinja', settings=settings_form)
        return render_template('settings.jinja', 
                               header   = tab_div_header, 
                               content  = tab_div_settings
                               ), 200, {'ContentType':'text/html; charset=utf-8'} 

    if request.method == 'POST':
       
         # Load form data -> dict
        cookie_settings = {
            "shares_owned"  : request.form.get('shares_owned'),
            "term"          : request.form.get('term'),
            "frequency"     : request.form.get('frequency'),
            "contribution"  : request.form.get('contribution'),
            "purchase_mode" : request.form.get('purchase_mode'),
        }
        
        # Load form, init fields from request
        settings_form = SettingsForm()
        settings_form.shares_owned.data  = request.form.get('shares_owned')
        settings_form.term.data          = request.form.get('term')
        settings_form.frequency.data     = request.form.get('frequency')
        settings_form.contribution.data  = request.form.get('contribution')
        settings_form.purchase_mode.data = request.form.get('purchase_mode')
        
        # Render html components
        tab_div_settings = render_template('tab_div_settings.jinja', settings=settings_form)
        response = make_response(render_template('settings.jinja', 
                                                 header  = tab_div_header, 
                                                 content = tab_div_settings
                                                 ), 200, {'ContentType':'text/html; charset=utf-8'})
        # Write dict -> cookies
        for k, v in cookie_settings.items():
            response.set_cookie(k, v)
        return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
