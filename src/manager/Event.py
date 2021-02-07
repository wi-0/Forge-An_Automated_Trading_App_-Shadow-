import ib_insync as ibi
import datetime
from src.util.log_util import *


class EventManager(object):

    @Logger('main', 'info')
    def __init__(self, agent):
        self.ib = agent.ib
        self.agent = agent
        self.config = None
        self.switch = None

        # Status attributes.
        self.isIbConnected     = None
        self.isRequestRequired = False
        self.isFarmConnected   = None

    # ------------------------------------- Basic Functions -------------------------------------

    # These are logged by ib_insync.

    def onError(self, reqId, errorCode, errorString, contract):

        if self.switch['onError'] is False:
            pass

        contract = contract.localSymbol if contract is not None else None
        print(f'{datetime.datetime.now()} - Error - {reqId} - {errorCode} - {contract} - {errorString}')

        if errorCode in [1100, 2110, 10182]:
            self.isIbConnected = False
            self.isRequestRequired = True

        if errorCode in [1101, 1102]:
            self.isIbConnected = True

        # if errorCode in [2103, 2105]:
        #     self.farm_connected = False
        #
        # if errorCode in [2104, 2106]:
        #     self.farm_connected = True

    def onConnected(self):
        if self.switch['onConnected'] is False:
            pass
        print(f'{datetime.datetime.now()} - IB connected by user.')

    def onDisconnected(self):
        if self.switch['onDisconnected'] is False:
            pass
        print(f'{datetime.datetime.now()} - IB disconnected by user.')

    def onUpdate(self):
        if self.switch['onUpdate'] is False:
            pass
        pass

    def onPendingTickers(self, tickers):
        if self.switch['onPendingTickers'] is False:
            pass
        pass

    def onBarUpdate(self, bars, hasNewBar):
        if self.switch['onBarUpdate'] is False:
            pass
        pass

    def onNewOrder(self, trade):
        if self.switch['onNewOrder'] is False:
            pass
        order = trade.order
        symbol = trade.contract.localSymbol
        action = order.action
        orderType = order.orderType
        qty = order.totalQuantity
        ccy = trade.contract.currency
        price = str(order.lmtPrice) + ' ' + ccy if orderType == 'LMT' else ''
        print(f'{datetime.datetime.now()} - New order - {action} {qty} {symbol} @ {orderType} {price}')

    def onOrderModify(self, trade):
        if self.switch['onOrderModify'] is False:
            pass
        order = trade.order
        symbol = trade.contract.localSymbol
        action = order.action
        orderType = order.orderType
        qty = order.totalQuantity
        ccy = trade.contract.currency
        price = str(order.lmtPrice) + ' ' + ccy if orderType == 'LMT' else ''
        print(f'{datetime.datetime.now()} - Modify order - {action} {qty} {symbol} @ {orderType} {price}')

    def onCancelOrder(self, trade):
        if self.switch['onCancelOrder'] is False:
            pass
        order = trade.order
        symbol = trade.contract.localSymbol
        action = order.action
        orderType = order.orderType
        qty = order.totalQuantity
        ccy = trade.contract.currency
        price = str(order.lmtPrice) + ' ' + ccy if orderType == 'LMT' else ''
        print(f'{datetime.datetime.now()} - Cancel order - {action} {qty} {symbol} @ {orderType} {price}')

    def onOpenOrder(self, trade):
        if self.switch['onOpenOrder'] is False:
            pass
        order = trade.order
        symbol = trade.contract.localSymbol
        action = order.action
        orderType = order.orderType
        qty = order.totalQuantity
        ccy = trade.contract.currency
        price = str(order.lmtPrice) + ' ' + ccy if orderType == 'LMT' else ''
        print(f'{datetime.datetime.now()} - Open order - {action} {qty} {symbol} @ {orderType} {price}')

    def onOrderStatus(self, trade):
        if self.switch['onOrderStatus'] is False:
            pass
        order = trade.order
        symbol = trade.contract.localSymbol
        action = order.action
        orderType = order.orderType
        qty = order.totalQuantity
        ccy = trade.contract.currency
        price = str(order.lmtPrice) + ' ' + ccy if orderType == 'LMT' else ''
        print(f'{datetime.datetime.now()} - Order status update: {trade.orderStatus.status} - {action} {qty} {symbol} @ {orderType} {price}')

    def onExecDetails(self, trade, fill):
        if self.switch['onExecDetails'] is False:
            pass
        order = trade.order
        symbol = trade.contract.localSymbol
        action = order.action
        orderType = order.orderType
        qty = order.totalQuantity
        ccy = trade.contract.currency
        price = str(order.lmtPrice) + ' ' + ccy if orderType == 'LMT' else ''
        # cum_qty = fill.execution.cumQty
        filledPrice = str(fill.execution.price) + ' ' + ccy
        print(f'{datetime.datetime.now()} - Filled - Qty: {qty} @ {filledPrice} - {action} {qty} {symbol} @ {orderType} {price}')

    def onCommissionReport(self, trade, fill, report):
        if self.switch['onCommissionReport'] is False:
            pass
        pass

    def onUpdatePortfolio(self, item):
        if self.switch['onUpdatePortfolio'] is False:
            pass
        pass

    def onPosition(self, position):
        if self.switch['onPosition'] is False:
            pass
        pass

    def onAccountValue(self, value):
        if self.switch['onAccountValue'] is False:
            pass
        pass

    def onAccountSummary(self, value):
        if self.switch['onAccountSummary'] is False:
            pass
        pass

    def onPnl(self, entry):
        if self.switch['onPnl'] is False:
            pass
        pass

    def onPnlSingle(self, entry):
        if self.switch['onPnlSingle'] is False:
            pass
        pass

    def onTickNews(self, news):
        if self.switch['onTickNews'] is False:
            pass
        pass

    def onNewsBulletin(self, bulletin):
        if self.switch['onNewsBulletin'] is False:
            pass
        pass

    def onScannerData(self, data):
        if self.switch['onScannerData'] is False:
            pass
        pass

    def onTimeout(self, idlePeriod):
        if self.switch['onTimeout'] is False:
            pass
        pass

    # ------------------------------------- Initialize -------------------------------------

    @Logger('main', 'info')
    def initialize(self, config):
        self.config = config
        self.switch = config['SWITCH']

        # Event handlers.
        self.ib.errorEvent            += self.onError
        self.ib.connectedEvent        += self.onConnected
        self.ib.disconnectedEvent     += self.onDisconnected
        self.ib.updateEvent           += self.onUpdate
        self.ib.pendingTickersEvent   += self.onPendingTickers
        self.ib.barUpdateEvent        += self.onBarUpdate
        self.ib.newOrderEvent         += self.onNewOrder
        self.ib.orderModifyEvent      += self.onOrderModify
        self.ib.cancelOrderEvent      += self.onCancelOrder
        self.ib.openOrderEvent        += self.onOpenOrder
        self.ib.orderStatusEvent      += self.onOrderStatus
        self.ib.execDetailsEvent      += self.onExecDetails
        self.ib.commissionReportEvent += self.onCommissionReport
        self.ib.updatePortfolioEvent  += self.onUpdatePortfolio
        self.ib.positionEvent         += self.onPosition
        self.ib.accountValueEvent     += self.onAccountValue
        self.ib.accountSummaryEvent   += self.onAccountSummary
        self.ib.pnlEvent              += self.onPnl
        self.ib.pnlSingleEvent        += self.onPnlSingle
        self.ib.tickNewsEvent         += self.onTickNews
        self.ib.newsBulletinEvent     += self.onNewsBulletin
        self.ib.scannerDataEvent      += self.onScannerData
        self.ib.timeoutEvent          += self.onTimeout

    # ------------------------------------- Update -------------------------------------

    @Logger('main', 'info')
    def update(self):
        pass


if __name__ == '__main__':

    pass

    '''
        2103 Market data farm connection is broken:cashfarm
        2105 HMDS data farm connection is broken
        10182 Failed to request live updates (disconnected)
    
        1100  Connectivity between IB and Trader Workstation has been lost
    
        2104 Market data farm connection is OK:hfarm
        2157 - None - Sec-def data farm connection is broken:secdefhk
        2158 Sec-def data farm connection is OK:secdefhk
        2106 HMDS data farm connection is OK:euhmds
    
        1102 Connectivity between IB and Trader Workstation has been restored - data maintained.
            The following farms are connected: usfarm.nj; hfarm; jfarm; eufarm; cashfarm; usfarm; euhmds; cashhmds; hkhmds; ushmds; fundfarm; secdefhk.
            The following farms are not connected: usfuture.
    
        366 No historical data query found for ticker id:32
        162 Historical Market Data Service error message:API historical data query cancelled
    '''

