
# --------------------------- Agent Config -----------------------------

CONFIG_AGENT = {
    'IP'            : '127.0.0.1',
    'SOCKET_PORT'   : 7497,
    'CLIENT_ID'     : 10,
    'BASE_CCY'      : 'USD',
    'MIN_BALANCE'   : 100000,
    'MIN_PORT_PNL'  : -10000,
    'SLEEP_TIME'    : 2,
    'BUFFER_TIME'   : 5,
    'LOOP_INTERVAL' : 60,           # Seconds
    'ENDING_PROCESS': 'cancel',     # 'cancel' or 'disconnect'
    'MODE'          : 'trade',      # 'trade' or 'backtest'
}

# --------------------------- Config - Account Manager -----------------------------

CONFIG_ACCOUNT = {
    'ACCOUNT': 'yourAccountId'
}

# --------------------------- Config - Contract Manager -----------------------------

CONTRACTS = {
    'EUR.USD_CFD':
        {
            'sec_type': 'CFD',
            'para'    : {'localSymbol': 'EUR.USD'}
        },
    'GBP.USD_CFD':
        {
            'sec_type': 'CFD',
            'para': {'localSymbol': 'GBP.USD'}
        },
    'EUR.USD':
        {
            'sec_type': 'Forex',
            'para'    : {'pair': 'EURUSD'}
        },
    'GBP.USD':
        {
            'sec_type': 'Forex',
            'para': {'pair': 'GBPUSD'}
        }
}
CONFIG_CONTRACT = {
    'CONTRACTS': CONTRACTS
}
# --------------------------- Config - Market Data Manager -----------------------------

PARA_H = {
    'endDateTime'   : '',
    'durationStr'   : '1 D',
    'barSizeSetting': '1 min',
    'whatToShow'    : 'MIDPOINT',
    'useRTH'        : True,
    'formatDate'    : 2,
    'keepUpToDate'  : False
}
PARA_R = {
    'endDateTime'   : '',
    'durationStr'   : '1 D',
    'barSizeSetting': '1 min',
    'whatToShow'    : 'MIDPOINT',
    'useRTH'        : True,
    'formatDate'    : 2,
    'keepUpToDate'  : True
}
MARKET_DATA = {
    'EUR.USD':
        {
            'custom_id'  : 'EUR.USD',
            'contract_id': 'EUR.USD',
            'para'       : PARA_R,
            'option'     : 3,
            'start_date' : None,
            'update_func': None,
            'df_base'    : None,
            'max_len'    : 100000,
         },
    'GBP.USD':
        {
            'custom_id'  : 'GBP.USD',
            'contract_id': 'GBP.USD',
            'para'       : PARA_R,
            'option'     : 3,
            'start_date' : None,
            'update_func': None,
            'df_base'    : None,
            'max_len'    : 100000,
        }
}
FX_PAIRS_FILE = r'C:\Users\USER\PycharmProjects\Forge\statics\FX_Symbols.csv'
SHADOW_DATA = {
    'EUR.USD_CFD':
        {
            'contract_id'   : 'EUR.USD_CFD',
            'market_data_id': 'EUR.USD'
        },
    'GBP.USD_CFD':
        {
            'contract_id'   : 'GBP.USD_CFD',
            'market_data_id': 'GBP.USD'
        },
}
CONFIG_MARKET_DATA = {
    'MARKET_DATA'  : MARKET_DATA,
    'SHADOW_DATA'  : SHADOW_DATA,
    'FX_PAIRS_FILE': FX_PAIRS_FILE,
}

# --------------------------- Config - Event Manager -----------------------------

EVENT_SWITCH = {
    'onError':            True,
    'onConnected':        True,
    'onDisconnected':     True,
    'onUpdate':           False,
    'onPendingTickers':   False,
    'onBarUpdate':        False,
    'onNewOrder':         True,
    'onOrderModify':      True,
    'onCancelOrder':      True,
    'onOpenOrder':        True,
    'onOrderStatus':      True,
    'onExecDetails':      True,
    'onCommissionReport': False,
    'onUpdatePortfolio':  False,
    'onPosition':         False,
    'onAccountValue':     False,
    'onAccountSummary':   False,
    'onPnl':              False,
    'onPnlSingle':        False,
    'onTickNews':         False,
    'onNewsBulletin':     False,
    'onScannerData':      False,
    'onTimeout':          False
}

CONFIG_EVENT = {
    'SWITCH': EVENT_SWITCH
}

