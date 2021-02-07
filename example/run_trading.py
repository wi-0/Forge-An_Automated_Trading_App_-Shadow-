import ib_insync as ibi
from src.manager.Agent import Agent
from src.strategy import ATRTrailing
from src.allocator import EqualWeight
from src.util.log_util import *
from cfg.config import *

updateLogFilePath()
logging.config.dictConfig(CONFIG_LOGGING)


class Agent1(Agent):

    @Logger('main', 'info')
    def __init__(self, ib):
        super().__init__(ib)
        self.atrTrailing1 = ATRTrailing.ATRTrailing(agent=self)
        self.atrTrailing2 = ATRTrailing.ATRTrailing(agent=self)
        self.ew1 = EqualWeight.EqualWeight(agent=self)

    @Logger('main', 'info')
    def initialize(self, config):
        super().startInitialize(config)

        self.atrTrailing1.initialize(config['ATR_TRAILING_1'])
        self.atrTrailing2.initialize(config['ATR_TRAILING_2'])
        self.ew1.initialize(config['EQUAL_WEIGHT'])

        super().endInitialize()

    @Logger('main', 'info')
    def update(self):
        super().startUpdate()

        print('run update')
        self.atrTrailing1.update()
        self.atrTrailing2.update()
        self.ew1.update()

        super().endUpdate()


if __name__ == '__main__':

    ib = ibi.IB()
    A1 = Agent1(ib)
    A1.run(CONFIG_MASTER)

