import pandas as pd
import numpy as np
import ib_insync as ibi
from src.util.dt_util import mapBarSize
from src.util.log_util import *
from copy import copy


pd.set_option('mode.chained_assignment', None)  # Turn off pandas warning.


class DataInterface(object):

    @Logger('main', 'info')
    def __init__(self):
        self.df = None

    @Logger('main', 'info')
    def update(self, **kwargs):
        pass

    @Logger('main', 'info')
    def set(self, **kwargs):
        pass

    @Logger('main', 'debug')
    def append(self, df):
        if self.df is not None:
            self.df = self.df.append(df, ignore_index=True)
        else:
            self.assignDf(df)

    @Logger('main', 'debug')
    def getDf(self, col=None, val=None):
        if (col is None) and (val is None):
            return self.df
        else:
            return self.df.loc[self.df[col] == val]

    @Logger('main', 'debug')
    def assignDf(self, df):
        self.df = df

    @Logger('main', 'debug')
    def drop(self, col, val):
        self.df.drop(index=self.df.loc[(self.df[col] == val)].index, inplace=True)
        self.df.reset_index(inplace=True, drop=True)


class BarData(DataInterface):

    @Logger('main', 'info')
    def __init__(self, id_, contract, barSize, maxLen, option, isShadow):
        super(BarData, self).__init__()
        self.id           = id_
        self.contract     = contract
        self.barSize      = barSize  # timedelta or relativedelta
        self.maxLen       = maxLen
        self.isShadow     = isShadow
        self.option       = option
        self.barsH        = None
        self.barsR        = None
        self.pxLast       = None
        self.lastDateDf   = None
        self.lastDateBars = None
        self.isActive     = False
        self.isUpdated    = False
        self.isReady      = False
        self.updateTime   = {'isActive':None,
                             'isUpdated':None,
                             'isReady':None,
                             'pxLast':None}

    @Logger('main', 'info')
    def set(self, barType, bars, currentTime):
        self.setBars(barType, bars)
        self.setDf(bars) if self.df is None else self.updateBarsToDf(bars)
        self.updateForNonShadow(currentTime, isInitializing=True)

    @Logger('main', 'debug')
    def setBars(self, barType, bars):
        if barType == 'h':
            self.barsH = bars
        elif barType == 'r':
            self.barsR = bars
        else:
            raise ValueError('Error: Invalid bar type.')

    @Logger('main', 'debug')
    def setDf(self, bars):
        self.assignDf(ibi.util.df(bars))
        self.resizeDf()

    @Logger('main', 'info')
    def update(self, currentTime, parentBarData=None):

        mainLogger.debug(f'Updating bar data for {self.contract.localSymbol}')

        if self.isShadow is False:
            self.updateForNonShadow(currentTime, isInitializing=False)
        else:
            self.updateForShadow(parentBarData)

    @Logger('main', 'debug')
    def updateDf(self, isInitializing):
        if isInitializing is False:
            newBars = self.extractNewBars()
            self.updateBarsToDf(newBars) if self.df is not None else self.setDf(newBars)

    @Logger('main', 'debug')
    def updateBarsToDf(self, bars):
        df = ibi.util.df(bars)
        if df is not None:
            for _ in range(len(df)):
                if df['date'].iloc[0] <= self.df['date'].iloc[-1]:
                    self.df.drop(self.df.tail(1).index, inplace=True)
                else:
                    break
            self.append(df)
            self.resizeDf()

    @Logger('main', 'debug')
    def updateForNonShadow(self, currentTime, isInitializing=False):
        self.updateReadyStatus(currentTime, isInitializing)
        if self.isReady:
            self.updateLastDateBars()
            self.updateDf(isInitializing)
            self.updateUpdateStatus(currentTime, isInitializing)
            self.updateActiveStatus(currentTime)
            self.updateLastDateDf()
            self.updateLastOpenRowInDf()
            self.updateLastDateDf()
            self.updatePxLast(currentTime)

    @Logger('main', 'debug')
    def updateForShadow(self, parentBarData):
        self.df           = parentBarData.df
        self.barsH        = parentBarData.barsH
        self.barsR        = parentBarData.barsR
        self.pxLast       = parentBarData.pxLast
        self.lastDateDf   = parentBarData.lastDateDf
        self.lastDateBars = parentBarData.lastDateBars
        self.isActive     = parentBarData.isActive
        self.isUpdated    = parentBarData.isUpdated
        self.isReady      = parentBarData.isReady
        self.updateTime   = parentBarData.updateTime

    @Logger('main', 'debug')
    def updateReadyStatus(self, currentTime, isInitializing):
        self.isReady = True if isInitializing else (currentTime - self.lastDateBars) >= self.barSize
        self.updateTime['isReady'] = currentTime

        mainLogger.debug(f'isReady:{self.isReady} - currentTime:{currentTime} - lastDateBars:{self.lastDateBars} - barSize:{self.barSize}')

    @Logger('main', 'debug')
    def updateUpdateStatus(self, currentTime, isInitializing):
        if self.df is not None:
            date_0 = self.df['date'].iloc[-1]
            self.isUpdated = True if isInitializing else date_0 > self.lastDateDf

            mainLogger.debug(f'isUpdated:{self.isUpdated} - date_0:{date_0} - lastDateDf:{self.lastDateDf}')

        self.updateTime['isUpdated'] = currentTime

    @Logger('main', 'debug')
    def updateActiveStatus(self, currentTime):
        if self.df is not None:
            self.isActive = (currentTime - self.lastDateBars) < self.barSize

            mainLogger.debug(f'isActive:{self.isActive} - currentTime:{currentTime} - lastDateBars:{self.lastDateBars} - barSize:{self.barSize}')

            # self.isActive = self.lastDateBars > self.lastDateDf
            self.updateTime['isActive'] = currentTime

    @Logger('main', 'debug')
    def updateLastDateBars(self):
        if self.barsR is not None:
            lastDateBars = self.barsR[-1].date
            self.lastDateBars = lastDateBars if self.lastDateBars is None else max(lastDateBars, self.lastDateBars)
        elif self.barsH is not None:
            lastDateBars = self.barsH[-1].date
            self.lastDateBars = lastDateBars if self.lastDateBars is None else max(lastDateBars, self.lastDateBars)

    @Logger('main', 'debug')
    def updateLastDateDf(self):
        if self.df is not None:
            self.lastDateDf = self.df['date'].iloc[-1]

    @Logger('main', 'debug')
    def updateLastOpenRowInDf(self):
        if self.df is not None:
            if self.option in [3, 4]:
                if self.isActive and (self.lastDateBars == self.lastDateDf):
                    self.df.drop(self.df.tail(1).index, inplace=True)

    @Logger('main', 'debug')
    def updatePxLast(self, currentTime):
        if (self.barsR is not None) and (len(self.barsR) > 0):
            self.pxLast = self.barsR[-1]
            self.updateTime['pxLast'] = currentTime
        elif (self.barsH is not None) and (len(self.barsH) > 0):
            self.pxLast = self.barsH[-1]
            self.updateTime['pxLast'] = currentTime

    @Logger('main', 'debug')
    def extractNewBars(self):
        bars = self.barsR
        newBars = list()
        if (bars is not None) and len(bars) > 0:
            if self.df is not None:
                for i in reversed(range(len(bars))):
                    if bars[i].date >= self.lastDateDf:
                        newBars.append(bars[i])
                    else:
                        break
                newBars.reverse()
            else:
                newBars = bars
        return newBars

    @Logger('main', 'debug')
    def resizeDf(self):
        if (self.df is not None) and (len(self.df) > self.maxLen):
            self.df = self.df.iloc[len(self.df) - self.maxLen:, :]
            self.df.reset_index(drop=True, inplace=True)


