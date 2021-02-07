import pandas as pd
import numpy as np
from src.util.dt_util import isWithinPeriod
from src.util.log_util import *


class SingleContractAndBarDataStrategy(object):

    @Logger('main', 'info')
    def __init__(self, agent):
        self.agent               = agent
        self.config              = None
        self.strategyId          = ''
        self.contractId          = ''
        self.marketDataId        = ''
        self.contract            = None
        self.barData             = None
        self.df                  = None
        self.actions             = None
        self.tag                 = ''
        self.lastDateStamp       = None
        self.signals             = list()
        self.archives            = list()
        self.signalCount         = 0
        self.signalValidLatency  = ''
        self.signalValidSurvival = ''
        self.sendInitialSignal   = False
        self.isReady             = False
        self.isInitialized       = False

    # ------------------------------------- Basic Functions -------------------------------------

    @Logger('main', 'debug')
    def processSignals(self, isInitializing=False):
        if len(self.signals) > 0:
            for signal in self.signals:

                if (isInitializing is True) and (self.sendInitialSignal is False):
                    signal['is_valid'] = False
                else:
                    self.stampSignal(signal)

                if signal['is_valid'] is True:
                    self.agent.SignalManager.add([signal])

            self.archive()
            self.reset()

    @Logger('main', 'debug')
    def stampSignal(self, signal):
        signal['create_date'] = self.agent.currentTime
        signal['is_valid'   ] = self.validateSignal(signal)

    @Logger('main', 'debug')
    def validateSignal(self, signal):
        isValidLatency  = isWithinPeriod(signal['create_date'], self.barData.lastDateBars, self.signalValidLatency)
        isValidSurvival = isWithinPeriod(self.barData.lastDateBars, signal['create_date'], self.signalValidSurvival)
        return isValidLatency or isValidSurvival

    @Logger('main', 'info')
    def get(self, attrs=None):
        para = {
            'date': self.df['date'],
            'close': self.df['close']
        }
        if attrs is not None:
            for attr in attrs:
                if attr not in ['date', 'close']:
                    para[attr] = getattr(self, attr)
        return pd.DataFrame(para)

    @Logger('main', 'info')
    def plot(self, attrs=None):
        df = self.get(attrs)
        df.plot.line(x='date')

    # ------------------------------------- Initialize -------------------------------------

    @Logger('main', 'debug')
    def initializeMarketData(self):
        self.barData = self.agent.MarketDataManager.barDataDict[self.marketDataId]
        self.df = self.barData.df
        self.contract = self.agent.ContractManager.getContract(self.contractId)

    # ------------------------------------- Update -------------------------------------

    @Logger('main', 'debug')
    def updateMarketData(self):
        self.barData = self.agent.MarketDataManager.barDataDict[self.marketDataId]
        self.df = self.barData.df

    @Logger('main', 'debug')
    def updateInitializeStatus(self):
        self.isInitialized = True

    @Logger('main', 'debug')
    def updateStrategyReadyStatus(self):
        isActive  = self.barData.isActive
        isUpdated = self.barData.isUpdated
        isReady   = self.barData.isReady
        self.isReady = isActive and isUpdated and isReady

        mainLogger.debug(f'Bar data - isReady:{isReady} - isActive:{isActive} - isUpdated:{isUpdated}')

    @Logger('main', 'debug')
    def updateLastDateStamp(self):
        self.lastDateStamp = self.barData.lastDateDf

    # @Logger('main', 'debug')
    def updateSignal(self, idx=None):
        date_0 = self.barData.lastDateDf if idx is None else self.df['date'].iloc[idx]
        action = self.actions[-1]

        if action is not None:
            self.signalCount += 1
            signalId = self.strategyId + '_' + str(date_0.timestamp()) + '_' + str(self.signalCount)
            signal = self.agent.SignalManager.createSignal(id_=signalId,
                                                           contract=self.contract,
                                                           action=action,
                                                           signalDate=date_0,
                                                           createDate=None,
                                                           tag=self.tag,
                                                           isValid=None)

            mainLogger.debug(f'Created {action} signal for {self.contract.localSymbol} with signal date {date_0}')

            self.signals.append(signal)

    # ------------------------------------- Reset -------------------------------------

    @Logger('main', 'info')
    def reset(self):
        self.signals = list()

    # ------------------------------------- Archive -------------------------------------

    @Logger('main', 'info')
    def archive(self):
        self.archives.extend(self.signals)


