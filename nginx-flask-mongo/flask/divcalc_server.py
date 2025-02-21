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
        tab_div_calc    = render_template('tab_div_calc.jinja', 
                                          form = settings_form, 
                                          data = data_model)
        
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
        term            = int(settings_form.term.data)
        initial_capital = float(settings_form.initial_capital.data)   
        shares_owned    = float(settings_form.shares_owned.data)
        contribution    = float(settings_form.contribution.data)     
        share_price     = float(settings_form.share_price.data)
        volatility      = float(settings_form.volatility.data)   
        distribution    = float(settings_form.distribution.data)
        purchase_mode   = settings_form.purchase_mode.data
        frequency       = settings_form.frequency.data

        ###########################################################
        # MAIN LOOP
        ###########################################################
        
        # Create position based on initial capital
       
        balance = 0.00
        # Fractional - Use all capital (initial and recurring contributions) to purchase shares
        if purchase_mode == 'Fractional':
            shares_owned += initial_capital / share_price
        # Modulus - Maintain a balance carryover, which would be < price of 1 share
        else:
            shares_purchased = initial_capital // share_price
            shares_owned += shares_purchased
            balance = initial_capital - (shares_purchased * share_price)
        
        # Init summary totals
        totals = {
            "contributions":0.00,
            "starting_assets":shares_owned * share_price,
            "starting_distribution":shares_owned * distribution,
            "total_reinvested":0.00,
        }
        
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
        
        # Roll up Report Summary totals not in loop
        match frequency:
            case 'Monthly':
                income_sequence = 12
            case 'Quarterly':
                income_sequence = 4
            case 'Semiannual':
               income_sequence = 2
            case 'Annual':
               income_sequence = 1
        total_years = term / income_sequence 
                        
        totals['periods'] = p
        totals['years_vested'] = term / income_sequence
       
       # Assets/value
        totals['cash'] = balance
        totals['shares_owned'] = shares_owned
        totals['ending_assets'] = shares_owned * share_price
        totals['asset_growth_tot'] = 100 * (totals['ending_assets'] / totals['starting_assets'])
        totals['asset_growth_avg'] = totals['asset_growth_tot'] / term
        
        # Dividends/income
        totals['ending_distribution'] = distribution * shares_owned
        totals['distribution_growth_tot'] = totals['ending_distribution'] - totals['starting_distribution']
        totals['distribution_growth_pct'] = 100 * (totals['distribution_growth_tot'] / totals['starting_distribution'])
        totals['distribution_growth_avg'] = totals['distribution_growth_tot'] / term
        totals['reinvestment_gain'] = 100 * ((totals['distribution_growth_pct'] / 100) - (data_model.financials['annual_yield'] * total_years))
        totals['yield_years'] = 100 * (data_model.financials['annual_yield'] * total_years)
        totals['income_annual'] =  (distribution * shares_owned) * income_sequence
        
        summary = render_template('tab_div_summary.jinja', totals=totals, model=data_model)

# Roll up chart data

        # History
        div_history_dates = []
        div_history_amount = []
        
        for d in data_model.dividend_history:
            div_history_dates.append(d['payment_date'])
            div_history_amount.append(d['amount'])
                
        #labels = [ d for d in data_model.dividend_history[0]]
        #y1     = [ d for d in data_model.dividend_history[1]]
        tab_div_chart_hist = render_template('tab_div_chart_hist.jinja',
                                div_dates   = div_history_dates, 
                                div_amounts = div_history_amount)        
  
        # Simulation
        i = len(report)
        cols = [i for i in range(1, i +1)]
        income = [float(r.get('income').replace('$','').replace(',','')) for r in report]
        assets = [r.get('asset_value') for r in report]
        price  = [r.get('price') for r in report]
        tab_div_chart_sim = render_template('tab_div_chart_sim.jinja',
                                labels = cols, 
                                income = income,
                                assets = assets,
                                price  = price)        