class FxData(DataInterface):

    @Logger('main', 'info')
    def __init__(self, ib, baseCcy, filePath, updateTimeOut=0):
        super(FxData, self).__init__()
        self.ib = ib
        self.baseCcy = baseCcy
        self.filePath = filePath
        self.updateTimeOut = updateTimeOut

    @Logger('main', 'info')
    def set(self):
        df = pd.read_csv(self.filePath)
        df = df.loc[df['IB SYMBOL'].apply(lambda x: self.baseCcy in x) & df['IS APPLIED'], :]
        df.reset_index(drop=True, inplace=True)
        df['domestic ccy'] = df['IB SYMBOL'].apply(lambda x: x[:3])
        df['foreign ccy' ] = df['IB SYMBOL'].apply(lambda x: x[4:])
        df['symbol'      ] = df['IB SYMBOL'].apply(lambda x: x.replace('.', ''))
        df['contract'    ] = df['symbol'   ].apply(lambda x: self.ib.qualifyContracts(ibi.Forex(x))[0])
        df['ticker'      ] = df['contract' ].apply(lambda x: self.ib.reqMktData(x, snapshot=False))
        df['inverse'     ] = df['domestic ccy'] == self.baseCcy
        df['fx'          ] = np.nan

        idx = df['inverse']
        df['currency'] = df['domestic ccy'].to_list()
        df['currency'].loc[idx] = df['foreign ccy'].loc[idx]
        df['pair'    ] = df['currency'] + self.baseCcy

        col_keep = ['pair', 'contract', 'ticker', 'inverse', 'currency', 'fx']
        df = df[col_keep]

        self.assignDf(df)
        self.update()

        while self.df['fx'].isnull().any():
            self.ib.waitOnUpdate(self.updateTimeOut)
            self.update()

    @Logger('main', 'info')
    def update(self):
        idx = self.df['inverse']
        self.df['fx'] = self.df['ticker'].apply(lambda x: x.marketPrice())
        self.df['fx'].loc[idx] = 1 / self.df['fx'].loc[idx]


