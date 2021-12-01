
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
from itertools import groupby


class MarketCapWeightedPortfolioConstructionModel(PortfolioConstructionModel):
    
    def __init__(self):
        self.marketCapDict = {}
        self.removedSymbols = []
        self.insightCollection = InsightCollection()
        self.nextExpiryTime = datetime.min.replace(tzinfo=pytz.utc)
        self.rebalanceFreq = timedelta(30)
        self.securities = {}
        self.maxWeight = .1
    
    
    def CreateTargets(self, algorithm, insights):
        targets = []
        if not self.ShouldCreateTargets(algorithm.UtcTime, insights):
            return targets
        self.insightCollection.AddRange(insights)
        targets.extend(self.CreateZeroQuantityTargetsForRemovedSecurities())
        targets.extend(self.CreateZeroQuantityTargetsForExpiredInsights(algorithm))
        lastActiveInsights = self.GetLastActiveInsights(algorithm)
        if self.ShouldUpdateTargetPercent(algorithm, lastActiveInsights):
            weights = self.DetermineTargetPercent(algorithm, lastActiveInsights)
            targets.extend([PortfolioTarget.Percent(algorithm, symbol, weight) for symbol, weight in weights.items()])
        self.UpdateNextExpiryTime(algorithm)
        return targets
        
    
    def ShouldCreateTargets(self, time, insights):
        return len(insights) > 0 or (time > self.nextExpiryTime)
    
    def CreateZeroQuantityTargetsForRemovedSecurities(self):
        if len(self.removedSymbols) == 0:
            return []
        zeroTargets = [PortfolioTarget(symbol, 0) for symbol in self.removedSymbols]
        self.insightCollection.Clear(self.removedSymbols)
        self.removedSymbols = []
        return zeroTargets
        
    
    def CreateZeroQuantityTargetsForExpiredInsights(self, algorithm):
        zeroTargets = []
        expiredInsights = self.insightCollection.RemoveExpiredInsights(algorithm.UtcTime)
        if len(expiredInsights) == 0:
            return zeroTargets
        key = lambda insight: insight.Symbol
        for symbol, _ in groupby(sorted(expiredInsights, key=key), key):
            if not self.insightCollection.HasActiveInsights(symbol, algorithm.UtcTime): 
                zeroTargets.append(PortfolioTarget(symbol, 0))
                continue
        return zeroTargets
        
    
    def GetLastActiveInsights(self, algorithm):
        activeInsights = self.insightCollection.GetActiveInsights(algorithm.UtcTime)
        lastActiveInsights = []
        groupedInsights = GroupBy(activeInsights, key = lambda insight: (insight.Symbol, insight.SourceModel))
        for kvp in groupedInsights:
            lastActiveInsights.append(sorted(kvp[1], key=lambda insight: insight.GeneratedTimeUtc)[-1])
        return lastActiveInsights    

    
    def ShouldUpdateTargetPercent(self, algorithm, lastActiveInsights):
        if algorithm.UtcTime > self.nextExpiryTime:
            return True
        for insight in lastActiveInsights:
            if insight.Direction != InsightDirection.Flat and not algorithm.Portfolio[insight.Symbol].Invested:
                return True
            elif insight.Direction != InsightDirection.Up and algorithm.Portfolio[insight.Symbol].IsLong:
                return True
            elif insight.Direction != InsightDirection.Down and algorithm.Portfolio[insight.Symbol].IsShort:
                return True
            else:
                continue
        return False
  
    
    def UpdateNextExpiryTime(self, algorithm):
        self.nextExpiryTime = self.insightCollection.GetNextExpiryTime()
        if self.nextExpiryTime is None:
            self.nextExpiryTime = algorithm.UtcTime + self.rebalanceFreq
    
    
    def DetermineTargetPercent(self, algorithm, lastActiveInsights):
        weights = {}
        if not lastActiveInsights:
            return weights
        marketCapBySymbol = {insight.Symbol : algorithm.Securities[insight.Symbol].Fundamentals.MarketCap if insight.Direction == InsightDirection.Up else 0 for insight in lastActiveInsights if insight.Symbol in self.securities}
        aggregatedMarketCap = sum(marketCapBySymbol.values())
        weights = {symbol : min(self.maxWeight, round(mktCap/aggregatedMarketCap, 5)) for symbol, mktCap in marketCapBySymbol.items()}
        weights.update({symbol :  weight for symbol, weight in weights.items() if weight > 0})
        return weights
        
    
    
    def OnSecuritiesChanged(self, algorithm, changes):

        for security in changes.RemovedSecurities:
            symbol = security.Symbol
            self.removedSymbols.append(symbol)
            self.securities.pop(symbol, None)
        
        for security in changes.AddedSecurities:
            if security.Fundamentals is not None and security.Fundamentals.MarketCap > 0:
                self.securities[security.Symbol] = security
        
        
def GroupBy(iterable, key=lambda x: x):
    d = defaultdict(list)
    for item in iterable:
        d[key(item)].append(item)
    return d.items()
    