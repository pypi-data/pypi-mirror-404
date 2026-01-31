import copy
from collections import OrderedDict

import ambr as am
import numpy as np
import numpy.random as random

from .EnergyFirmBase import EnergyFirmBase


class BrownEnergyFirm(EnergyFirmBase):
    """A BrownEnergyFirm agent"""

    def setup(self):
        super().setup()
        # self.price = random.randint(1,6) #6-10 greenE
        self.capital = 50000
        self.capital_increase = 25000
        self.capital_demand = self.capital * (
            self.capital_growth_rate + self.capital_depreciation
        )
        self.price = copy.copy(self.model.fossil_fuel_price)
        self.useEnergy = "brown"
        self.defaultProb = 0
        self.base_price = copy.copy(self.model.fossil_fuel_price)
        self.energy_price_growth = self.p.energy_price_growth
        self.brown_firm = self.useEnergy == "brown"
