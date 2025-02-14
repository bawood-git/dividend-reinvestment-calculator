#!/usr/bin/env python

# System
import os
import json
import random
import statistics

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
from api_config import APIConfiguration

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
    from api_config import AlphaVantage
    api_functions = AlphaVantage(api_config.config)

def getSentimentScore(symbol):
    #Needsfeed sentiment
    sentiment_scores   = []
    news = api_functions.getSentiment(symbol)
                        
    for article in news['feed']:
        for sentiment in article.get('ticker_sentiment'):
            if sentiment['ticker'] == symbol:
                        sentiment_scores.append(float(sentiment['ticker_sentiment_score']))

    if sentiment_scores:
        sentiment_avg = statistics.mean(sentiment_scores)
        if sentiment_avg >= 0.35:
            sentiment_desc = 'Bullish'
        elif sentiment_avg > 0.15:
            sentiment_desc = 'Somewhat Bullish'
        elif sentiment_avg <= -0.35:
            sentiment_desc = 'Bearish'
        elif sentiment_avg <= -0.15:
            sentiment_desc = 'Somewhat-Bearish'
        else:
            sentiment_desc = 'Neutral'
    else:
        sentiment_desc = 'No news at the moment'
        sentiment_avg = None
    return f'{sentiment_desc} - Mean:{sentiment_avg}'

@app.route('/', methods=['GET'])
def index():
    tab_div_header = render_template("tab_div_header.jinja")
    return render_template('index.jinja', header=tab_div_header), 200, {'ContentType':'text/html; charset=utf-8'} 

@app.route('/search', methods=['POST'])
def search():
    symbol = request.form.get('symbol')
    
    if 'POST' == request.method:
        
        # Page header
        tab_div_header = render_template("tab_div_header.jinja")
        
        # Lookup search input
        overview = api_functions.getOverview(symbol)

        # No records returned, error out
        if {} == overview:
            msg= '''
                <p> No records matched your search term: {symbol}</p>
                <p> Only individual stocks are available for research at this time. ETFs, mutual funds, and the like will not appear.</p>
                <p> If you are unsure, try searching for the company stock with your favorite search engine. Some popular picks include Apple (AAPL), Microsoft (MSFT), and Alphabet (GOOG).</p>            
            '''.format(symbol=symbol)
            return render_template('error.jinja', msg=msg, header=tab_div_header)

        # Record found, fetch all data, build form
        else:
            quote     = api_functions.getQuote(symbol)
            dividends = api_functions.getDividendHistory(symbol)
            dividend  = dividends['data'][0]
            sentiment = getSentimentScore(symbol)
            
            # Init config defaults
            config = {
                "stock_symbol"  : symbol,
                "share_price"   : quote['Global Quote']['05. price'],  
                "shares_owned"  : 1000,                 
                "distribution"  : dividend['amount'],   
                "term"          : 48,                    
                "contribution"  : 0.00,
                "volatility"    : overview['Beta'],                 
                "frequency"     : "Quarterly",
                "purchase_mode" : "Fractional",
            }
        
            tab_div_profile = render_template('tab_div_profile.jinja', quote=quote, dividend=dividend, overview=overview, sentiment=sentiment)
            tab_div_metrics = render_template('tab_div_metrics.jinja', quote=quote, dividend=dividend, overview=overview)
            tab_div_config  = render_template('tab_div_config.jinja',  model=config, quote=quote, dividend=dividend, overview=overview)

            return render_template('search.jinja', header=tab_div_header, profile=tab_div_profile, metrics=tab_div_metrics, config=tab_div_config, quote=quote, overview=overview, dividend=dividend), 200, {'ContentType':'text/html; charset=utf-8'}

