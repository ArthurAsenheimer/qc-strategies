from Selection.FundamentalUniverseSelectionModel import FundamentalUniverseSelectionModel
from datetime import datetime, timedelta




class RuleOfFortySaasSelectionModel(FundamentalUniverseSelectionModel):
    def __init__(self, algorithm):
        self.algorithm = algorithm
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
        filteredByIndustry = [f for f in fine if f.MarketCap > 1e9 and f.AssetClassification.MorningstarIndustryCode in {31110010, 31110020, 31110030, 30830010}] 
        ''' IndustryCodeMapping: 
            31110010 --> 'InformationTechnologyServices',
            31110020 --> 'SoftwareApplication',
            31110030 --> 'SoftwareInfrastructure'
            30830010 --> 'InternetContentAndInformation'
        '''
        selection = []
        for f in filteredByIndustry:
            if f.Symbol not in self.selectionDataDict:
                self.selectionDataDict[f.Symbol] = SelectionData(algorithm, f.Symbol)
            self.selectionDataDict[f.Symbol].Update(algorithm.Time, f.ValuationRatios.FCFYield, f.OperationRatios.RevenueGrowth.Value)
            if self.selectionDataDict[f.Symbol].SatisfiesRuleOfForty:
                selection.append(f.Symbol)
        self.nextSelectionTime = Expiry.EndOfMonth(algorithm.Time)
        return selection




class SelectionData:
    
    def __init__(self, algorithm, symbol):
        self.Symbol = symbol
        self.Time = datetime.min
        self.fcfYield = 0 
        self.revenueGrowth = 0 
        self.efficiencyScore = 0
    
    
    def Update(self, time, fcfYield, revenueGrowth):
        self.Time = time
        self.fcfYield = fcfYield
        self.revenueGrowth = revenueGrowth
        self.efficiencyScore = fcfYield + revenueGrowth
    
    
    @property
    def SatisfiesRuleOfForty(self):
        return self.efficiencyScore > .4
        
        
        
        