import json, requests

class APIConfiguration:
    def __init__(self, path):
        config = ''
        with open(path, 'r') as f:
            self.config = json.load(f)

class DataMap:
    def __init__(self):
        self.map = {
            "overview":{},
            "quote":{},
            "dividend_history":{},
            }
    def mapAlphaAdvantage(self):
        self.map['overview'] = {
            "company_name":["Name",""],
            "company_description":["Description",""],
            "company_website":["OfficialSite",""],
            "company_origin":["Country",""],
            "category_sector":["Sector",""],
            "category_industry":["Industry",""],
            "stock_exchange":["Exchange",""],
        }


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
        return r.json()

    def getDividendHistory(self, symbol):
        url = f'https://www.alphavantage.co/query?function=DIVIDENDS&symbol={symbol}&apikey={self.key}'
        r = requests.get(url)
        return r.json()

