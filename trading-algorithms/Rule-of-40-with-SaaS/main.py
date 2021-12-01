from selection import RuleOfFortySaasSelectionModel
from portfolio import MarketCapWeightedPortfolioConstructionModel
from collections import deque


class RuleOfFortyScoreSaasStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2010, 1, 1)  
        self.SetCash(1_000_000) 
        self.spx = self.AddIndex('SPX', Resolution.Minute).Symbol
        self.SetBenchmark(self.spx)
        self.AddUniverseSelection(RuleOfFortySaasSelectionModel(self))
        self.AddAlpha(ConstantAlphaModel(InsightType.Price, InsightDirection.Up, timedelta(100)))
        self.SetPortfolioConstruction(MarketCapWeightedPortfolioConstructionModel())
        self.Settings.RebalancePortfolioOnSecurityChanges = True
        self.Settings.RebalancePortfolioOnInsightChanges = False
        self.InitCharts()
        self.Schedule.On(self.DateRules.EveryDay(self.spx), self.TimeRules.BeforeMarketClose(self.spx, 1), self.UpdateCharts)
    
    
    def InitCharts(self):
        chart = Chart('Holdings')
        chart.AddSeries(Series('Number of Holdings', SeriesType.Scatter, ''))
        self.AddChart(chart)
        self.benchmark_init_price = None
        self.init_tpv = None
        self.portfolioHistory = deque()
        
        
    def UpdateCharts(self):
        tpv = self.Portfolio.TotalPortfolioValue
        if self.benchmark_init_price is None or self.init_tpv is None:
            self.benchmark_init_price = self.Benchmark.Evaluate(self.Time)
            self.init_tpv = tpv
        benchmark_adj_price = self.Benchmark.Evaluate(self.Time)/self.benchmark_init_price*self.init_tpv
        self.Plot('Strategy Equity', 'Benchmark SPX', benchmark_adj_price)
        numHoldings = sum(1 for symbol, holding in self.Portfolio.items() if holding.Invested)
        self.Plot('Holdings', 'Number of Holdings', int(numHoldings))
        
        weights = {symbol : holding.HoldingsValue/tpv for symbol, holding in self.Portfolio.items() if holding.Invested}
        weights['time'] = self.Time
        self.portfolioHistory.appendleft(weights)
    
    def OnEndOfAlgorithm(self):
        self.ObjectStore.Save('portfolioHistory', pd.DataFrame(self.portfolioHistory).set_index('time').to_json(orient='split', default_handler=str))
        
        



 