from selection import DividendGrowthSelectionModel
from portfolio import MarketCapWeightedPortfolioConstructionModel

class DividendGrowthRateStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2010, 1, 1)  
        self.SetCash(1_000_000)  
        self.UniverseSettings.Resolution = Resolution.Minute
        self.AddUniverseSelection(DividendGrowthSelectionModel())
        self.AddAlpha(ConstantAlphaModel(InsightType.Price, InsightDirection.Up, timedelta(30)))
        self.Settings.RebalancePortfolioOnInsightChanges = False
        self.Settings.RebalancePortfolioOnSecurityChanges = True
        self.SetPortfolioConstruction(MarketCapWeightedPortfolioConstructionModel())
        


  
        


