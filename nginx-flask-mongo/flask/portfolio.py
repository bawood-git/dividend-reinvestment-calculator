
class Portfolio:
    def __init__(self):
        return ''

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
    def getdata():
        data = 'some resource like yahoo'
        return data


class Position():
    def __init__(self, data):
        
        # init with form data -> dict -> Position
        self.data = data
        symbol       = data['stock_symbol']
        share_price  = data['share_price']
        shares_owned = data['shares_owned']
        distribution = data['distribution']
        term         = data['term']
        contribution = data['contribution']
        volatility   = data['volatility']
        calculations = {}
    
    def calculate(self):
        lc = Calculation()
        lc.calculate_position(self.data)
    
class Calculation:
    
    def __init__(self):
        pass

    def calculate_position(self, data):
        datasets = {
            "Linear":[], 
            "Volitile":[],
            "Historical":[],
            }
        
        for r in range(1, data['term'] + 1):
            if data['volatility'] > 0:
                data['distribution'] +=1
        return data
