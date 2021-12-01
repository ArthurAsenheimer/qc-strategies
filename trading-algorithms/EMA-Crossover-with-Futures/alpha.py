
class EmaCrossoverAlphaModel(AlphaModel):
    
    def __init__(self):
        self.symbolDataDict = {}
        self.date = None
    
    def Update(self, algorithm, data):
        insights = []
        if self.date == algorithm.Time.date():
            return insights
        self.date = algorithm.Time.date()
        
        for symbol, symbolData in self.symbolDataDict.items():
            if symbolData.Security.HasData and symbol in data.QuoteBars:
                insight = symbolData.CreateInsight()
                insights.append(insight)
        return insights
        
        
    
    def OnSecuritiesChanged(self, algorithm, changes):
        for security in changes.RemovedSecurities:
            self.symbolDataDict.pop(security.Symbol, None)
            
        for security in changes.AddedSecurities:
            if security.Symbol not in self.symbolDataDict:
                self.symbolDataDict[security.Symbol] = SymbolData(algorithm, security.Symbol)
        
      

class SymbolData:
    
    def __init__(self, algorithm, symbol):
        self.algorithm = algorithm
        self.Symbol = symbol
        self.Security = algorithm.Securities[symbol]
        barsPerDay = self.Security.Exchange.Hours.RegularMarketDuration.seconds/Extensions.ToTimeSpan(Resolution.Minute).seconds
        periodFast, periodSlow = [int(barsPerDay*10), int(barsPerDay*50)]
        self.fast = algorithm.EMA(symbol, periodFast, Resolution.Minute)
        self.slow = algorithm.EMA(symbol, periodSlow, Resolution.Minute)
        self.tol = .01
        self.futureName = symbol.ID.ToString().split()[0]
        self.scheduledEvent = algorithm.Schedule.On(algorithm.DateRules.EveryDay(symbol), algorithm.TimeRules.At(12,0), self.UpdateCharts )
    
    def CreateInsight(self):
        return Insight.Price(self.Symbol, timedelta(2), self.InsightDirection)
    
    
    @property 
    def InsightDirection(self):
        if not self.slow.IsReady:
            return InsightDirection.Flat
        if self.fast.Current.Value > self.slow.Current.Value*(1 + self.tol):
            return InsightDirection.Up
        elif self.fast.Current.Value < self.slow.Current.Value*(1 - self.tol):
            return InsightDirection.Down
        else:
            return InsightDirection.Flat

    
    def UpdateCharts(self):
        if (self.Security.HasData and self.slow.IsReady):
            self.algorithm.Plot('Signals ' + self.futureName, 'Price', self.Security.Close)
            self.algorithm.Plot('Signals ' + self.futureName, 'FastEMA', self.fast.Current.Value)
            self.algorithm.Plot('Signals ' + self.futureName, 'SlowEMA', self.slow.Current.Value)
            
        
        
         
        
        