# Roll up report
        return render_template('report.jinja', 
                                header     = tab_div_header,        # Widget
                                config     = tab_div_calc,          # Widget
                                rows       = rows,                  # Data? FIXME
                                summary    = summary,               # Data? FIXME
                                chart_sim  = tab_div_chart_sim,     # Widget
                                model      = data_model             # Data
                                ), 200, {'ContentType':'text/html; charset=utf-8'}
        
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
        if not hasattr(data_model, 'profile'):
            msg= '''
                <p> No records matched your search term: {symbol}</p>
                <p> Only individual stocks are available for research at this time. ETFs, mutual funds, and the like will not appear.</p>
                <p> If you are unsure, try searching for the company stock with your favorite search engine. Some dividend stocks to try: KO, CVX, UPS, ARR, SHIP</p>            
            '''.format(symbol=symbol)
            return render_template('error.jinja', msg=msg, header=tab_div_header)

        # Record found, fetch all data, build form
        else:
            
            # Init config defaults based on search result and cookie settings
            settings_form = DivCalcForm()
            
            # Hidden fields. Better way?
            settings_form.stock_symbol.data  = symbol
            settings_form.share_price.data   = data_model.financials['stock_price']
            
            # Prefernces
            if request.cookies.get('shares_owned') != None:
                settings_form.shares_owned.data  = Decimal(request.cookies.get('shares_owned'))
            else:
                settings_form.shares_owned.data  = Decimal(0.00)
            if request.cookies.get('term') != None:
                settings_form.term.data = int(request.cookies.get('term'))
            else:
                settings_form.term.data = int(120)
            if request.cookies.get('frequency') != None:
                settings_form.frequency.data = request.cookies.get('frequency')
            else:
                settings_form.frequency.data = 'Monthly'
            if request.cookies.get('contribution') != None:
                settings_form.contribution.data = Decimal(request.cookies.get('contribution'))
            else:
                settings_form.contribution.data = Decimal(0.00)
            if request.cookies.get('purchase_mode') != None:
                settings_form.purchase_mode.data = request.cookies.get('purchase_mode')
            else:
                settings_form.purchase_mode.data = 'Modulus'
            
            # Company stock data 
            settings_form.distribution.data  = Decimal(data_model.financials['dividend'])
            settings_form.volatility.data    = Decimal(data_model.financials['beta'])

            # Chart Stuff
            div_dates = []
            div_amounts = []
            
            for d in data_model.dividend_history:
                div_dates.append(d['payment_date'])
                div_amounts.append(d['amount'])
                
            #labels = [ d for d in data_model.dividend_history[0]]
            #y1     = [ d for d in data_model.dividend_history[1]]
            
            
            # Create widgets
            tab_div_profile = render_template('tab_div_profile.jinja',   model=data_model)
            tab_div_finance = render_template('tab_div_financial.jinja', model=data_model)
            tab_div_history = render_template('tab_div_history.jinja',   model=data_model)
            tab_div_chart   = render_template('tab_div_chart_hist.jinja', 
                                               div_dates   = div_dates,
                                               div_amounts = div_amounts
                                               )
            tab_div_calc    = render_template('tab_div_calc.jinja',      form=settings_form, data=data_model)

            return render_template('search.jinja', 
                                   header   = tab_div_header, 
                                   profile  = tab_div_profile, 
                                   finance  = tab_div_finance,
                                   history  = tab_div_history,
                                   settings = tab_div_calc,
                                   chart    = tab_div_chart
                                   ), 200, {'ContentType':'text/html; charset=utf-8'}

@app.route('/settings', methods=['GET','POST'])
def settings():
    tab_div_header = render_template("tab_div_header.jinja")

    if request.method == 'GET':

        # Load form, cookies -> fields
        settings_form = SettingsForm()
        if request.cookies.get('initial_capital') != None:
            settings_form.shares_owned.data = Decimal(request.cookies.get('initial_capital'))
        else:
            settings_form.shares_owned.data  = Decimal(1000.00)
        if request.cookies.get('shares_owned') != None:
            settings_form.shares_owned.data = Decimal(request.cookies.get('shares_owned'))
        else:
            settings_form.shares_owned.data  = Decimal(100.00)
        if request.cookies.get('term') != None:
            settings_form.term.data = int(request.cookies.get('term'))
        else:
            settings_form.term.data = int(12)
        if request.cookies.get('frequency') != None:
            settings_form.frequency.data = request.cookies.get('frequency')
        else:
            settings_form.frequency.data = 'Monthly'
        if request.cookies.get('contribution') != None:
            settings_form.contribution.data = Decimal(request.cookies.get('contribution'))
        else:
            settings_form.contribution.data = Decimal(0.00)
        if request.cookies.get('purchase_mode') != None:
            settings_form.purchase_mode.data = request.cookies.get('purchase_mode')
        else:
            settings_form.purchase_mode.data = 'Modulus'
    
        # render form 
        tab_div_settings = render_template('tab_div_settings.jinja', settings=settings_form)
        return render_template('settings.jinja', 
                               header   = tab_div_header, 
                               content  = tab_div_settings
                               ), 200, {'ContentType':'text/html; charset=utf-8'} 

    if request.method == 'POST':
       
         # Load form data -> dict
        cookie_settings = {
            "initial_capital"  : request.form.get('initial_capital'),
            "shares_owned"  : request.form.get('shares_owned'),
            "term"          : request.form.get('term'),
            "frequency"     : request.form.get('frequency'),
            "contribution"  : request.form.get('contribution'),
            "purchase_mode" : request.form.get('purchase_mode'),
        }
        
        # Load form, init fields from request
        settings_form = SettingsForm()
        settings_form.initial_capital.data = request.form.get('initial_capital')
        settings_form.shares_owned.data    = request.form.get('shares_owned')
        settings_form.term.data            = request.form.get('term')
        settings_form.frequency.data       = request.form.get('frequency')
        settings_form.contribution.data    = request.form.get('contribution')
        settings_form.purchase_mode.data   = request.form.get('purchase_mode')
        
        # Render html components
        tab_div_settings = render_template('tab_div_settings.jinja', settings=settings_form)
        response = make_response(render_template('settings.jinja', 
                                                 header  = tab_div_header, 
                                                 content = tab_div_settings,
                                                 ), 200, {'ContentType':'text/html; charset=utf-8'})
        # Write dict -> cookies
        for k, v in cookie_settings.items():
            response.set_cookie(k, v)
        return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
