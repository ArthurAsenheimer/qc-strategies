from alpha import EmaCrossoverAlphaModel
from portfolio import NaiveFuturesPortfolioConstructionModel


class EmaCrossoverFutures(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2015, 1, 1) 
        self.SetCash(1_000_000)
        self.Settings.EnableAutomaticIndicatorWarmUp = True
        futures = [Futures.Metals.Gold, Futures.Energies.CrudeOilWTI, Futures.Indices.SP500EMini, Futures.Currencies.BTC]
        for future in futures:
            self.AddFuture(future, 
                            dataNormalizationMode = DataNormalizationMode.BackwardsRatio,
                            dataMappingMode = DataMappingMode.OpenInterest,
                            contractDepthOffset = 0)

        self.AddAlpha(EmaCrossoverAlphaModel())
        self.Settings.FreePortfolioValuePercentage = .1
        self.SetPortfolioConstruction(NaiveFuturesPortfolioConstructionModel())
        
        
                                            
    


 