class ATRTrailing(SingleContractAndBarDataStrategy):

    @Logger('main', 'info')
    def __init__(self, agent):
        super(ATRTrailing, self).__init__(agent)

        self.trs           = [np.nan, np.nan]
        self.atrs          = None
        self.supports      = None
        self.resists       = None
        self.xLevels       = None
        self.breakOutType  = None
        self.side          = None
        self.xSide         = None
        self.window        = None
        self.multiplier    = None
        self.rangeType     = None

    # ------------------------------------- Basic Functions -------------------------------------

    @staticmethod
    @Logger('main', 'debug')
    def trueRange(close_1, high_0, low_0, high_1=None, low_1=None, rangeType=None):
        # Calculate true range value.
        if rangeType is None:
            return max(high_0 - low_0,
                       abs(high_0 - close_1),
                       abs(low_0 - close_1))

        if rangeType == 'full':
            return max(high_0 - low_0,
                       high_1 - low_1,
                       abs(high_0 - low_1),
                       abs(high_1 - low_0))

    @staticmethod
    @Logger('main', 'debug')
    def trueRangeNp(close, high, low, rangeType=None):
        # Calculate true range array.
        close_1 = close[:-1]
        high_0  = high[1:]
        low_0   = low[1:]

        if rangeType is None:
            return np.maximum.reduce([high_0 - low_0,
                                      np.abs(high_0 - close_1),
                                      np.abs(low_0 - close_1)])

        if rangeType == 'full':
            high_1 = high[:-1]
            low_1  = low[:-1]
            return np.maximum.reduce([high_0 - low_0,
                                      high_1 - low_1,
                                      np.abs(high_0 - low_1),
                                      np.abs(high_1 - low_0)])

    # ------------------------------------- Initialize -------------------------------------

    @Logger('main', 'info')
    def initialize(self, config):
        self.initializeConfig(config)
        self.initializeMarketData()
        self.updateLastDateStamp()
        self.updateStrategyReadyStatus()
        if self.barData.isUpdated:
            self.initializeStrategy()
            self.updateInitializeStatus()
            self.logLevels()
            if self.isReady:
                self.processSignals(isInitializing=True)

    @Logger('main', 'debug')
    def initializeConfig(self, config):
        self.config              = config
        self.strategyId          = config['STRATEGY_ID']
        self.contractId          = config['CONTRACT_ID']
        self.marketDataId        = config['MARKET_DATA_ID']
        self.tag                 = config['TAG']
        self.window              = config['WINDOW']
        self.multiplier          = config['MULTIPLIER']
        self.rangeType           = config['RANGE_TYPE']
        self.signalValidLatency  = config['SIGNAL_VALID_LATENCY']
        self.signalValidSurvival = config['SIGNAL_VALID_SURVIVAL']
        self.sendInitialSignal   = config['SEND_INITIAL_SIGNAL']

    @Logger('main', 'debug')
    def initializeStrategy(self):
        self.supports = [np.nan] * (self.window + 1)
        self.resists  = [np.nan] * (self.window + 1)
        self.xLevels  = [np.nan] * (self.window + 2)
        self.actions  = [None  ] * (self.window + 1)
        
        assert len(self.df) > (self.window + 2)

        high      = self.df['high' ].iloc[:-1].to_numpy()
        low       = self.df['low'  ].iloc[:-1].to_numpy()
        close     = self.df['close'].iloc[:-1].to_numpy()
        tr        = self.trueRangeNp(close, high, low, rangeType=self.rangeType)
        self.trs  = np.append(self.trs, tr).tolist()
        self.atrs = (pd.Series(self.trs).rolling(window=self.window).mean() * self.multiplier).to_list()

        start = np.argmin(np.isnan(self.atrs))
        for i in range(start, len(self.atrs)):

            close_1 = self.df['close'].iloc[i - 1]
            atr_0   = self.atrs[i]

            if i == start:
                self.supports.append(close_1 - atr_0)
                self.resists.append(close_1 + atr_0)
            else:
                self.updateLevel(i)

            self.updateBreakout(i)
            self.updateAction()
            self.updateSignal(i)

    # ------------------------------------- Update -------------------------------------

    @Logger('main', 'info')
    def update(self):
        self.updateMarketData()
        self.updateStrategyReadyStatus()
        if self.barData.isUpdated:
            if self.isInitialized is False:
                self.updateLastDateStamp()
                self.initializeStrategy()
                self.updateInitializeStatus()
                if self.isReady:
                    self.processSignals(isInitializing=True)
            else:
                self.runStrategy()
                self.updateLastDateStamp()
                if self.isReady:
                    self.processSignals(isInitializing=False)
            self.logLevels()

    @Logger('main', 'debug')
    def runStrategy(self):
        lastIdx = np.flatnonzero(self.df['date'] == self.lastDateStamp)[0]

        # If only one data point is updated in barData df.
        if (lastIdx + 1) == (len(self.df) - 1):
            self.runStrategyUpdates()

        # If more than one data point updated in barData df.
        elif (lastIdx + 1) < (len(self.df) - 1):
            for i in range(lastIdx + 1, len(self.df)):
                self.runStrategyUpdates(i)

        elif (lastIdx + 1) == (len(self.df)):
            print('ATRTrailing:update_all: Already updated.')

        else:
            raise ValueError('ATRTrailing:update_all: Invalid lastIdx.')

    @Logger('main', 'debug')
    def runStrategyUpdates(self, i=None):
        self.updateAtr(i)
        self.updateLevel(i)
        self.updateBreakout(i)
        self.updateAction()
        self.updateSignal(i)

    # @Logger('main', 'debug')
    def updateAtr(self, idx=None):
        close_2 = self.df['close'].iloc[-3] if idx is None else self.df['close'].iloc[idx - 2]
        high_1  = self.df['high' ].iloc[-2] if idx is None else self.df['high' ].iloc[idx - 1]
        low_1   = self.df['low'  ].iloc[-2] if idx is None else self.df['low'  ].iloc[idx - 1]
        high_2  = self.df['high' ].iloc[-3] if idx is None else self.df['high' ].iloc[idx - 2]
        low_2   = self.df['low'  ].iloc[-3] if idx is None else self.df['low'  ].iloc[idx - 2]

        tr_0 = self.trueRange(close_2, high_1, low_1, high_2, low_2, rangeType=self.rangeType)
        self.trs.append(tr_0)
        self.atrs.append(np.mean(self.trs[-self.window:]) * self.multiplier)

    # @Logger('main', 'debug')
    def updateLevel(self, idx=None):
        close_1 = self.df['close'].iloc[-2] if idx is None else self.df['close'].iloc[idx - 1]
        atr_0   = self.atrs[-1] if idx is None else self.atrs[idx]

        # Update xLevels
        if self.xSide == 'up':
            self.xLevels.append(self.resists[-1])
            self.xSide = None
        elif self.xSide == 'down':
            self.xLevels.append(self.supports[-1])
            self.xSide = None
        else:
            self.xLevels.append(self.xLevels[-1])

        # Update support and resist.
        if self.side == 'up':
            self.supports.append(max(self.supports[-1], close_1 - atr_0))
            self.resists.append(close_1 + atr_0)
        elif self.side == 'down':
            self.supports.append(close_1 - atr_0)
            self.resists.append(min(self.resists[-1], close_1 + atr_0))
        else:
            self.supports.append(max(self.supports[-1], close_1 - atr_0))
            self.resists.append(min(self.resists[-1], close_1 + atr_0))

    # @Logger('main', 'debug')
    def updateBreakout(self, idx=None):
        close_0 = self.df['close'].iloc[-1] if idx is None else self.df['close'].iloc[idx]
        close_1 = self.df['close'].iloc[-2] if idx is None else self.df['close'].iloc[idx - 1]

        if close_1 < self.resists[-1] < close_0:
            self.side = 'up'
            self.xSide = 'up'
            self.breakOutType = 'resist'
        elif close_1 > self.supports[-1] > close_0:
            self.side = 'down'
            self.xSide = 'down'
            self.breakOutType = 'support'
        elif close_1 < self.xLevels[-1] < close_0:
            self.side = 'up'
            self.breakOutType = 'xLevelUp'
        elif close_1 > self.xLevels[-1] > close_0:
            self.side = 'down'
            self.breakOutType = 'xLevelDown'
        else:
            self.xSide = None
            self.breakOutType = None

    # @Logger('main', 'debug')
    def updateAction(self):
        if self.breakOutType is None:
            action = None
        else:
            if self.breakOutType == 'resist':
                action = 'BUY'
            elif self.breakOutType == 'support':
                action = 'SELL'
            elif self.breakOutType == 'xLevelUp':
                action = 'BUY'
            elif self.breakOutType == 'xLevelDown':
                action = 'SELL'
            else:
                raise ValueError('Error:Unknown breakout type.')
        self.actions.append(action)

    @Logger('main', 'debug')
    def logLevels(self):
        close_0 = self.df['close'].iloc[-1]
        close_1 = self.df['close'].iloc[-2]
        mainLogger.debug(f'ID:{self.strategyId} - '
                         f'action:{self.actions[-1]} - '
                         f'close_0:{close_0:.2f} - '
                         f'close_1:{close_1:.2f} - '
                         f'resist:{self.resists[-1]:.2f} - '
                         f'support:{self.supports[-1]:.2f} - '
                         f'xLevel:{self.xLevels[-1]:.2f} - '
                         f'side:{self.side} - '
                         f'xSide:{self.xSide} - '
                         f'breakOutType:{self.breakOutType}')


if __name__ == '__main__':

    pass
