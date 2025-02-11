import json, requests

class AlphaAPI:
    def __init__(self, path):
        key = ''
        with open(path, 'r') as f:
            config = json.load(f)
            self.key = config['alpha']['key']

    def getOverview(symbol):
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={key}'
        r = requests.get(url)
        return r.json()

    def getQuote(symbol):
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={key}'
        r = requests.get(url)
        return r.json()

    def getDividendHistory(symbol):
        url = f'https://www.alphavantage.co/query?function=DIVIDENDS&symbol={symbol}&apikey={key}'
        r = requests.get(url)
        return r.json()

