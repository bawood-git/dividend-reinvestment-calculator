import datetime
import random
from dateutil import parser
from collections import Counter


class Calculator:
    def __init__(self, data_model):
        self.data_model = data_model
        self.config = data_model.config
        self.report = [] #data_model.report
        
        self.totals = {}
        
    def run(self):

        term = self.config['term']
        initial_capital = self.config['initial_capital']
        shares_owned = self.config['shares_owned']
        contribution = self.config['contribution']
        share_price = self.config['share_price']
        volatility = self.config['volatility']
        distribution = self.config['distribution']
        purchase_mode = self.config['purchase_mode']
        frequency = self.config['frequency']




        ###########################################################
        # Initialize assets and beginning balance
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
        self.totals = {
            "initial_capital"       : initial_capital,
            "contributions"         : 0.00,
            "initial_shares"        : shares_owned,
            "starting_assets"       : shares_owned * share_price,
            "starting_distribution" : shares_owned * distribution,
            "total_reinvested"      : 0.00,
        }
        
        ###########################################################
        # Simulate periods through term
        ###########################################################
        match frequency:
            case 'Monthly':
                income_sequence = 12
            case 'Quarterly':
                income_sequence = 4
            case 'Semiannual':
               income_sequence = 2
            case 'Annual':
               income_sequence = 1
        
        frequency_map = {
            'Monthly'   : 12,
            'Quarterly' : 4,
            'Semiannual': 2,
            'Annual'    : 1
        }
        
        months_map = {
            1   : ['December'],
            2   : ['June', 'December'],
            4   : ['March', 'June', 'September', 'December'],
            12  : ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        }
        
        quarters_map = {
            1   : ['Q4'],
            2   : ['Q2', 'Q4'],
            4   : ['Q1', 'Q2', 'Q3', 'Q4'],
            12  : ['Q1', 'Q1', 'Q1', 'Q2', 'Q2', 'Q2', 'Q3', 'Q3', 'Q3', 'Q4', 'Q4', 'Q4']
        }
        
        income_sequence = frequency_map.get(frequency, 1)
        months = months_map[income_sequence]
        quarters = quarters_map[income_sequence]

        #report = []
        
        # Loop through term
        for p in range(1, 1 + (term * income_sequence)):
            
            # Calculate period to year/quarter/month based on frequency
            year = (p - 1) // income_sequence + 1
            month = months[(p - 1) % len(months)]
            quarter = quarters[(p - 1) % len(quarters)]
                
            # Calculate dividend
            dividend = shares_owned * distribution

            #Purchase power
            balance += dividend + contribution
            
            #Calculate volatile price 
            if volatility > 0:
                v1 = share_price + (share_price * (volatility -1)) / 100
                v2 = share_price - (share_price * (volatility -1)) / 100
                share_price = round(random.uniform(v1, v2),4)

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
                "period"            : p,
                "year"              : year,
                "quarter"           : quarter,
                "month"             : month,
                "balance"           : balance,
                "shares_owned"      : shares_owned,
                "share_price"       : share_price,
                "asset_value"       : shares_owned * share_price,
                "dividend"          : f'${distribution:,.2f}',
                "income"            : f'${(distribution * shares_owned):,.2f}',
                "contribution"      : f'${contribution:,.2f}',
                "shares_purchased"  : shares_purchased,
            }
            self.totals['contributions'] += contribution
            self.totals['total_reinvested'] += dividend
            
            self.report.append(row_data)
       
       ###########################################################
       # Roll up totals
       ###########################################################
        self.totals['periods'] = p
        self.totals['years_vested'] = year
       
        # Investment
        self.totals['investment_tot'] = initial_capital + self.totals['contributions']
       
        # Assets/value
        self.totals['cash'] = balance
        self.totals['shares_owned'] = shares_owned
        self.totals['ending_assets'] = shares_owned * share_price
        
        # Dividends/income
        self.totals['ending_distribution'] = distribution * shares_owned
        self.totals['distribution_growth_tot'] = self.totals['ending_distribution'] - self.totals['starting_distribution']
        
        # If you zero out inputs, you have no growth!
        if self.totals['distribution_growth_tot'] > 0:
            self.totals['distribution_growth_pct'] = 100 * (self.totals['distribution_growth_tot'] / self.totals['starting_distribution'])
        else:
            self.totals['distribution_growth_pct'] = 0
        self.totals['distribution_growth_avg'] = self.totals['distribution_growth_tot'] / term
        self.totals['income_annual'] =  (distribution * shares_owned) * income_sequence





class Dividend:
    # Standard mapping for dividend data from variable API sources
    # Dividend History structure: [
    #         { 
    #           amount, declaration_date, record_date, payment_date, open_price, close_price
    #         },...
    #     ]
    def __init__(self, amount, payment_date, declaration_date=None, record_date=None, open_price=None, close_price=None):
        # Required fields
        self.amount = amount
        self.payment_date = payment_date
        # Optional fields
        self.declaration_date = declaration_date
        self.record_date = record_date
        # FIXME Need to add open and close price for the dividend date
        self.open_price = open_price
        self.close_price = close_price


