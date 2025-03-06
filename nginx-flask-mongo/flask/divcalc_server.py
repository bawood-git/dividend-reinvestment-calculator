#!/usr/bin/env python

# System
import os
from decimal import *
#import authlib
from collections import deque
# Mongo
from pymongo import MongoClient

# Flask
from flask              import Flask, request, session, render_template, redirect
from flask_bootstrap    import Bootstrap5
from flask_session      import Session
from flask_wtf          import CSRFProtect

# Local
from divcalc_data   import DataModel, Dividend, Calculator
from divcalc_forms  import StockSettingsForm, APISettingsForm, DivCalcForm, LoginForm

#App Info
app_info = {
    'name'    :'Dividend Reinvestment Calculator',
    'version' : '0.4.8'
}

# Config
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#FIXME Maybe include a vault?
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)
#client = MongoClient("mongo:27017")

@app.route('/', methods=['GET'])
def index():
    tab_div_header = render_template("tab_div_header.jinja", app_info=app_info)

    return render_template('index.jinja', 
                           header = tab_div_header
                           ), 200, {'ContentType':'text/html; charset=utf-8'} 

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

@app.route("/login", methods=["POST", "GET"])
def login():
    
    if request.method == 'GET':
        tab_div_login = render_template("tab_div_login.jinja", login_form=LoginForm())
        return render_template('login.jinja', login=tab_div_login )
    
    if request.method == 'POST':
        #FIXME
        session['api_src'] = None
        session['api_key'] = None
        session["username"] = request.form.get("username")
        
        if session["username"] != None:
            return redirect('/')
        else:
            tab_div_login = render_template("tab_div_login.jinja", login_form=LoginForm())
            return render_template('login.jinja', login=tab_div_login )

@app.route("/logout", methods=["GET"])
def logout():

    session["username"] = None
        
    tab_div_login = render_template("tab_div_login.jinja", login_form=LoginForm())
    return render_template('login.jinja', login=tab_div_login )
        

@app.route('/news/<symbol>', methods=['GET','POST'])
def news(symbol):
    #news = api_functions.getSentiment(symbol)                
    #return render_template('news.jinja', symbol=symbol, news=news), 200, {'ContentType':'text/html; charset=utf-8'}
    return None

@app.route('/report', methods=['GET','POST'])
def report():

    if request.method =='POST':
        
        ###########################################################
        # Load Data
        ###########################################################
        
        # Recreate DataModel instance using session data
        data_model_data = session.get('data_model')
        if data_model_data is None:
            return redirect('/search', code=302, Response=None)
        
        #data_model = DataModel(config=api_config, symbol=symbol)
        data_model = DataModel()
        data_model.profile              = data_model_data['profile']
        data_model.financials           = data_model_data['financials']
        data_model.dividend_history     = [Dividend(**d) for d in data_model_data['dividend_history']]
        data_model.dividend_frequency   = data_model_data['dividend_frequency']

        # Init config defaults based on search result and cookie settings
        settings_form = DivCalcForm()
        settings_form.stock_symbol.data  = request.form.get('stock_symbol')
        settings_form.share_price.data   = request.form.get('share_price')
        settings_form.shares_owned.data  = request.form.get('shares_owned')
        settings_form.distribution.data  = request.form.get('distribution')
        settings_form.term.data          = request.form.get('term')
        settings_form.frequency.data     = request.form.get('frequency')
        settings_form.contribution.data  = request.form.get('contribution')
        settings_form.volatility.data    = request.form.get('volatility')
        settings_form.purchase_mode.data = request.form.get('purchase_mode')          

        tab_div_header  = render_template("tab_div_header.jinja", 
                                          app_info=app_info)
        tab_div_calc    = render_template('tab_div_calc.jinja', 
                                          form = settings_form, 
                                          data = data_model)

        ###########################################################
        # Load Parameters
        ###########################################################

        # Form data -> vars for cleaner math
        
        data_model.config['term']            = int(settings_form.term.data)
        data_model.config['initial_capital'] = float(settings_form.initial_capital.data)
        data_model.config['shares_owned']    = float(settings_form.shares_owned.data)
        data_model.config['contribution']    = float(settings_form.contribution.data)
        data_model.config['share_price']     = float(settings_form.share_price.data)
        data_model.config['volatility']      = float(settings_form.volatility.data)
        data_model.config['distribution']    = float(settings_form.distribution.data)
        data_model.config['purchase_mode']   = settings_form.purchase_mode.data
        data_model.config['frequency']       = settings_form.frequency.data
        
        # Calculate dividend
        calc = Calculator(data_model)
        calc.run()
        
        tab_div_summary = render_template('tab_div_summary.jinja', totals=calc.totals, model=data_model, frequency=calc.config['frequency'])
        tab_div_report  = render_template('tab_div_report_rows.jinja', report=calc.report)
        
        ###################################
        # Roll up chart data
        ###################################
        
        # Simulation chart
        i = len(calc.report)
        cols = [i for i in range(1, i +1)]
        income = [float(r.get('income').replace('$','').replace(',','')) for r in calc.report]
        assets = [r.get('asset_value') for r in calc.report]
        price  = [r.get('share_price') for r in calc.report]
        tab_div_chart_sim = render_template('tab_div_chart_sim.jinja',
                                labels = cols, 
                                income = income,
                                assets = assets,
                                price  = price,
                                frequency = data_model.config['frequency'],
                                )        

        # Render page with widgets
        return render_template('report.jinja', 
                                header     = tab_div_header,        # Widget
                                config     = tab_div_calc,          # Widget
                                summary    = tab_div_summary,       # Widget
                                chart_sim  = tab_div_chart_sim,     # Widget
                                report     = tab_div_report,        # Widget
                                model      = data_model,            # Data
                                ), 200, {'ContentType':'text/html; charset=utf-8'}
        