@app.route('/report', methods=['GET','POST'])
def report():

    if 'POST' == request.method:

        tab_div_header = render_template("tab_div_header.jinja")
        
        # Web form (Configure Model Parameters) values -> Dict
        model = {
            "stock_symbol"  : request.form.get('stock_symbol'),
            "share_price"   : request.form.get('share_price'),  
            "shares_owned"  : request.form.get('shares_owned'),  # Initial position
            "distribution"  : request.form.get('dividend'),      # Dividend payout
            "term"          : request.form.get('term'),          # Number of iterations  
            "contribution"  : request.form.get('contribution'),  # Term contribution
            "volatility"    : request.form.get('volatility'),    # Default: Beta
            "frequency"     : request.form.get('frequency'),
            "purchase_mode" : request.form.get('purchase_mode'),
        }

        overview  = api_functions.getOverview(model['stock_symbol'])
        quote     = api_functions.getQuote(model['stock_symbol'])
        dividends = api_functions.getDividendHistory(model['stock_symbol'])
        dividend  = dividends['data'][0]
       
        sentiment = getSentimentScore(model['stock_symbol'])

        tab_div_profile = render_template('tab_div_profile.jinja', dividend=dividend, quote=quote, overview=overview, sentiment=sentiment)
        tab_div_metrics = render_template('tab_div_metrics.jinja', dividend=dividend, quote=quote, overview=overview)
        tab_div_config = render_template('tab_div_config.jinja', model=model, overview=overview, dividend=dividend, quote=quote)        

        rows = []
        report = []
        summary = ''


        # Dict parameters -> vars for cleaner math
        term         = int(model['term'])
        contribution = float(model['contribution'])     
        shares_owned = float(model['shares_owned'])   
        share_price  = float(model['share_price'])
        volatility   = float(model['volatility']) -1      
        distribution = float(model['distribution'])


        # Init summary totals
        totals = {
            "months":0,
            "shares_owned":0,
            "last_dividend":0.00,
            "contributions":0.00,
            "pct_growth":0.00,
            "starting_assets":shares_owned * share_price,
            "ending_assets":0.00,
            "starting_distribution":shares_owned * distribution,
            "ending_distribution":0.00,
            "total_reinvested":0.00,
            "distribution_growth":0.00

        }
        
        # Initial balance
        balance = float('0.00')

        # Calculate each period
        for p in range(1, 1 + term):

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
            if shares_purchased >= 0:
                shares_owned += shares_purchased
                balance = balance - (shares_purchased * share_price)
            
            row_data = {
                "period":       p,
                "balance":      balance,
                "shares_owned": shares_owned,
                "price":        f'${share_price:,.2f}',
                "asset_value":  shares_owned * share_price,
                "dividend":     f'${distribution:,.2f}',
                "income":       f'${(distribution * shares_owned):,.2f}',
                "contribution": f'${contribution:,.2f}',
                "purchased":    shares_purchased,
            }

            totals['periods'] = p
            totals['contributions'] += contribution
            totals['total_reinvested'] += dividend


            report.append(row_data)
            rows.append(render_template('dividend_row.jinja', **row_data))
    
        totals['shares_owned'] = shares_owned
        totals['ending_distribution'] = dividend

        totals['distribution_growth'] = (totals['ending_distribution'] / totals['starting_distribution']) * 100

        totals['ending_assets'] = shares_owned * share_price
        if shares_owned > 0:
            totals['pct_growth'] = (totals['ending_assets'] / totals['starting_assets']) *100

        match model['frequency']:
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
        assets =  [r.get('asset_value') for r in report]
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

@app.route('/history/', methods=['GET','POST'])
def history():
    #FIXME
    return f'TODO: Add chart/data visual from alpha.getDividendHistory()'

@app.route('/news/<symbol>', methods=['GET','POST'])
def news(symbol):

    news = api_functions.getSentiment(symbol)                
    
    return render_template('news.jinja', news=news), 200, {'ContentType':'text/html; charset=utf-8'} 

@app.route('/export/csv', methods=['GET','POST'])
def csv(rows):
    #FIXME
    return render_template('report_csv.jinja', rows=rows,), 200, {'ContentType':'text/json; charset=utf-8'}


@app.route('/export/json', methods=['GET','POST'])
def jsn(rows):
    #FIXME
    return render_template('report_json.jinja', rows=rows,), 200, {'ContentType':'text/json; charset=utf-8'}



@app.route('/export/data', methods=['GET'])
def download():
    #FIXME
    d = request.args.get('d')
    j = json.loads(d)
    return j


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
