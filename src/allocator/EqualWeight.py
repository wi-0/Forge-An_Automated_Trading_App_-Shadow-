import pandas as pd
import numpy as np
from src.util.log_util import *


class PortfolioAllocatorBySignal(object):

    @Logger('main', 'info')
    def __init__(self, agent):
        self.agent         = agent
        self.config        = None
        self.id            = ''
        self.dfSignals     = None
        self.dfPort        = None
        self.dfSign        = None
        self.allocation    = dict()
        self.archives      = list()
        self.scope         = ''
        self.minCash       = None
        self.maxWeight     = None
        self.contractScope = list()
        self.signalScope   = list()
        self.targetScope   = list()
        self.minWeightDiff = None
        self.isReady       = False

    # ------------------------------------- Basic Functions -------------------------------------

    @Logger('main', 'debug')
    def filterSignalDf(self, dfSignals):
        if dfSignals is not None:
            return dfSignals.loc[dfSignals['tag'] == self.id, :]

    @Logger('main', 'debug')
    def getScopeBySignals(self):
        if self.dfSignals is not None:
            return self.dfSignals['contract'].unique().tolist()
        else:
            return []

    @Logger('main', 'debug')
    def getScopeByContracts(self):
        if self.dfPort is not None:
            contractPort   = self.dfPort['contract'].loc[self.dfPort['contract'].isin(self.contractScope)].to_list()
            contractActive = [contract for contract in contractPort if self.checkContractStatus(contract)]
        else:
            contractActive = []
        return pd.unique(contractActive + self.signalScope).tolist()

    @Logger('main', 'debug')
    def getScopeByPositions(self):
        if self.dfPort is not None:
            contractPort   = self.dfPort['contract'].to_list()
            contractActive = [contract for contract in contractPort if self.checkContractStatus(contract)]
        else:
            contractActive = []
        return pd.unique(contractActive + self.signalScope).tolist()

    @Logger('main', 'debug')
    def checkContractStatus(self, contract):
        # Check if data is active.
        activeStatusDf = self.agent.MarketDataManager.activeStatusData.getDf('contract', contract)
        isActive       = activeStatusDf['status'].iloc[activeStatusDf['update_time'].argmax()]

        # Check if bar data is updated.
        updateStatusDf = self.agent.MarketDataManager.updateStatusData.getDf('contract', contract)
        isUpdated      = updateStatusDf['status'].iloc[updateStatusDf['update_time'].argmax()]

        return isActive and isUpdated

    @Logger('main', 'debug')
    def getSignDfSignal(self):
        if self.dfSignals is not None:
            dfSign = self.dfSignals[['contract', 'action']]
            dfSign['sign'] = np.nan
            dfSign['sign'].loc[dfSign['action'] == 'BUY'] = 1
            dfSign['sign'].loc[dfSign['action'] == 'SELL'] = -1
            dfSign['sign'].loc[dfSign['action'] == 'CLOSE'] = 0
            return dfSign[['contract', 'sign']]
        else:
            return None

    @Logger('main', 'debug')
    def getSignDfRemainPortScope(self):
        if self.dfPort is not None:
            remainScope = [c for c in self.targetScope if c not in self.signalScope]
            dfSign = self.dfPort[['contract', 'position']].loc[self.dfPort['contract'].isin(remainScope)]
            if len(dfSign) > 0:
                dfSign['sign'] = np.sign(dfSign['position'])
                return dfSign[['contract', 'sign']]
        return None

    @Logger('main', 'debug')
    def getPortAvailable(self):
        baseValue = self.agent.PortfolioManager.baseValue
        avaValue  = baseValue * (1 - self.minCash)  # Fund size after min cash.
        posPortNotInScope, negPortNotInScope = self.getPortNotInScope()
        posAvaPort = avaValue - posPortNotInScope  # Positive portfolio portion available for trading.
        negAvaPort = avaValue - abs(negPortNotInScope)  # Negative portfolio portion available for trading.

        assert (posAvaPort > 0) and (negAvaPort > 0) and (posAvaPort < baseValue) and (negAvaPort < baseValue), \
            'EqualWeight:get_allocation: Invalid portfolio portion available for trading.'

        return posAvaPort, negAvaPort

    @Logger('main', 'debug')
    def getPortNotInScope(self):
        # Get positive and negative current holdings which are outside trading scope.
        if self.dfPort is not None:
            posPortNotInScope = self.dfPort['marketValueBase'].loc[
                (self.dfPort['contract'].isin(self.targetScope) == False) & \
                (self.dfPort['marketValueBase'] > 0)] \
                .sum()
            negPortNotInScope = self.dfPort['marketValueBase'].loc[
                (self.dfPort['contract'].isin(self.targetScope) == False) & \
                (self.dfPort['marketValueBase'] < 0)] \
                .sum()
        else:
            posPortNotInScope = 0
            negPortNotInScope = 0
        return posPortNotInScope, negPortNotInScope

    @Logger('main', 'debug')
    def getTargetPositionNum(self):
        nPos = max((self.dfSign['sign'] == 1).sum(), 1)
        nNeg = max((self.dfSign['sign'] == -1).sum(), 1)
        return nPos, nNeg

    @staticmethod
    @Logger('main', 'debug')
    def aggDf(df, groupCol, aggFunc):
        return df.groupby(df[groupCol]).aggregate(aggFunc)

    # ------------------------------------- Update -------------------------------------

    @Logger('main', 'debug')
    def updateReadyStatus(self):
        self.isReady = (self.dfSignals is not None) and (len(self.dfSignals) > 0)
        msg = len(self.dfSignals) if self.dfSignals is not None else 0

        mainLogger.debug(f'No. of Signals:{msg}')

    @Logger('main', 'debug')
    def updateSignalDf(self):
        dfSignals = self.agent.SignalManager.getSignalDf()
        self.dfSignals = self.filterSignalDf(dfSignals)
        msg = len(self.dfSignals) if self.dfSignals is not None else 0

        mainLogger.debug(f'No. of Signals:{msg}')

    @Logger('main', 'debug')
    def updatePortDf(self):
        self.dfPort = self.agent.PortfolioManager.getDf()

    @Logger('main', 'debug')
    def updateScopes(self):
        self.signalScope = self.getScopeBySignals()

        if self.scope == 'by_signals':
            self.targetScope = self.signalScope

        if self.scope == 'by_contracts':
            self.targetScope = self.getScopeByContracts()

        if self.scope == 'by_positions':
            self.targetScope = self.getScopeByPositions()

    @Logger('main', 'debug')
    def updateSignDf(self):
        dfSignSignal = self.getSignDfSignal()
        dfSignPort   = self.getSignDfRemainPortScope()
        dfSign       = pd.concat([dfSignSignal, dfSignPort])
        dfSign       = dfSign.groupby('contract').agg('sum').reset_index()
        self.dfSign = dfSign

    @Logger('main', 'debug')
    def removeMiscAllocation(self):
        if len(self.allocation) > 0:
            for contract in list(self.allocation.keys()):
                weight        = self.allocation[contract]
                currentWeight = self.agent.PortfolioManager.getCurrentWeight(contract)
                diff          = weight - currentWeight
                if abs(diff) < self.minWeightDiff:
                    del self.allocation[contract]

                    mainLogger.debug(f'Removed allocation for {contract.localSymbol} with {diff} difference from current portfolio weight.')

    @Logger('main', 'debug')
    def createOrders(self):
        for contract, weight in self.allocation.items():
            action, qty = self.agent.PortfolioManager.getMarketOrderInputs(contract, weight)
            if action is not None:
                _ = self.agent.TradeManager.createOrder(contract, action, qty, orderType='market', append=True)

    # ------------------------------------- Reset -------------------------------------

    @Logger('main', 'info')
    def reset(self):
        self.dfSignals   = None
        self.dfPort      = None
        self.dfSign      = None
        self.signalScope = list()
        self.targetScope = list()
        self.allocation  = dict()

    # ------------------------------------- Archive -------------------------------------

    @Logger('main', 'info')
    def archive(self):
        currentTime = self.agent.currentTime

        mainLogger.debug(f'No. of allocations:{len(self.allocation)}')

        self.archives.append((currentTime, self.allocation))


