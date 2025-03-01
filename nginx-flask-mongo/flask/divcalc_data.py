class DataModel:
        def __init__(self, config, symbol=None):
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
            self.dividend_history = None
            
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
                if overview == None or len(overview) == 0:
                    return None

                # Historical is ordered newest -> oldest 
                dividends = api_functions.getDividendHistory(symbol)
                dividend  = dividends[0]
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
                
                # Some records have missing fields
                self.dividend_history = [d for d in dividends if len(d['payment_date']) == 10]
                
                self.financials = {
                    "dividend"          : float(dividend['amount']),
                    "dec_date"          : dividend['declaration_date'],
                    "rcd_date"          : dividend['record_date'],
                    "pay_date"          : dividend['payment_date'],
                    "annual_yield"      : float(overview['DividendYield']),
                    "share_price"       : float(quote['05. price']),
                    "target_price"      : overview['AnalystTargetPrice'],
                    "book_value"        : float(overview['BookValue']),
                    "beta"              : float(overview['Beta']),
                }

                self.articles           = news
                self.sentiment          = api_functions.getSentimentScore(symbol)
