from AlgorithmImports import *
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')
mpl.style.use('dark_background')
mpl.rcParams.update({'axes.grid': True, 'grid.color': 'grey', 'grid.linestyle': '-', 'grid.linewidth': .3})
mpl.rcParams['axes.linewidth'] = .2


class BacktestAnalyzer:

    def __init__(self, backtest):
        self.backtest = backtest
        self.qb = QuantBook()
        self.start = backtest.TotalPerformance.TradeStatistics.StartDateTime.date()
        self.end = backtest.TotalPerformance.TradeStatistics.EndDateTime.date()
        # prep data
        self.closedTrades = pd.DataFrame([(trade.Symbol, trade.ProfitLoss) for trade in  self.backtest.TotalPerformance.ClosedTrades], columns=['Ticker', 'PnL'])
        self.symbols = self.closedTrades.Ticker.unique().tolist()
        self.closedTrades.loc[:,'Name'] = self.closedTrades.Ticker.map(self.GetCompanyName(self.symbols))
        self.efficiencyScore = self.GetEfficiencyScoreHistory()
        self.efficiencyScoreTreshold = .4
        self.portfolioHistory = self.GetPortfolioHistory()


    def GetCompanyName(self, symbols):
        return self.qb.GetFundamental(symbols, 'CompanyReference.StandardName', datetime.now()-timedelta(1), datetime.now()).iloc[-1] \
                                .rename(SymbolCache.GetSymbol, axis=0) \
                                .str.split().apply(lambda x: x[0]).to_dict()

    def PlotBiggestWinnersAndLosers(self):
        green = (32/255, 142/255, 8/255)
        red = (185/255, 18/255, 22/255)
    
        plt.figure(figsize=(15, 8))
        ax = self.closedTrades.groupby('Name').PnL.sum().nlargest(20)[::-1].plot.barh(color=green, alpha=1)
        ax.set_title('Biggest Winners by accumulative PnL', fontsize=16, fontweight='bold', pad=25)
        ax.set_ylabel('')
        ax.set_xlabel('Profit/Loss in USD', fontsize=14, labelpad=20)
        ax.yaxis.set_tick_params(labelsize=12)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(.5)
        ax.spines['bottom'].set_linewidth(.5)
        ax.grid(which='both', alpha=.3)
        plt.show()
    
        plt.figure(figsize=(15, 8))
        ax = self.closedTrades.groupby('Name').PnL.sum().nsmallest(20).pipe(lambda x: x[x<0]).plot.barh(color=red)
        ax.set_title('Biggest Losers by accumulative PnL', fontsize=16, fontweight='bold', pad=25)
        ax.set_ylabel('')
        ax.set_xlabel('Profit/Loss in USD', fontsize=14, labelpad=20)
        ax.yaxis.set_tick_params(labelsize=12)
        ax.invert_xaxis()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(.5)
        ax.spines['bottom'].set_linewidth(.5)
        ax.grid(which='both', alpha=.3)
        plt.show()


    def GetEfficiencyScoreHistory(self):
        fcfYield = self.qb.GetFundamental(self.symbols, 'ValuationRatios.FCFYield', self.start, self.end)
        revenueGrowth = self.qb.GetFundamental(self.symbols, 'OperationRatios.RevenueGrowth.Value', self.start, self.end)
        return fcfYield + revenueGrowth

    def GetPortfolioHistory(self):
        if self.qb.ObjectStore.ContainsKey('portfolioHistory'):
            portfolioHistory = pd.read_json(self.qb.ObjectStore.Read('portfolioHistory'), orient='split').fillna(0)
            return portfolioHistory

    def PlotEfficiencyScoreVsFwd12MonthsReturns(self):
        dfList = []
        for symbol in self.symbols:
            if symbol.ID.ToString() not in self.efficiencyScore.columns:
                continue
            history = self.qb.History([symbol], self.start, self.end, Resolution.Daily).close.unstack().transpose()
            history.asfreq('Y', method='bfill').pct_change().fillna(0, limit=1).shift(-1).fillna(0, limit=1)
            ef_score = self.efficiencyScore.loc[:,symbol]
            df = pd.concat([history.asfreq('Y', method='bfill').pct_change().fillna(0, limit=1).shift(-1).fillna(0, limit=1), \
                        ef_score.asfreq('Y', method='bfill').pipe(replace_by_iloc, -1, 0)], \
                        axis=1) 
            df.columns = ['Fwd12MonthsReturns', 'EfficiencyScore']
            dfList.append(df)
    
        df = pd.concat(dfList, ignore_index=True).dropna() #.clip(lower=-1, upper=1)
        X = df.EfficiencyScore.clip(lower=-1, upper=2).to_numpy().reshape(-1,1)
        y = df.Fwd12MonthsReturns.clip(lower=-1, upper=1).to_numpy().reshape(-1,1)
        lm = LinearRegression()
        lm.fit(X,y)
        y_pred = lm.predict(X)
        lmDf = pd.DataFrame(y_pred.squeeze(), index=X.squeeze(), columns=['y_pred']).reset_index().rename({'index':'EfficiencyScore'}, axis=1)
        
        fig, ax = plt.subplots(figsize=(20,10))
        ax = df.plot.scatter(x='EfficiencyScore', y='Fwd12MonthsReturns', marker='o', s=50, alpha=.7, ax=ax)
      
        ax = lmDf.sort_values(by='EfficiencyScore').plot.line(x='EfficiencyScore', y='y_pred', linewidth=3, alpha=.5, ax=ax, legend=None)
        ax.set_xlim([-1,2])
        ax.set_ylim([-1, 10])
        ax.set_title('Efficiency Score vs Forward 12 Months Returns', fontsize=16, fontweight='bold', pad=35)
        ax.xaxis.labelpad = 20
        ax.yaxis.labelpad=20
        plt.grid(alpha=.3)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_linewidth(.5)
        ax.spines['left'].set_linewidth(.5)
        ax.tick_params(axis='both', pad=10)
        ax.set_ylabel('Forward 12 Months Returns', fontsize=12)
        ax.set_xlabel('Efficiency Score', fontsize=12)
        plt.show()
    
    def PlotSummaryBySymbol(self, symbol):
        start, end = self.portfolioHistory.iloc[np.where(self.portfolioHistory.loc[:,symbol.ID.ToString()] != 0)[0][[-1,0]]].index.date
        start -= timedelta(30)
        start = max(self.start, start)
        end += timedelta(30)
        end = min(end, self.end)
        priceHistory = self.qb.History([symbol], start, end, Resolution.Daily).close.unstack().transpose().pct_change().fillna(0, limit=1).add(1).cumprod().sub(1)
        
        fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=(20,12), gridspec_kw={'height_ratios':[3,1]}, sharex=True)
        priceHistory.plot(color='white', linewidth=3, ax=ax1)
        
        yellow = tuple(x/255 for x in (254, 221, 0))
        self.portfolioHistory.loc[:,symbol].plot(color=yellow, alpha=.1, linewidth=3, secondary_y=True, label='Weight', ax=ax1)
        ax1.right_ax.set_ylabel('Portfolio Weight', fontsize=10)
        self.efficiencyScore.loc[start:end,symbol].plot(ax=ax2, color='purple', alpha=.5)
        ax2.axhline(self.efficiencyScoreTreshold, color='white', linewidth=5, alpha=.1)
        
        ax1.set_title('Price History, Portfolio Weighting and Efficiency Score', fontsize=16, fontweight='bold', pad=25)
        ax1.set_ylabel('Returns', fontsize=10)
        lines = ax1.get_lines() + ax1.right_ax.get_lines()
        x,y = lines[1].get_xydata()[:,0], lines[1].get_xydata()[:,1]
        ax1.right_ax.fill_between(x,y, color='yellow', alpha=.1)
        ax1.yaxis.labelpad = 20
        ax1.right_ax.yaxis.labelpad = 20
        ax1.legend(lines, [[*self.GetCompanyName(symbol).values()][0], 'Portfolio Weight'], loc='upper left', frameon=True).legendHandles[1].set_alpha(.3)
        ax1.spines['top'].set_visible(False)
        ax1.spines['bottom'].set_linewidth(.5)
        ax1.spines['left'].set_linewidth(.5)
        ax1.spines['right'].set_linewidth(.5)
        ax1.grid(which='both', alpha=.2)
        ax1.right_ax.grid(which='both', alpha=.2)
        lines = ax2.get_lines()
        x, y = lines[0].get_xydata()[:,0], lines[0].get_xydata()[:,1]
        ax2.fill_between(x, self.efficiencyScoreTreshold, y, color='pink', alpha=.2, where=(y >= self.efficiencyScoreTreshold))
        ax2.fill_between(x, self.efficiencyScoreTreshold, y,  color='red', alpha=.2, where=(y < self.efficiencyScoreTreshold))
        # ax2.set_ylim([min(0, ax2.get_ylim()[0]), ax2.get_ylim()[1]])
        ax2.legend(['Efficiency Score']).legendHandles[0].set_alpha(1)
        ax2.spines['left'].set_linewidth(.5)
        ax2.spines['bottom'].set_linewidth(.5)
        ax2.spines['right'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.grid(which='both', alpha=.2)
        plt.show()
        
        
    def GetBiggestWinner(self):
        return self.closedTrades.groupby('Ticker').PnL.sum().nlargest(1).index[0]

    def GetBiggestLoser(self):
        return self.closedTrades.groupby('Ticker').PnL.sum().nsmallest(1).index[0]

def replace_by_iloc(s, idx, value):
    s.iloc[idx] = value
    return s

