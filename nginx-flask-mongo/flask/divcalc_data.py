import datetime
from dateutil import parser
from collections import Counter

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
                "shares"            : None,
                "dividend"          : None,
                "term"              : None,
                "frequency"         : None,
                "contributions"     : None,
                "volatility"        : None,
                "purchase_mode"     : None,
            }
            
            # Report Data
            self.report = {
                "years_vested"      : None,
                "contrib_vested"    : None,
                "div_vested"        : None,
                "asset_growth_pct"  : None,
                "asset_start_val"   : None,
                "asset_end_val"     : None,
                "asset_cnt"         : None,
                "div_growth_pct"    : None,
                "div_start_amt"     : None,
                "div_end_amt"       : None,
                "years_vested"      : None,
                "years_vested"      : None,
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
                
           