class EqualWeight(PortfolioAllocatorBySignal):

    @Logger('main', 'info')
    def __init__(self, agent):
        super(EqualWeight, self).__init__(agent)

    # ------------------------------------- Basic Functions -------------------------------------

    @Logger('main', 'debug')
    def getEqualWeight(self, posAvaPort, negAvaPort, nPos, nNeg):
        baseValue   = self.agent.PortfolioManager.baseValue
        posEqWeight = posAvaPort / nPos / baseValue
        negEqWeight = negAvaPort / nNeg / baseValue
        allEqWeight = min(posEqWeight, negEqWeight, self.maxWeight)
        return allEqWeight

    # ------------------------------------- Initialize -------------------------------------

    @Logger('main', 'info')
    def initialize(self, config):
        self.initializeConfig(config)
        self.initializeAllocation()

    @Logger('main', 'debug')
    def initializeConfig(self, config):
        self.config        = config
        self.id            = config['CUSTOM_ID']
        self.scope         = config['SCOPE']
        self.minCash       = config['MIN_CASH']
        self.maxWeight     = config['MAX_WEIGHT']
        self.contractScope = self.agent.ContractManager.getAllContracts(config['CONTRACT_SCOPE'])
        self.minWeightDiff = config['MIN_WEIGHT_DIFF']

    @Logger('main', 'debug')
    def initializeAllocation(self):
        if self.agent.mode == 'trade':
            self.update()

    # ------------------------------------- Update -------------------------------------

    @Logger('main', 'info')
    def update(self):
        self.updateSignalDf()
        self.updateReadyStatus()
        if self.isReady:
            self.updatePortDf()
            self.updateScopes()
            self.updateSignDf()
            self.updateAllocation()
            self.removeMiscAllocation()
            self.createOrders()
            self.archive()
            self.reset()

    @Logger('main', 'debug')
    def updateAllocation(self):
        posAvaPort, negAvaPort = self.getPortAvailable()
        nPos      , nNeg       = self.getTargetPositionNum()
        weights                = self.getEqualWeight(posAvaPort, negAvaPort, nPos, nNeg)

        # Sum target weights by contract id.
        self.dfSign['conId' ] = self.dfSign['contract'].apply(lambda x: x.conId)
        self.dfSign['weight'] = self.dfSign['sign'] * weights
        self.dfSign = self.aggDf(self.dfSign, groupCol='conId', aggFunc={'contract': 'first', 'weight': 'sum'})
        self.allocation = dict(zip(self.dfSign['contract'], self.dfSign['weight']))