# --------------------------- Config - Portfolio -----------------------------

CONFIG_PORTFOLIO = {
    'VALUE_BASIS': 'net_liq'
}

# --------------------------- Config - Signal -----------------------------

CONFIG_SIGNAL = None

# --------------------------- Config - Trade -----------------------------

CONFIG_TRADE = {
    'IS_CANCEL_OPEN_TRADE'   : True,
    'OPEN_TRADE_VALID_PERIOD': '15 mins',
}

# --------------------------- Config - ATRTrailing 1 -----------------------------

CONFIG_ATR_TRAILING_1 = {
    'STRATEGY_ID'          : 'ATRTrailing1',
    'CONTRACT_ID'          : 'EUR.USD_CFD',
    'MARKET_DATA_ID'       : 'EUR.USD_CFD',
    'TAG'                  : 'EW1',
    'WINDOW'               : 14,
    'MULTIPLIER'           : 3,
    'RANGE_TYPE'           : 'full',    # full or None
    'SIGNAL_VALID_LATENCY' : PARA_R['barSizeSetting'],
    'SIGNAL_VALID_SURVIVAL': '1 day',
    'SEND_INITIAL_SIGNAL'  : True,
}
CONFIG_ATR_TRAILING_2 = {
    'STRATEGY_ID'          : 'ATRTrailing2',
    'CONTRACT_ID'          : 'GBP.USD_CFD',
    'MARKET_DATA_ID'       : 'GBP.USD_CFD',
    'TAG'                  : 'EW1',
    'WINDOW'               : 14,
    'MULTIPLIER'           : 3,
    'RANGE_TYPE'           : 'full',    # full or None
    'SIGNAL_VALID_LATENCY' : PARA_R['barSizeSetting'],
    'SIGNAL_VALID_SURVIVAL': '1 day',
    'SEND_INITIAL_SIGNAL'  : False,
}
# --------------------------- Config - EqualWeight Allocator -----------------------------

CONTRACT_SCOPE_ID = ['EUR.USD_CFD', 'GBP.USD_CFD']
CONFIG_EQUAL_WEIGHT = {
    'CUSTOM_ID'      : 'EW1',
    'SCOPE'          : 'by_signals',     # by_signals / by_contracts / by_positions
    'MIN_CASH'       : 0.2,              # % of minimum cash in portfolio
    'MAX_WEIGHT'     : 0.1,              # % of maximum position weight
    'CONTRACT_SCOPE' : CONTRACT_SCOPE_ID,
    'MIN_WEIGHT_DIFF': 0.02,
}

# --------------------------- Config - Master -----------------------------

CONFIG_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
        'simpleFormatter': {
            'format': '%(asctime)s %(name)s - %(levelname)s:%(message)s'
        },
    },
    'handlers': {
        'consoleHandler': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simpleFormatter',
            'stream': 'ext://sys.stdout'
        },
        'fileHandler': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': r'C:\Users\USER\PycharmProjects\Forge\log\default.log'
        },
    },
    'loggers': {
        'root': {
            'level': 'DEBUG',
            'handlers': ['fileHandler']
        },
        'ib_insync.ib': {
            'level': 'DEBUG',
            'handlers': ['fileHandler']
        },
        'ib_insync.client': {
            'level': 'INFO',
            'handlers': ['fileHandler']
        },
        'ib_insync.wrapper': {
            'level': 'DEBUG',
            'handlers': ['fileHandler']
        },
        'main': {
            'level': 'DEBUG',
            'handlers': ['consoleHandler', 'fileHandler']
        },
    }
}

# --------------------------- Config - Master -----------------------------

CONFIG_MASTER = {
    # Basic config.
    'AGENT'      : CONFIG_AGENT,
    'ACCOUNT'    : CONFIG_ACCOUNT,
    'EVENT'      : CONFIG_EVENT,
    'CONTRACT'   : CONFIG_CONTRACT,
    'MARKET_DATA': CONFIG_MARKET_DATA,
    'PORTFOLIO'  : CONFIG_PORTFOLIO,
    'SIGNAL'     : CONFIG_SIGNAL,
    'TRADE'      : CONFIG_TRADE,
    'LOGGING'    : CONFIG_LOGGING,

    # Specialized config.
    'ATR_TRAILING_1': CONFIG_ATR_TRAILING_1,
    'ATR_TRAILING_2': CONFIG_ATR_TRAILING_2,

    'EQUAL_WEIGHT'  : CONFIG_EQUAL_WEIGHT,
}
