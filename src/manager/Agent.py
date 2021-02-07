from src.manager.Contract import ContractManager
from src.manager.MarketData import MarketDataManager
from src.manager.Event import EventManager
from src.manager.Portfolio import PortfolioManager
from src.manager.Account import AccountManager
from src.manager.Signal import SignalManager
from src.manager.Trade import TradeManager
from src.util.log_util import *


class Agent(object):

    @Logger('main', 'info')
    def __init__(self, ib):
        self.ib            = ib
        self.config        = None
        self.ip            = ''
        self.socketPort    = None
        self.clientId      = None
        self.baseCcy       = ''
        self.currentTime   = None
        self.minBal        = None
        self.minPnl        = None
        self.sleepTime     = None
        self.bufferTime    = None
        self.startTime     = None
        self.endTime       = None
        self.loopInterval  = None
        self.endingProcess = ''
        self.mode          = ''

        self.AccountManager    = AccountManager(agent=self)
        self.EventManager      = EventManager(agent=self)
        self.ContractManager   = ContractManager(agent=self)
        self.MarketDataManager = MarketDataManager(agent=self)
        self.PortfolioManager  = PortfolioManager(agent=self)
        self.SignalManager     = SignalManager(agent=self)
        self.TradeManager      = TradeManager(agent=self)

    # ------------------------------------- Basic Functions -------------------------------------

    @Logger('main', 'debug')
    def checkConnection(self):
        isConnected = self.EventManager.isIbConnected
        if isConnected is False:
            mainLogger.debug(f'Connection to be re-established...')
            return False
        else:
            return True

    @Logger('main', 'debug')
    def checkStreaming(self):
        if (self.EventManager.isRequestRequired is True) and (self.EventManager.isIbConnected is True):
            self.MarketDataManager.resetAllData()
            self.EventManager.isRequestRequired = False
            return True
        elif (self.EventManager.isRequestRequired is True) and (self.EventManager.isIbConnected is False):
            mainLogger.debug(f'Connection to be re-established...')
            return False
        else:
            return True

    @Logger('main', 'debug')
    def checkNetLiquidity(self):
        minBal = self.minBal
        netLiq = self.AccountManager.netLiq
        if netLiq < minBal:
            mainLogger.debug('Net liquidity less than minimum required balance')
            return False
        else:
            return True

    @Logger('main', 'debug')
    def checkMinPortfolioPnl(self):
        minPnl = self.minPnl
        realizedPnl   = float(self.AccountManager.getAccountDetail(detail='values',
                                                                   filter={'tag': 'RealizedPnL',
                                                                           'currency': self.baseCcy}))
        unrealizedPnl = float(self.AccountManager.getAccountDetail(detail='values',
                                                                   filter={'tag': 'UnrealizedPnL',
                                                                           'currency': self.baseCcy}))
        if minPnl > (realizedPnl + unrealizedPnl):
            mainLogger.debug('Total PnL less than minimum PnL')
            return False
        else:
            return True

    @Logger('main', 'debug')
    def sleep(self, sleepTime=None):
        sleepTime = self.sleepTime if sleepTime is None else sleepTime
        print(f'Sleeping for {sleepTime} seconds.')
        self.ib.sleep(sleepTime)

    @Logger('main', 'debug')
    def connect(self, ip=None, socketPort=None, clientId=None):
        ip         = self.ip if ip is None else ip
        socketPort = self.socketPort if socketPort is None else socketPort
        clientId   = self.clientId if clientId is None else clientId
        self.ib.connect(ip, socketPort, clientId)

    @Logger('main', 'debug')
    def disconnect(self):
        self.MarketDataManager.dropAllData()
        self.TradeManager.cancelOrdersAll()
        self.sleep()
        self.ib.disconnect()

    @Logger('main', 'debug')
    def getLoopingTimePara(self):
        now = datetime.datetime.now()
        date = now.date()
        hour = now.hour
        self.startTime = datetime.datetime.combine(date, datetime.time(hour, 0))
        self.endTime   = self.startTime + datetime.timedelta(weeks=1)

    def bufferIntervalStartTime(self):
        if self.currentTime.second < self.bufferTime:
            self.sleep(self.bufferTime - self.currentTime.second)
            self.currentTime = self.ib.reqCurrentTime()

    # ------------------------------------- Initialize -------------------------------------

    @Logger('main', 'info')
    def initialize(self, config):
        pass

    @Logger('main', 'info')
    def startInitialize(self, config):
        self.initializeConfig(config)
        self.initializeManagers(config)

    @Logger('main', 'info')
    def initializeConfig(self, config):
        self.config        = config['AGENT']
        self.ip            = self.config['IP']
        self.socketPort    = self.config['SOCKET_PORT']
        self.clientId      = self.config['CLIENT_ID']
        self.baseCcy       = self.config['BASE_CCY']
        self.minBal        = self.config['MIN_BALANCE']
        self.minPnl        = self.config['MIN_PORT_PNL']
        self.sleepTime     = self.config['SLEEP_TIME']
        self.bufferTime    = self.config['BUFFER_TIME']
        self.loopInterval  = self.config['LOOP_INTERVAL']
        self.endingProcess = self.config['ENDING_PROCESS']
        self.mode          = self.config['MODE']

    @Logger('main', 'info')
    def initializeManagers(self, config):
        self.connect()
        self.currentTime = self.ib.reqCurrentTime()
        self.bufferIntervalStartTime()

        self.AccountManager.initialize(config['ACCOUNT'])
        self.EventManager.initialize(config['EVENT'])
        self.ContractManager.initialize(config['CONTRACT'])
        self.MarketDataManager.initialize(config['MARKET_DATA'])
        self.PortfolioManager.initialize(config['PORTFOLIO'])
        self.SignalManager.initialize(config['SIGNAL'])
        self.TradeManager.initialize(config['TRADE'])

    @Logger('main', 'info')
    def endInitialize(self):
        # Process for signals and orders from initialization.
        self.SignalManager.update()
        self.TradeManager.update()

    # ------------------------------------- Update -------------------------------------

    @Logger('main', 'info')
    def update(self, **kwargs):
        pass

    @Logger('main', 'info')
    def startUpdate(self):
        print('Start update')

        self.currentTime = self.ib.reqCurrentTime()

        self.maintainConnection()
        self.maintainStreaming()
        self.checkPortfolioValue()
        self.checkPortfolioPnl()

        self.currentTime = self.ib.reqCurrentTime()
        self.bufferIntervalStartTime()

        self.AccountManager.update()
        self.EventManager.update()
        self.ContractManager.update()
        self.MarketDataManager.update()
        self.PortfolioManager.update()

    # ------------------------------------- Routine Checks -------------------------------------

    @Logger('main', 'info')
    def endUpdate(self):
        print('End update')
        self.SignalManager.update()
        self.TradeManager.update()

    @Logger('main', 'debug')
    def maintainConnection(self):
        isConnected = self.checkConnection()
        while isConnected is not True:
            self.ib.waitOnUpdate(10)
            isConnected = self.checkConnection()
            currentTime = self.ib.reqCurrentTime()

            if (isConnected is False) and (currentTime - self.currentTime > datetime.timedelta(seconds=self.loopInterval)):

                mainLogger.warning(f'Wait time exceeds loop interval, terminating...')
                raise Exception('Unable to re-connect within loop interval')

    @Logger('main', 'debug')
    def maintainStreaming(self):
        isStreaming = self.checkStreaming()
        while isStreaming is not True:
            self.ib.waitOnUpdate(10)
            isStreaming = self.checkStreaming()
            currentTime = self.ib.reqCurrentTime()

            if (isStreaming is False) and (currentTime - self.currentTime > datetime.timedelta(seconds=self.loopInterval)):

                mainLogger.warning(f'Wait time exceeds loop interval, terminating...')
                raise Exception('Unable to reset streaming within loop interval')

    @Logger('main', 'debug')
    def checkPortfolioValue(self):
        isMinBal = self.checkNetLiquidity()

        if isMinBal is False:

            mainLogger.warning(f'Portfolio value below minimal balance threshold, terminating...')
            raise Exception('Portfolio value below minimal balance threshold')

    @Logger('main', 'debug')
    def checkPortfolioPnl(self):
        isMinPnl = self.checkMinPortfolioPnl()

        if isMinPnl is False:

            mainLogger.warning(f'Total portfolio P&L below minimal balance threshold, terminating...')
            raise Exception('Total portfolio P&L below minimal balance threshold')

    # ------------------------------------- Execution -------------------------------------

    @Logger('main', 'info')
    def run(self, config):
        self.initialize(config)
        self.getLoopingTimePara()

        for t in self.ib.timeRange(self.startTime, self.endTime, self.loopInterval):

            try:
                mainLogger.info(f'Start processing interval at {t}....')

                self.sleep(self.bufferTime)
                self.update()

                mainLogger.info(f'Interval process completed, waiting to start the next interval...')

            except KeyboardInterrupt:

                mainLogger.info(f'Process interrupted by user.')

                self.TradeManager.cancelOrdersAll()

                if self.endingProcess == 'disconnect':
                    self.disconnect()

                if self.endingProcess == 'cancel':
                    self.MarketDataManager.cancelAllDataRequest()
                    self.sleep()

                mainLogger.info(f'Process ended by User')

            except Exception as e:

                self.TradeManager.cancelOrdersAll()
                self.MarketDataManager.cancelAllDataRequest()
                self.sleep()
                self.disconnect()

                mainLogger.info(f'Process ended with exception')

                raise e