class DataModel:
        def __init__(self):
            # API Data
            self.profile = {
                "stock_symbol"      : None,
                "company_name"      : None,
                "company_desc"      : None,
                "company_website"   : None,
                "stock_sector"      : None,
                "stock_industry"    : None,
                "exchange"          : None,
            }
            
            #FIXME Emulate dividend history
            self.dividend_history = {}
            
            self.financials = {
                "dividend"          : None,
                "dec_date"          : None,
                "rcd_date"          : None,
                "pay_date"          : None,
                "annual_yield"      : None,
                "share_price"       : None,
                "target_price"      : None,
                "book_value"        : None,
                "beta"              : None,
            }

            self.articles           = None
            self.sentiment          = None

            # User Data            
            self.config = {
                "term"              : None,
                "initial_capital"   : None,
                "shares_owned"      : None,
                "contribution"      : None,
                "share_price"       : None,
                "volatility"        : None,
                "distribution"      : None,
                "purchase_mode"     : None,
                "frequency"         : None,
                "dividend"          : None,
            }
            
        def getData(self, config, symbol=None):
            ########################################################
            #
            # DataModel mapping to specic API configurations
            # Supported APIs: Manual, AlphaVantage
            #
            ########################################################

            # Get config settings     
            # Maybe set up a custom integration companion class?
            if config['api_src'] == 'Manual':
                from divcalc_api import ManualStock
                api_functions = ManualStock()
            
            if config['api_src'] == 'AlphaVantage':
                from divcalc_api import AlphaVantage
                api_functions = AlphaVantage(key=config['api_key'])
            
                overview = api_functions.getOverview(symbol)
                
                
                # If data not found, return None
                if overview == {} or 'Error Message' in overview:
                    return None


                ########################################################
                #
                # Dividend History
                #
                ########################################################

                # Historical is ordered newest -> oldest
                dividends = api_functions.getDividendHistory(symbol)
                # Convert date strings to datetime objects
                for d in dividends:
                    # Ensure all date strings are valid for each dividend
                    if len(d['payment_date']) != 10 or len(d['declaration_date']) != 10 or len(d['record_date']) != 10:
                        pass
                    else:
                        d['payment_date'] = parser.parse(d['payment_date']).strftime('%Y-%m-%d')
                        d['declaration_date'] = parser.parse(d['declaration_date']).strftime('%Y-%m-%d')
                        d['record_date'] = parser.parse(d['record_date']).strftime('%Y-%m-%d')
                
                # Create Dividend objects that contain additional fields and utilities 
                self.dividend_history = []
                
                for d in dividends:
                    if len(d['payment_date']) == 10:
                        dividend = Dividend(
                            amount=d['amount'], 
                            payment_date=d['payment_date'], 
                            declaration_date=d['declaration_date'], 
                            record_date=d['record_date'])
                        self.dividend_history.append(dividend)
                # First is newest in AplhaVantage
                dividend  = self.dividend_history[0]

                # Determine dividend frequency                
                self.dividend_frequency = self.getDividedFrequency(dividends)     
                
                quote     = api_functions.getQuote(symbol)
                news      = api_functions.getNewsSentiment(symbol)

                self.profile = {
                    "stock_symbol"      : symbol,
                    "company_name"      : overview['Name'],
                    "company_desc"      : overview['Description'],
                    "company_website"   : overview['OfficialSite'],
                    "stock_sector"      : overview['Sector'],
                    "stock_industry"    : overview['Industry'],
                    "exchange"          : overview['Exchange'],
                }
                
                self.financials = {
                    "dividend"          : float(dividend.amount),
                    "dec_date"          : dividend.declaration_date,
                    "rcd_date"          : dividend.record_date,
                    "pay_date"          : dividend.payment_date,
                    "annual_yield"      : float(overview['DividendYield']) * 100,
                    "share_price"       : float(quote['05. price']),
                    "target_price"      : overview['AnalystTargetPrice'],
                    "book_value"        : float(overview['BookValue']),
                    "beta"              : float(overview['Beta']),
                }

                self.articles           = news
                self.sentiment          = api_functions.getSentimentScore(symbol)
        
        def getDividedFrequency(self, dividends):
            # Dividend structure: [{amount, declaration_date, record_date, payment_date},...]
            if not dividends:
                return None
                        
            dividend_frequency = None
            if len(dividends) >= 1:
                # Calculate dividend frequency
                years = [parser.parse(d['payment_date']).year for d in dividends if len(d['payment_date']) == 10]
                year_counts = Counter(years)
                
                # Determine the most common frequency
                most_common_year, most_common_count = year_counts.most_common(1)[0]

                current_year = datetime.datetime.now().year
                
                # Check if the current year is in the year_counts
                if current_year in year_counts:
                    current_year_count = year_counts[current_year]
                    # Adjust the most common year and count if the current year has more counts
                    if current_year_count > most_common_count:
                        most_common_year = current_year
                        most_common_count = current_year_count
                
                # Map the count to frequency
                if most_common_count >= 12:
                    dividend_frequency = 'Monthly'
                elif most_common_count >= 4:
                    dividend_frequency = 'Quarterly'
                elif most_common_count >= 2:
                    dividend_frequency = 'Semiannual'
                elif most_common_count >= 1:
                    dividend_frequency = 'Annual'
                else:
                    # No dividend history
                    dividend_frequency = None
            
            return dividend_frequency
                
           
