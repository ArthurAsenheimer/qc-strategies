from Selection.FundamentalUniverseSelectionModel import FundamentalUniverseSelectionModel
from datetime import datetime, timedelta




class DividendGrowthSelectionModel(FundamentalUniverseSelectionModel):
    def __init__(self):
        self.selectionDataDict = {}
        self.nextSelectionTime = datetime.min
        super().__init__(True, None)
        
    
    def SelectCoarse(self, algorithm, coarse):
        if algorithm.Time < self.nextSelectionTime:
            return Universe.Unchanged
        coarseFiltered = [c for c in coarse if (c.HasFundamentalData and c.Price > 1 and c.DollarVolume > 1e6 and (algorithm.Time - c.Symbol.ID.Date) > timedelta(365))]
        sortedByDollarVolume = sorted(coarseFiltered, key=lambda c: c.DollarVolume, reverse=True)
        return [c.Symbol for c in sortedByDollarVolume[:1000]]
    
    def SelectFine(self, algorithm, fine):
        filteredByIndustry = sorted(fine, key=lambda f: f.MarketCap, reverse=True)[:500]
        selection = []
        for f in filteredByIndustry:
            if f.Symbol not in self.selectionDataDict:
                self.selectionDataDict[f.Symbol] = SelectionData(algorithm, f.Symbol)
            self.selectionDataDict[f.Symbol].Update(algorithm.Time, f.ValuationRatios.ExpectedDividendGrowthRate)
        selection = dict(sorted(self.selectionDataDict.items(), key=lambda x: x[1].expectedDividendGrowthRate, reverse=True)[:50])
        self.nextSelectionTime = Expiry.EndOfMonth(algorithm.Time)
        return list(selection.keys())




class SelectionData:
    
    def __init__(self, algorithm, symbol):
        self.Symbol = symbol
        self.Time = datetime.min
        self.expectedDividendGrowthRate = 0
        
    
    
    def Update(self, time, expectedDividendGrowthRate):
        self.Time = time
        self.expectedDividendGrowthRate = expectedDividendGrowthRate
        
      
 
        
        
        
        