import json, requests, statistics

class ManualStock:
    def __init__(self):
        self.data = {
            "stock_symbol"      : 'Manual Entry',
            "company_name"      : 'Manual Entry',
            "company_desc"      : 'Manual Entry',
            "company_website"   : 'Manual Entry',
            "stock_sector"      : 'Manual Entry',
            "stock_industry"    : 'Manual Entry',
            "exchange"          : 'Manual Entry',
        }
        self.dividend_history = []
        self.financials = {
            "dividend"          : 0.0,
            "dec_date"          : 'Manual Entry',
            "rcd_date"          : 'Manual Entry',
            "pay_date"          : 'Manual Entry',
            "annual_yield"      : 0.0,
            "share_price"       : 0.0,
            "target_price"      : 0.0,
            "book_value"        : 0.0,
            "beta"              : 0.0,
        }
        self.articles = []
        self.sentiment = 'Neutral - Mean:None'
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
        }



class AlphaVantage:
    def __init__(self, key):
        self.key = key
        if key == None:
            return {}
        
    def test(self):
        url = f'https://www.alphavantage.co/query?function=MARKET_STATUS&apikey={self.key}'
        r = requests.get(url)
        return r.json()
        

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