@app.route('/search', methods=['POST'])
def search():

    if request.method == 'POST':

        # API data filtering key
        symbol = request.form.get('stock_symbol').upper()
        
        # Confirm data source
        api_config = {
            "api_src": session['api_src'],
            "api_key": session['api_key'],
        }
        
        if api_config['api_src'] == None:
            return redirect('/settings',code=302, Response=None)
        
        # Search and build stock profile
        data_model = DataModel()
        data_model.getData(config=api_config, symbol=symbol)
        
        
        # No records returned on profile, error out
        if data_model.profile.get('stock_symbol') == None:
            tab_div_header = render_template("tab_div_header.jinja", app_info=app_info)

            msg= '''
                <p> No records matched your search term: {symbol}</p>
                <p> Only individual stocks are available for research at this time. ETFs, mutual funds, and the like will not appear.</p>
                <p> If you are unsure, try searching for the company stock with your favorite search engine. Some dividend stocks to try: KO, CVX, UPS, ARR, SHIP</p>            
            '''.format(symbol=symbol)
            return render_template('error.jinja', msg=msg, header=tab_div_header)

        # Record found, fetch all data, build form, add valid data to session
        else:
            
            # Store necessary data in the session
            session['data_model'] = {
                'profile'           : data_model.profile,
                'financials'        : data_model.financials,
                'dividend_history'  : [d.__dict__ for d in data_model.dividend_history],
                'dividend_frequency': data_model.dividend_frequency
            }            
            # Update session stock search history
            if 'stock_history' in session and session['stock_history'] is not None:
                session['stock_history'].appendleft(symbol)
            else:
                session['stock_history'] = deque([symbol], maxlen=5)
            
            # Init config defaults based on search result and cookie settings
            settings_form = DivCalcForm()
            
            # Hidden fields. Better way?
            settings_form.stock_symbol.data  = symbol
            settings_form.share_price.data   = data_model.financials['share_price']
            
            ###########################################################
            # Set form defaults with prefernces if set
            ###########################################################
            # Add initial capital if available from preference
            if session['initial_capital'] != None:
                settings_form.initial_capital.data = Decimal(session['initial_capital'])
            # Add shares owned if available from preference
            if session['shares_owned'] != None:
                settings_form.shares_owned.data  = Decimal(session['shares_owned'])
            # Add term if available from preference
            if session['term'] != None:
                settings_form.term.data = int(session['term'])
            # Add frequency if available from calculation, then preference
            if data_model.dividend_frequency != None:
                settings_form.frequency.data = data_model.dividend_frequency
            if session['frequency'] != None and data_model.dividend_frequency == None:
                settings_form.frequency.data = session['frequency']
            # Add contribution if available from preference
            if session['contribution'] != None:
                settings_form.contribution.data = Decimal(session['contribution'])
            # Add purchase mode if available from preference
            if session['purchase_mode'] != None:
                settings_form.purchase_mode.data = session['purchase_mode']
            
            # Company stock data 
            settings_form.distribution.data  = Decimal(data_model.financials['dividend'])
            settings_form.volatility.data    = Decimal(data_model.financials['beta'])

            # Chart Axes
            div_dates = []
            div_amounts = []
            
            for d in data_model.dividend_history[::-1]:
                div_dates.append(d.payment_date)
                div_amounts.append(d.amount)
                
            # Create page widgets
            tab_div_header = render_template("tab_div_header.jinja", app_info=app_info)
            tab_div_profile = render_template('tab_div_profile.jinja',   model=data_model)
            tab_div_finance = render_template('tab_div_financial.jinja', model=data_model)
            tab_div_history = render_template('tab_div_history.jinja',   model=data_model)
            tab_div_chart   = render_template('tab_div_chart_hist.jinja', 
                                               div_dates   = div_dates,
                                               div_amounts = div_amounts
                                               )
            tab_div_calc    = render_template('tab_div_calc.jinja',
                                              form=settings_form,
                                              data=data_model
                                              )
            # Render page with widgets
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

    if session['username'] == None:
        return redirect('/login', code=302, Response=None)

    if request.method == 'GET':

        # Load form, cookies -> fields
        api_settings_form = APISettingsForm()
        settings_form = StockSettingsForm()
        
        # Load form data from session - API settings
        if session['api_src'] != None:
            api_settings_form.api_src.data = session['api_src']
        if session['api_key'] != None:
            api_settings_form.api_key.data = session['api_key']
            
        # Load form data from session - Stock settings
        if session['initial_capital'] != None:
            settings_form.initial_capital.data = Decimal(session['initial_capital'])
        if session['contribution'] != None:
            settings_form.contribution.data = Decimal(session['contribution'])
        if session['shares_owned'] != None:
            settings_form.shares_owned.data = Decimal(session['shares_owned'])
        if session['term'] != None:
            settings_form.term.data = session['term']
        if session['frequency'] != None:
            settings_form.frequency.data = session['frequency']
        if session['purchase_mode'] != None:
            settings_form.purchase_mode.data = session['purchase_mode']
    
        # Render widgets 
        tab_div_header = render_template("tab_div_header.jinja", app_info=app_info)
        tab_div_settings = render_template('tab_div_settings.jinja', 
                                           settings=settings_form, 
                                           api_settings=api_settings_form)
        settings_page    = render_template('settings.jinja',
                                           header=tab_div_header,
                                           content=tab_div_settings
                                           ), 200, {'ContentType':'text/html; charset=utf-8'} 
        return settings_page
    
    if request.method == 'POST':
        
        # Update session API settings
        api_settings_form = APISettingsForm()
        
        api_settings_form.api_src.data = request.form.get('api_src')
        session['api_src'] = api_settings_form.api_src.data
        
        api_settings_form.api_src.data = request.form.get('api_key')
        session['api_key'] = api_settings_form.api_key.data
        
        # Update session stock configuration settings     
        stock_settings_form = StockSettingsForm()
        
        stock_settings_form.initial_capital.data = request.form.get('initial_capital')
        session['initial_capital'] = stock_settings_form.initial_capital.data
        
        stock_settings_form.contribution.data = request.form.get('contribution')
        session['contribution'] = stock_settings_form.contribution.data
                
        stock_settings_form.shares_owned.data = request.form.get('shares_owned')
        session['shares_owned'] = stock_settings_form.shares_owned.data
        
        stock_settings_form.term.data = request.form.get('term')
        session['term'] = stock_settings_form.term.data
        
        stock_settings_form.frequency.data = request.form.get('frequency')
        session['frequency'] = stock_settings_form.frequency.data
        
        stock_settings_form.purchase_mode.data = request.form.get('purchase_mode')
        session['purchase_mode'] = stock_settings_form.purchase_mode.data
                
        # Render widget(s)
        tab_div_header = render_template("tab_div_header.jinja", app_info=app_info)
        tab_div_settings = render_template('tab_div_settings.jinja', 
                                           settings=stock_settings_form, 
                                           api_settings=api_settings_form)
        # Render page
        settings_page    = render_template('settings.jinja',
                                           header=tab_div_header,
                                           content=tab_div_settings,
                                           #api_status = api_status,
                                           ), 200, {'ContentType':'text/html; charset=utf-8'}
        return settings_page

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