class StatusData(DataInterface):

    @Logger('main', 'info')
    def __init__(self, statusType):
        super(StatusData, self).__init__()
        self.df = pd.DataFrame(columns=['contract', 'id', 'status', 'update_time'])
        self.statusType = statusType

    @Logger('main', 'info')
    def set(self, ids, contracts, status, updateTimes):
        ids         = [ids        ] if isinstance(ids,         list) is not True else ids
        contracts   = [contracts  ] if isinstance(contracts,   list) is not True else contracts
        status      = [status     ] if isinstance(status,      list) is not True else status
        updateTimes = [updateTimes] if isinstance(updateTimes, list) is not True else updateTimes

        df = pd.DataFrame({'id':ids,
                           'contract':contracts,
                           'status':status,
                           'update_time':updateTimes})
        self.assignDf(df)

    @Logger('main', 'info')
    def update(self, id_, status, updateTime):
        self.df['status'     ].loc[self.df['id'] == id_] = status
        self.df['update_time'].loc[self.df['id'] == id_] = updateTime


class PxLastData(DataInterface):

    @Logger('main', 'info')
    def __init__(self):
        super(PxLastData, self).__init__()
        self.df = pd.DataFrame(columns=['contract', 'id', 'close', 'px_time', 'update_time'])

    @Logger('main', 'info')
    def set(self, contracts, ids, closes, lastDateBars, updateTimes):
        contracts    = [contracts   ] if isinstance(contracts,    list) is not True else contracts
        ids          = [ids         ] if isinstance(ids,          list) is not True else ids
        closes       = [closes      ] if isinstance(closes,       list) is not True else closes
        lastDateBars = [lastDateBars] if isinstance(lastDateBars, list) is not True else lastDateBars
        updateTimes  = [updateTimes ] if isinstance(updateTimes,  list) is not True else updateTimes

        df = pd.DataFrame({'contract':contracts,
                           'id':ids,
                           'close':closes,
                           'px_time':lastDateBars,
                           'update_time':updateTimes})
        self.assignDf(df)

    @Logger('main', 'info')
    def update(self, id_, close, lastDateBars, updateTime):
        self.df['close'      ].loc[self.df['id'] == id_] = close
        self.df['px_time'    ].loc[self.df['id'] == id_] = lastDateBars
        self.df['update_time'].loc[self.df['id'] == id_] = updateTime


