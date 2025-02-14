from api_config import APIConfiguration

class CompanyProfile:
    def __init__(self, symbol):
        
        api_config = APIConfiguration('./local/local_config.json')
        if api_config.config['datasource'] == 'alpha_vantage':
            from api_config import AlphaVantage
            api_functions = AlphaVantage(api_config.config)

        overview = api_functions.getOverview(symbol)

        self.properties = {
            "ticker":symbol,
            "company_name": overview['Name'],
            "description":  overview['Description'],
            "website":      overview['OfficialSite'],
            "sector":       overview['Sector'],
            "industry":     overview['Industry'],
            "country":      overview['Country'],
            "exchange":     overview['Exchange'],
            "sentiment":    overview['sentiment'],
        }


    def getProfile(self, apiFunctions):
        pass
    def getMetrics(self, apiFunctions):
        pass

