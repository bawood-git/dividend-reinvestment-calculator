import json, requests, statistics

class APIConfiguration:
    def __init__(self, path):
        config = ''
        with open(path, 'r') as f:
            self.config = json.load(f)

class AlphaVantage:
    def __init__(self, config):
        self.config = config
        self.key = config['key']

    def getOverview(self, symbol):
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.key}'
        r = requests.get(url)
        return r.json()

    def getQuote(self, symbol):
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.key}'
        r = requests.get(url)
        d = r.json()
        return d['Global Quote']

    def getDividendHistory(self, symbol):
        url = f'https://www.alphavantage.co/query?function=DIVIDENDS&symbol={symbol}&apikey={self.key}'
        r = requests.get(url)
        d = r.json()
        return d['data']

    def getNewsSentiment(self, symbol):
        url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={self.key}'
        r = requests.get(url)
        return r.json()

    def getSentimentScore(self, symbol):
        #Needsfeed sentiment
        news = self.getNewsSentiment(symbol)
                            
        sentiment_scores = []
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
            sentiment_desc = [float(sentiment['ticker_sentiment_score']) for sentiment in article.get('ticker_sentiment') ]
            sentiment_avg = None
        return f'{sentiment_desc} - Mean:{sentiment_avg}'



class DataModel:
        def __init__(self, symbol):
            api_config = APIConfiguration('./local/local_config.json')
            if api_config.config['datasource'] == 'alpha_vantage':
                from divcalc_api import AlphaVantage
                api_functions = AlphaVantage(api_config.config)
            
            overview = api_functions.getOverview(symbol)
            if overview == {}:
                return None

            dividends   = api_functions.getDividendHistory(symbol)
            dividend    = dividends[0]
            quote       = api_functions.getQuote(symbol)
            news        = api_functions.getNewsSentiment(symbol)

            self.profile = {
                "stock_symbol"      : symbol,
                "company_name"      : overview['Name'],
                "company_desc"      : overview['Description'],
                "company_website"   : overview['OfficialSite'],
                "stock_sector"      : overview['Sector'],
                "stock_industry"    : overview['Industry'],
                "exchange"          : overview['Exchange'],
            }
            
            self.dividend_history = [d for d in dividends if len(d['payment_date']) == 10]
            
            self.financials = {
                "dividend"          : dividend['amount'],
                "dec_date"          : dividend['declaration_date'],
                "rcd_date"          : dividend['record_date'],
                "pay_date"          : dividend['payment_date'],
                "annual_yield"      : overview['DividendYield'],
                "stock_price"       : quote['05. price'],
                "target_price"      : overview['AnalystTargetPrice'],
                "book_value"        : overview['BookValue'],
                "beta"              : overview['Beta'],
            }

            self.articles           = news
            self.sentiment          = api_functions.getSentimentScore(symbol)

            self.config = {
                "shares"            : None,
                "dividend"          : None,
                "term"              : None,
                "frequency"         : None,
                "contributions"     : None,
                "volatility"        : None,
                "purchase_mode"     : None,
            }

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