class BarDataRequestor(object):

    @Logger('main', 'info')
    def __init__(self, ib):
        self.ib = ib

    @Logger('main', 'debug')
    def reqConsecutiveBars(self, contract, para, startDate):
        barsList = []
        while True:
            bars = self.ib.reqHistoricalData(contract, **para)
            if bars[0].date <= startDate:
                bars = [bar for bar in bars if bar.date >= startDate] if bars[0].date < startDate else bars
                barsList.append(bars)
                break
            barsList.append(bars)
            para['endDateTime'] = bars[0].date

        barsOut = barsList[-1]
        for bar in reversed(barsList[:-1]):
            barsOut.extend(bar)

        return barsOut

    @Logger('main', 'debug')
    def createBarData(self, id_, contract, para, option, currentTime, startDate=None, updateFunc=None, dfBase=None, maxLen=100000):

        barSize = mapBarSize(para['barSizeSetting'])
        barData = BarData(id_, contract, barSize, maxLen, option, isShadow=False)

        if dfBase is not None:
            barData.df = dfBase

        # Historical bars.
        if option == 1:
            bars = self.ib.reqHistoricalData(contract, **para)
            barData.set('h', bars, currentTime)

        # Consecutive historical bars.
        elif option == 2:
            bars = self.reqConsecutiveBars(contract, para, startDate)
            barData.set('h', bars, currentTime)

        # Historical bars with real-time update.
        elif option == 3:
            assert para['keepUpToDate'], \
                f'Error:MarketData:{self.__class__.__name__}:{inspect.currentframe().f_code.co_name} ' \
                f'- Parameter keepUpToDate needs to be True for real-time request ID-{id_}.'
            bars = self.ib.reqHistoricalData(contract, **para)
            if updateFunc is not None:
                bars.updateEvent += updateFunc
            barData.set('r', bars, currentTime)

        # Consecutive historical bars with real-time update.
        elif option == 4:
            para['keepUpToDate'] = False
            para['endDateTime' ] = ''
            bars = self.reqConsecutiveBars(contract, para, startDate)
            barData.set('h', bars, currentTime)

            para['keepUpToDate'] = True
            para['endDateTime' ] = ''
            bars = self.ib.reqHistoricalData(contract, **para)
            if updateFunc is not None:
                bars.updateEvent += updateFunc
            barData.set('r', bars, currentTime)

        else:
            raise Exception(f'Error:MarketData:{self.__class__.__name__}:{inspect.currentframe().f_code.co_name} - Invalid option for ID-{id_}.')

        return barData


