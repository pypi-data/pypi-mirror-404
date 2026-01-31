import copy
from collections import OrderedDict

import ambr as am
import numpy as np
import numpy.random as random
from scipy.optimize import minimize

from ..utils import days_in_month
from .GoodsFirmBase import GoodsFirmBase

# ============================================================================
#                           CapitalGoodsFirm
# ============================================================================
# Role:
#   - Produces machines/capital for other firms (and for its own expansion).
#   - Plans output from recent sales vs. expected demand (exponential smoothing).
#   - Chooses inputs (labour, energy) and then produces via a CES-like function.
#   - Sets prices as a markup over average cost.
#   - Pays wages, services debt, applies carbon tax (if brown) and computes profits.
#   - Automatically withholds part of gross production to expand its own capital.
# ============================================================================


class CapitalGoodsFirm(GoodsFirmBase):
    """A CapitalGoodsFirm agent"""

    def setup(self):
        super().setup()

        # ----------------------------------------
        # Core state
        # ----------------------------------------
        self.wages = {}  # worker_id -> current wage
        self.price = 1  # unit price of capital goods
        self.capital = 0  # internal capital stock (also part of prod. function)
        self.labour = 0
        self.equity = 0
        self.deposit = 10000  # cash buffer

        # ----------------------------------------
        # Technology / preferences (capital-goods specific)
        # ----------------------------------------
        self.beta_capital = self.p.beta_capital_K
        self.beta_labour = self.p.beta_labour_K
        self.beta_energy = self.p.beta_energy_K
        self.eta_production = self.p.ETA_PRODUCTION_CAPITAL
        self.rho_labour = self.p.rho_labour_K
        self.rho_energy = self.p.rho_energy_K
        # self.capital_multiplier = self.p.capital_multiplier  # currently not use
        self.capital_growth_rate = self.p.capital_growth_rate
        self.mark_up = self.p.mark_up_factor
        self.mark_up_alpha = (
            self.p.mark_up_alpha
        )  # (unused here but kept for compatibility)
        self.mark_up_beta = (
            self.p.mark_up_beta
        )  # (unused here but kept for compatibility)
        self.carbon_tax_state = self.p.settings.find("CT") != -1
        self.div_ratio = self.p.ownerProportionFromProfits
        self.capital_depreciation = self.p.depreciationRate
        self.forecast_discount_factor = (
            self.p.forecast_discount_factor
        )  # smoothing weight β

        # ----------------------------------------
        # Transient / book-keeping
        # ----------------------------------------
        self.actual_production = 0  # net marketable output (after own expansion)
        self.planned_production = 1500  # initial production plan
        self.labour_demand = 0
        self.aggregate_demand = 20000  # placeholder; set each step in prepareForecast
        self.energy = 0
        self.brown_firm = self.useEnergy == "brown"

        # Capital accounting (value vs. physical)
        self.capital_investment = 0  # value variable
        self.capital_increase = 165  # physical increment autonomously targeted
        self.capital_price = self.price
        self.capital_value = self.capital * self.capital_price  # value variable
        self.cost_of_capital = 0  # value variable
        self.average_production_cost = 0

        # Initial capital differently by energy type
        if self.brown_firm:
            self.capital = 5000
        else:
            self.capital = 4200

    # ========================================
    # Forecasting & planning
    # ========================================
    def prepareForecast(self):
        """Reset per-step aggregates and scope the current employee pool."""
        self.set_aggregate_demand(0)
        self.soldProducts = 0
        # Keep only alive, working-age consumers for firm-level sick leave accounting
        self.consumersList = self.model.aliveConsumers.select(
            (self.model.aliveConsumers.getCovidStateAttr("state") != "dead")
            & (self.model.aliveConsumers.getAgeGroup() == "working")
        )

    def calculate_input_demand(self):
        """Plan production and inputs using simple exponential smoothing."""
        beta = self.forecast_discount_factor
        # Plan equals smoothed (recent sales vs. expected demand) plus own expansion need
        self.planned_production = (
            beta * self.sale_record + (1 - beta) * self.get_aggregate_demand()
        ) + self.capital_increase
        # print("capital planned production", self.planned_production)

        # Labour demand: simple proportional target over total workers (heuristic)
        self.labour_demand = 0.15 * self.model.num_worker / self.p.cpf_agents

        # Choose energy consistent with production function and current capital
        self.energy = self.optimize_energy(self.labour_demand, self.capital)
        # print("capital input", self.energy, self.labour_demand, self.capital)

    # ========================================
    # Production (CES-like technology adjusted for Covid sick-leave reduction)
    # ========================================
    def produce(self):
        """Calculate actual production based on inputs and sick leave adjustments."""
        # This function is to calculate the actual production value based on the inputs of current period
        # Check production function in GoodsFirmBase
        # print("worker list", len(self.workersList), self.getNumberOfLabours())

        # Aggregate sick leave among workers assigned to this firm
        workers_set = set(self.workersList)
        aggSickLeaves = sum(
            len(aConsumer.getSickLeaves())
            for aConsumer in self.consumersList
            if aConsumer.id in workers_set
        )
        # print("sick leave", aggSickLeaves)

        if len(self.workersList) > 0:
            denominator = 720 * len(self.workersList)
            if denominator > 0:  # Guard against division by zero
                sick_ratio = np.min([1, np.max([0, aggSickLeaves / denominator])])
            else:
                sick_ratio = 0
        else:
            sick_ratio = 0
        # print("sick ratio", sick_ratio)

        # Inputs for the period
        labour_input = self.labour_demand
        capital_input = self.get_capital()
        energy_input = self.get_energy()
        if self.p.verboseFlag:
            print(
                "capital input",
                self.get_energy(),
                self.labour_demand,
                self.get_capital(),
            )

        # Gross output from production function, reduced by sickness
        production_value = self.production_function(
            (capital_input, labour_input, energy_input)
        ) * (1 - sick_ratio)
        # print("capital production value")

        # Net marketable output: withhold own expansion (capital_increase) automatically
        self.set_actual_production(
            production_value - self.capital_increase
        )  # capital firm automatically take away the capital they need for own expansion
        # print("\ndemand", self.planned_production,"net capital production", self.get_actual_production(), self.capital_increase, "total capital", self.capital)

    # ========================================
    # Pricing (markup over average cost)
    # ========================================
    def price_setting(self):
        """Function to set price base on mark up over cost"""

        ## calculate cost
        self.calculate_average_production_cost()

        ## set price
        self.price = self.get_average_production_cost() * (1 + self.mark_up)

        # For capital producers, the "capital price" is their own output price
        self.set_capital_price(
            self.price
        )  # for capital firm, capital price is their own price (basically net zero)
        self.priceList.append(np.sum([self.getPrice()]))

    # ========================================
    # Accounting: wages, debt service, profits, taxes, owner income
    # ========================================
    def compute_net_profit(self, eps=1e-8):
        """Calculate profit after all costs, taxes, and owner payments"""
        # function to calculate profit

        # Wage component summarized as per-worker average if any wages were paid
        if self.wage_bill > 0:
            self.unitWageBill = self.wage_bill / (self.getNumberOfLabours() + eps)
        else:
            self.unitWageBill = 0  # If no labour demanded, treat as shutdown

        self.countWorkers = self.getNumberOfLabours()

        if self.p.verboseFlag:
            print(
                f"Number of workers in Capital Goods Firm no. {self.id - self.p.c_agents - self.p.csf_agents - 1 - 1} is {self.countWorkers}"
            )

        # Update loan payback / carbon surcharge into price if applicable
        self.progressPayback()

        # Operating profits + interest on deposits + (payback is a negative outflow)
        self.profits = (
            self.p.bankID * self.deposit
            + self.getSoldProducts() * self.getPrice()
            - self.get_average_production_cost() * self.get_actual_production()
            + self.payback
        )  # - self.inn

        # Apply taxes (+ carbon tax if brown and policy active), compute net profit
        self.updateProfitsAfterTax(isC02Taxed=self.carbon_tax_state * self.brown_firm)

        # Owner payout = all positive net profit (modeling choice here)
        self.ownerIncome = np.max([0, self.net_profit])

        # Retained earnings = net_profit - ownerIncome (≤ 0 if fully distributed)
        self.updateDeposit(self.net_profit - self.ownerIncome)

    # ========================================
    # Capital stock evolution for capital-goods firms
    # ========================================
    def update_capital_growth(self):
        """Update internal capital growth target"""
        # For capital-producers, internal capital growth equals replacement + target growth
        self.capital_growth = self.get_capital() * (
            self.capital_growth_rate + self.capital_depreciation
        )
        # for capital firm, capital growth is what they produce inhouse
