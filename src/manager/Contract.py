import pandas as pd
import ib_insync as ibi
from src.util.log_util import *


class ContractManager(object):

    sec_types = (
        'Stock',
        'Option',
        'Future',
        'ContFuture',
        'Forex',
        'Index',
        'CFD',
        'Commodity',
        'Bond',
        'FuturesOption',
        'MutualFund',
        'Warrant',
        'Bag'
    )

    @Logger('main', 'info')
    def __init__(self, agent):
        self.ib        = agent.ib
        self.agent     = agent
        self.config    = None
        self.contracts = None
        self.contractDetail  = None
        self.configContracts = None

    # ------------------------------------- Basic Functions -------------------------------------

    @Logger('main', 'debug')
    def getContract(self, id_):
        return self.contracts[id_][0]

    @Logger('main', 'debug')
    def getAllContracts(self, ids=None):
        ids = list(self.contracts.keys()) if ids is None else ids
        return [self.getContract(id_) for id_ in ids]

    @Logger('main', 'debug')
    def getAllContractsAsDf(self):
        ids = list(self.contracts.keys())
        contracts = [self.getContract(id_) for id_ in ids]
        return pd.DataFrame({'id':ids, 'contract':contracts})

    @Logger('main', 'debug')
    def createContract(self, id_, secType, para):
        contracts = self.ib.qualifyContracts(getattr(ibi.contract, secType)(**para))
        self.validateContract(id_, contracts)
        self.contracts[id_] = contracts

    @Logger('main', 'debug')
    def createContractDetail(self, id_, contracts):
        details = list()
        for contract in contracts:
            details.extend(self.ib.reqContractDetails(contract))
        self.contractDetail[id_] = details

    @Logger('main', 'debug')
    def setContract(self, id_, contract):
        self.contracts[id_] = self.ib.qualifyContracts(contract)

    @Logger('main', 'debug')
    def validateContract(self, id_, contractList):
        assert len(contractList) > 0, \
            f'Error:Contract:{self.__class__.__name__}:{inspect.currentframe().f_code.co_name} - No contract for ID-{id_}.'

        if id_ in list(self.contracts.keys()):
            print(
                f'Warning:Contract:{self.__class__.__name__}:{inspect.currentframe().f_code.co_name} - Duplicated custom ID-{id_}.')

    # ------------------------------------- Initialize -------------------------------------

    @Logger('main', 'info')
    def initialize(self, config):
        self.initializeConfig(config)
        self.initializeContracts()
        self.initializeContractDetail()
        self.initializeContractsFromConfig()
        self.initializeContractDetailFromConfig()

    @Logger('main', 'debug')
    def initializeConfig(self, config):
        self.config = config
        self.configContracts = self.config['CONTRACTS']

    @Logger('main', 'debug')
    def initializeContracts(self):
        self.contracts = dict()

    @Logger('main', 'debug')
    def initializeContractDetail(self):
        self.contractDetail = dict()

    @Logger('main', 'debug')
    def initializeContractsFromConfig(self):
        for key, val in self.configContracts.items():
            id_ = key
            secType = val['sec_type']
            para = val['para']
            self.createContract(id_, secType, para)

    @Logger('main', 'debug')
    def initializeContractDetailFromConfig(self):
        for id_ in self.contracts.keys():
            contract = self.contracts[id_]
            self.createContractDetail(id_, contract)

    # ------------------------------------- Update -------------------------------------

    @Logger('main', 'info')
    def update(self):
        pass


if __name__ == '__main__':

    pass