class MarketDataManager(object):
    
    @Logger('main', 'info')
    def __init__(self, agent):
        self.ib               = agent.ib
        self.agent            = agent
        self.config           = None
        self.barDataDict      = None
        self.fxData           = None
        self.activeStatusData = None
        self.updateStatusData = None
        self.readyStatusData  = None
        self.pxLastData       = None
        self.configMarketData = None
        self.configShadowData = None
        self.configFxPairFile = None

    # ------------------------------------- Basic Functions -------------------------------------

    @Logger('main', 'debug')
    def createBarData(self, id_, contract, para, option, startDate=None, updateFunc=None, dfBase=None, maxLen=100000, requestor=None):
        requestor   = BarDataRequestor(self.ib) if requestor is None else requestor
        currentTime = self.agent.currentTime

        self.validatePara(para)
        barData = requestor.createBarData(id_, contract, para, option, currentTime, startDate, updateFunc, dfBase, maxLen)

        return barData

    @Logger('main', 'debug')
    def createBarDataShadow(self, shadowId, contract, marketDataId):

        shadowData = copy(self.barDataDict[marketDataId])
        shadowData.contract = contract
        shadowData.isShadow = True

        self.barDataDict[shadowId] = shadowData

    @Logger('main', 'debug')
    def validatePara(self, para):
        if self.agent.mode == 'backtest':
            assert para['whatToShow'] == 'MIDPOINT'
            assert para['formatDate'] == 2
            assert para['keepUpToDate'] is False

    # ------------------------------------- Initialize -------------------------------------

    @Logger('main', 'info')
    def initialize(self, config):
        self.initializeConfig(config)
        self.initializeAllData()

    @Logger('main', 'debug')
    def initializeConfig(self, config):
        self.config = config
        self.configMarketData = config['MARKET_DATA']
        self.configFxPairFile = config['FX_PAIRS_FILE']
        self.configShadowData = config['SHADOW_DATA']

    @Logger('main', 'debug')
    def initializeAllData(self):
        self.initializeBarData()
        self.initializeBarDataShadow()
        self.initializeFxData()
        self.initializeActiveStatusData()
        self.initializeUpdateStatusData()
        self.initializeReadyStatusData()
        self.initializePxLastData()

    @Logger('main', 'debug')
    def initializeBarData(self):
        self.barDataDict = dict()
        requestor = BarDataRequestor(self.ib)
        for key, val in self.configMarketData.items():

            id_        = val['custom_id']
            contract   = self.agent.ContractManager.getContract(val['contract_id'])
            para       = val['para']
            option     = val['option']
            maxLen     = val['max_len']
            startDate  = val['start_date']
            updateFunc = val['update_func']
            dfBase     = val['df_base']

            self.barDataDict[id_] = self.createBarData(id_, contract, para, option, startDate, updateFunc, dfBase, maxLen, requestor)

            mainLogger.debug(f'Initialized bar data for {contract.localSymbol}')

    @Logger('main', 'debug')
    def initializeBarDataShadow(self):
        for id_, val in self.configShadowData.items():
            contractId   = val['contract_id']
            marketDataId = val['market_data_id']
            contract     = self.agent.ContractManager.getContract(contractId)

            self.createBarDataShadow(id_, contract, marketDataId)

            mainLogger.debug(f'Initialized bar data for {contract.localSymbol}')

    @Logger('main', 'debug')
    def initializeFxData(self):
        baseCcy  = self.agent.baseCcy
        filePath = self.configFxPairFile

        fxData   = FxData(self.ib, baseCcy, filePath, updateTimeOut=0)
        fxData.set()
        self.fxData = fxData

    @Logger('main', 'debug')
    def initializeActiveStatusData(self):
        ids         = list(self.barDataDict.keys())
        contracts   = [self.barDataDict[id_].contract for id_ in ids]
        status      = [self.barDataDict[id_].isActive for id_ in ids]
        updateTimes = [self.barDataDict[id_].updateTime['isActive'] for id_ in ids]

        self.activeStatusData = StatusData('active')
        self.activeStatusData.set(ids, contracts, status, updateTimes)

    @Logger('main', 'debug')
    def initializeUpdateStatusData(self):
        ids         = list(self.barDataDict.keys())
        contracts   = [self.barDataDict[id_].contract for id_ in ids]
        status      = [self.barDataDict[id_].isUpdated for id_ in ids]
        updateTimes = [self.barDataDict[id_].updateTime['isUpdated'] for id_ in ids]

        self.updateStatusData = StatusData('update')
        self.updateStatusData.set(ids, contracts, status, updateTimes)

    @Logger('main', 'debug')
    def initializeReadyStatusData(self):
        ids         = list(self.barDataDict.keys())
        contracts   = [self.barDataDict[id_].contract for id_ in ids]
        status      = [self.barDataDict[id_].isReady for id_ in ids]
        updateTimes = [self.barDataDict[id_].updateTime['isReady'] for id_ in ids]

        self.readyStatusData = StatusData('ready')
        self.readyStatusData.set(ids, contracts, status, updateTimes)

    @Logger('main', 'debug')
    def initializePxLastData(self):
        ids          = list(self.barDataDict.keys())
        contracts    = [self.barDataDict[id_].contract for id_ in ids]
        closes       = list()
        lastDateBars = list()
        updateTimes  = list()

        for id_ in ids:
            pxLast     = self.barDataDict[id_].pxLast
            updateTime = self.barDataDict[id_].updateTime
            if pxLast is not None:
                closes.append(pxLast.close)
                lastDateBars.append(pxLast.date)
                updateTimes.append(updateTime['pxLast'])
            else:
                closes.append(np.nan)
                lastDateBars.append(pd.NaT)
                updateTimes.append(pd.NaT)

        self.pxLastData = PxLastData()
        self.pxLastData.set(contracts, ids, closes, lastDateBars, updateTimes)

    # ------------------------------------- Update -------------------------------------

    @Logger('main', 'info')
    def update(self):
        self.updateBarData()
        self.updateFxData()
        self.updateActiveStatusData()
        self.updateUpdateStatusData()
        self.updateReadyStatusData()
        self.updatePxLastData()

    @Logger('main', 'debug')
    def updateBarData(self):
        currentTime  = self.agent.currentTime
        ids          = list(self.barDataDict.keys())
        idsNonShadow = [id_ for id_ in ids if self.barDataDict[id_].isShadow is False]
        idsShadow    = [id_ for id_ in ids if self.barDataDict[id_].isShadow is True]

        for id_ in idsNonShadow:
            self.barDataDict[id_].update(currentTime)

        for id_ in idsShadow:
            parentId = self.barDataDict[id_].id
            parentBarData = self.barDataDict[parentId]
            self.barDataDict[id_].update(currentTime, parentBarData)

    @Logger('main', 'debug')
    def updateFxData(self):
        self.fxData.update()

    @Logger('main', 'debug')
    def updateActiveStatusData(self):
        for id_ in self.barDataDict.keys():
            status = self.barDataDict[id_].isActive
            updateTime = self.barDataDict[id_].updateTime['isActive']
            self.activeStatusData.update(id_, status, updateTime)

    @Logger('main', 'debug')
    def updateUpdateStatusData(self):
        for id_ in self.barDataDict.keys():
            status = self.barDataDict[id_].isUpdated
            updateTime = self.barDataDict[id_].updateTime['isUpdated']
            self.updateStatusData.update(id_, status, updateTime)

    @Logger('main', 'debug')
    def updateReadyStatusData(self):
        for id_ in self.barDataDict.keys():
            status = self.barDataDict[id_].isReady
            updateTime = self.barDataDict[id_].updateTime['isReady']
            self.readyStatusData.update(id_, status, updateTime)

    @Logger('main', 'debug')
    def updatePxLastData(self):
        for id_ in self.barDataDict.keys():
            pxLast       = self.barDataDict[id_].pxLast
            close        = pxLast.close if pxLast is not None else np.nan
            lastDateBars = pxLast.date  if pxLast is not None else pd.NaT
            updateTime   = self.barDataDict[id_].updateTime['pxLast']
            self.pxLastData.update(id_, close, lastDateBars, updateTime)

    # ------------------------------------- Cancel -------------------------------------

    @Logger('main', 'info')
    def cancelAllDataRequest(self):
        self.cancelAllBarDataRequest()
        self.cancelAllFxDataRequest()

    @Logger('main', 'debug')
    def cancelBarDataRequest(self, id_):
        if self.barDataDict[id_].barsR is not None and self.barDataDict[id_].isShadow is False:
            self.ib.cancelHistoricalData(self.barDataDict[id_].barsR)

    @Logger('main', 'debug')
    def cancelAllBarDataRequest(self):
        for id_ in self.barDataDict.keys():
            self.cancelBarDataRequest(id_)

    @Logger('main', 'debug')
    def cancelFxDataRequest(self, contract):
        self.ib.cancelMktData(contract)

    @Logger('main', 'debug')
    def cancelAllFxDataRequest(self):
        if self.fxData is not None:
            for contract in self.fxData.df['contract']:
                self.cancelFxDataRequest(contract)

    # ------------------------------------- Drop -------------------------------------

    @Logger('main', 'info')
    def dropAllData(self):
        self.dropAllBarData()
        self.dropAllFxData()
        self.dropAllActiveStatusData()
        self.dropAllUpdateStatusData()
        self.dropAllReadyStatusData()
        self.dropAllPxLastData()

    @Logger('main', 'debug')
    def dropBarData(self, id_):
        self.cancelBarDataRequest(id_)
        del self.barDataDict[id_]

        self.dropActiveStatusData(id_)
        self.dropUpdateStatusData(id_)
        self.dropReadyStatusData(id_)
        self.dropPxLastData(id_)

    @Logger('main', 'debug')
    def dropAllBarData(self):
        self.cancelAllBarDataRequest()
        self.barDataDict = None

        self.dropAllActiveStatusData()
        self.dropAllUpdateStatusData()
        self.dropAllReadyStatusData()
        self.dropAllPxLastData()

    @Logger('main', 'debug')
    def dropFxData(self, contract):
        self.cancelFxDataRequest(contract)
        self.fxData.drop('contract', contract)

    @Logger('main', 'debug')
    def dropAllFxData(self):
        self.cancelAllFxDataRequest()
        self.fxData = None

    @Logger('main', 'debug')
    def dropActiveStatusData(self, id_):
        self.activeStatusData.drop('id', id_)

    @Logger('main', 'debug')
    def dropAllActiveStatusData(self):
        self.activeStatusData = None

    @Logger('main', 'debug')
    def dropUpdateStatusData(self, id_):
        self.updateStatusData.drop('id', id_)

    @Logger('main', 'debug')
    def dropAllUpdateStatusData(self):
        self.updateStatusData = None

    @Logger('main', 'debug')
    def dropReadyStatusData(self, id_):
        self.readyStatusData.drop('id', id_)

    @Logger('main', 'debug')
    def dropAllReadyStatusData(self):
        self.readyStatusData = None

    @Logger('main', 'debug')
    def dropPxLastData(self, id_):
        self.pxLastData.drop('id', id_)

    @Logger('main', 'debug')
    def dropAllPxLastData(self):
        self.pxLastData = None

    # ------------------------------------- Reset -------------------------------------

    @Logger('main', 'info')
    def resetAllData(self):
        self.dropAllData()
        self.initializeAllData()

    @Logger('main', 'debug')
    def resetBarData(self, id_):
        self.cancelBarDataRequest(id_)
        requestor  = BarDataRequestor(self.ib)

        val        = self.configMarketData[id_]
        id_        = val['custom_id']
        contract   = self.agent.ContractManager.getContract(val['contract_id'])
        para       = val['para']
        option     = val['option']
        maxLen     = val['max_len']
        startDate  = val['start_date']
        updateFunc = val['update_func']
        dfBase     = self.barDataDict[id_].df    # Inherit existing df.

        self.barDataDict[id_] = self.createBarData(id_, contract, para, option, startDate, updateFunc, dfBase, maxLen, requestor)

    @Logger('main', 'debug')
    def resetAllBarData(self):
        self.dropAllBarData()
        self.initializeBarData()
        self.initializeBarDataShadow()
        self.initializeActiveStatusData()
        self.initializeUpdateStatusData()
        self.initializeReadyStatusData()
        self.initializePxLastData()

    @Logger('main', 'debug')
    def resetAllFxData(self):
        self.dropAllFxData()
        self.initializeFxData()

    @Logger('main', 'debug')
    def resetAllActiveStatusData(self):
        self.dropAllActiveStatusData()
        self.initializeActiveStatusData()

    @Logger('main', 'debug')
    def resetAllUpdateStatusData(self):
        self.dropAllUpdateStatusData()
        self.initializeUpdateStatusData()

    @Logger('main', 'debug')
    def resetAllReadyStatusData(self):
        self.dropAllReadyStatusData()
        self.initializeReadyStatusData()

    @Logger('main', 'debug')
    def resetAllPxLastData(self):
        self.dropAllPxLastData()
        self.initializePxLastData()


if __name__ == '__main__':

    pass
