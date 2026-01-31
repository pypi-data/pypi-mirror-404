import copy
from collections import OrderedDict

import ambr as am
import numpy as np
import numpy.random as random
from scipy.optimize import minimize

from ..utils import days_in_month
from .GoodsFirmBase import GoodsFirmBase

# ============================================================================
#                           ConsumerGoodsFirm
# ============================================================================
# Role:
#   - Produces goods for households (final consumption).
#   - Forecasts demand using sales + expected demand (exponential smoothing).
#   - Determines input needs: labour, energy, and capital purchases.
#   - Produces output via CES-like technology (adjusted for Covid sick leave).
#   - Sets price as markup over costs (markup factor depends on utilization).
#   - Computes profits after paying wages, servicing debt, and carbon tax.
#   - Retains part of net profit, pays dividends to owners.
#   - Unlike CapitalGoodsFirm, capital growth here comes from purchased capital
#     rather than own production.
# ============================================================================


class ConsumerGoodsFirm(GoodsFirmBase):
    """A ConsumerGoodsFirm agent"""

    def setup(self):
        super().setup()

        # ----------------------------------------
        # Core state
        # ----------------------------------------
        self.wages = {}  # worker_id -> current wage
        self.price = 0  # unit price of consumer goods
        self.capital = 10000  # initial physical capital
        self.labour = 0
        self.equity = 0

        # ----------------------------------------
        # Technology / preferences (consumer-goods specific)
        # ----------------------------------------
        self.beta_capital = self.p.beta_capital
        self.beta_labour = self.p.beta_labour
        self.beta_energy = self.p.beta_energy
        self.eta_production = self.p.ETA_PRODUCTION
        self.rho_labour = self.p.rho_labour
        self.rho_energy = self.p.rho_energy
        self.capital_growth_rate = self.p.capital_growth_rate
        self.mark_up = self.p.mark_up_factor
        self.mark_up_adjustment = self.p.mark_up_adjustment
        self.mark_up_alpha = self.p.mark_up_alpha
        self.mark_up_beta = self.p.mark_up_beta
        self.carbon_tax_state = self.p.settings.find("CT") != -1
        self.div_ratio = self.p.ownerProportionFromProfits
        self.capital_depreciation = self.p.depreciationRate
        self.forecast_discount_factor = (
            self.p.forecast_discount_factor
        )  # smoothing weight β

        # ----------------------------------------
        # Transient / book-keeping
        # ----------------------------------------
        self.actual_production = 0
        self.planned_production = 1100
        self.utilization = 0
        self.labour_demand = 0
        self.aggregate_demand = 0
        self.energy = 0
        self.brown_firm = self.useEnergy == "brown"

        # Capital accounting (value vs. physical)
        self.capital_investment = 0  # value variable
        self.capital_increase = 616  # physical increment (target for expansion)
        self.capital_price = 0
        self.capital_value = self.capital * self.capital_price  # value variable
        self.cost_of_capital = 0  # value variable
        self.capital_purchase = 0  # physical variable
        self.capital_demand = self.capital * (
            self.capital_growth_rate + self.capital_depreciation
        )  # physical variable
        self.average_production_cost = 0

        # Market structure (each firm starts with equal market share)
        self.market_share = 1 / self.p.csf_agents
        self.market_shareList = []

    # ========================================
    # Forecasting & planning
    # ========================================
    def prepareForecast(self):
        """Reset per-step aggregates and scope the current consumer pool."""
        """if self.model.t > 31:
            print("total sale", self.model.total_good)
            self.market_share = self.getSoldProducts() / self.model.total_good

        self.market_shareList.append(self.market_share)"""
        self.set_aggregate_demand(0)
        self.soldProducts = 0

        # Optimization: Avoid O(N) selection. Use reference to global list.
        # Filtering is done efficiently in calculate_all_wages and produce.
        self.consumersList = self.model.aliveConsumers
        # market share

    def calculate_input_demand(self):
        """Plan production and input demands based on demand forecasts."""
        beta = self.forecast_discount_factor
        # This function is used to calculate all inputs and related demands
        # Plan = smoothed demand (no self-expansion term unlike capital firms)
        self.old_demand = self.get_aggregate_demand()
        self.planned_production = (
            beta * self.sale_record + (1 - beta) * self.get_aggregate_demand()
        )

        # Utilization ratio = recent sales / expected demand (used in pricing markup)
        self.utilization = self.sale_record / self.old_demand

        # Labour demand heuristic: allocate share of total workers
        self.labour_demand = 0.8 * self.model.num_worker / self.p.csf_agents

        # Choose energy given labour and capital
        self.energy = self.optimize_energy(self.labour_demand, self.capital)

        # Capital demand: replacement + expansion need
        self.capital_demand = self.get_capital() * (
            self.capital_growth_rate + self.capital_depreciation
        )
        # print("good firm capital demand", self.capital_demand, self.capital, self.capital* (1 - self.capital_depreciation) +self.capital_demand)

    # ========================================
    # Production (CES-like technology with Covid sick-leave reduction)
    # ========================================
    def produce(self):
        """Calculate actual production based on inputs and sick leave adjustments."""
        # This function is to calculate the actual production value based on the inputs of current period
        # Check production function in GoodsFirmBase

        # Aggregate sick leave among workers assigned to this firm
        # Optimization: Use fast attribute check or set membership
        # workers_set = set(self.workersList) # Use if self.workersList is not guaranteed to sync with employerID?
        # But employerID is likely single source of truth.

        # Fast iteration using direct attribute access if possible.
        # Since self.consumersList is now ALL consumers, filtering by employerID is needed.

        # Check if we can just iterate self.workersList if we can map IDs -> Objects?
        # If not, iterating 5000 items is fast (0.04s total for 138 calls is ~0.0003s).
        # Optimization: use fast set membership check on worker IDs
        # This mirrors the pattern in calculate_all_wages for consistency and speed.

        workers_set = set(self.workersList)
        aggSickLeaves = sum(
            len(aConsumer.getSickLeaves())
            for aConsumer in self.consumersList
            if aConsumer.id in workers_set
        )
        if self.p.verboseFlag:
            print("sick leave", aggSickLeaves)

        # Fraction of hours lost
        if len(self.workersList) > 0:
            sick_ratio = np.min(
                [1, np.max([0, aggSickLeaves / (30 * len(self.workersList))])]
            )
        else:
            sick_ratio = 0
        if self.p.verboseFlag:
            print("sick ratio", sick_ratio)

        # Inputs for the period
        labour_input = self.labour_demand
        capital_input = self.get_capital()
        energy_input = self.get_energy()
        # print("input", labour_input, capital_input, energy_input)
        # print("energy type", self.useEnergy)

        # Gross output reduced by sickness
        production_value = self.production_function(
            (capital_input, labour_input, energy_input)
        ) * (1 - sick_ratio)
        # print("production value", production_value, self.planned_production)

        # Net output = all goes to consumer market (no self-expansion withholding)
        self.set_actual_production(production_value)

    # ========================================
    # Pricing (markup over average cost, adjusted by utilization)
    # ========================================
    def price_setting(self):
        """Function to set price base on mark up over cost"""

        ## calculate cost
        self.calculate_average_production_cost()

        ## set price
        # Select relevant energy price (brown vs. green)
        energy_price = (
            self.model.brownEFirm[-1].getPrice()
            if self.brown_firm
            else self.model.greenEFirm[-1].getPrice()
        )

        # Markup is adjusted by (α + β * utilization)
        self.price = self.get_average_production_cost() * (
            1
            + self.mark_up * (self.mark_up_alpha + self.mark_up_beta * self.utilization)
        )
        # print("price ", self.price, self.id, self.getUseEnergy(), energy_price, " utilization: ", self.utilization, self.profits)
        self.priceList.append(np.sum([self.getPrice()]))

    # ========================================
    # Accounting: wages, debt service, profits, taxes, owner income
    # ========================================
    def compute_net_profit(self, eps=1e-8):
        """Calculate profit after all costs, taxes, and owner payments"""
        # function to calculate profit

        # Wage component summarized as per-worker average
        if self.wage_bill > 0:
            self.unitWageBill = self.wage_bill / (self.getNumberOfLabours())
        else:
            self.unitWageBill = 0  # If no labour demanded, treat as shutdown

        self.countWorkers = self.getNumberOfLabours()

        if self.p.verboseFlag:
            print(
                f"Number of workers in Consumer Goods Firm no. {self.id - self.p.c_agents - self.p.csf_agents - 1 - 1} is {self.countWorkers}"
            )

        # Update loan payback / carbon surcharge if applicable
        self.progressPayback()

        # printing firm report
        if self.p.verboseFlag:
            print()
            print("Activity Report for firm", self.id, ":")
            print("........................................")

        # Calculating Profit
        if self.p.verboseFlag:
            print(
                "loan payback",
                self.payback,
                self.deposit,
                self.get_average_production_cost() * self.get_actual_production(),
            )

        # Profits = interest on deposits + revenues - costs + payback
        self.profits = (
            self.p.bankID * self.deposit
            + self.getSoldProducts() * self.getPrice()
            - self.get_average_production_cost() * self.get_actual_production()
            + self.payback
        )  # - self.inn

        # Profit margin (sales margin measure)
        sales_val = self.getSoldProducts() * self.getPrice()
        if sales_val > 0:
            self.profit_margin = (
                sales_val
                - self.get_average_production_cost() * self.get_actual_production()
            ) / sales_val
        else:
            self.profit_margin = 0

        # Apply taxes (+ carbon tax if brown and policy active), compute net profit
        self.updateProfitsAfterTax(isC02Taxed=self.carbon_tax_state * self.brown_firm)

        # Owner payout = fraction of positive net profit
        self.ownerIncome = np.max([0, self.net_profit * self.div_ratio])

        if self.p.verboseFlag:
            print("deposit before", self.deposit)

        # Retained earnings = net profit - ownerIncome
        self.updateDeposit(self.net_profit - self.ownerIncome)

        if self.p.verboseFlag:
            print("deposit after", self.deposit)
            print("networth", self.netWorth)
            print("production and sale", self.actual_production, self.sale_record)
            print("profit", self.profits, self.net_profit)
            print(
                "owner income",
                self.ownerIncome,
                "deposit",
                self.deposit,
                "total cost",
                self.get_average_production_cost() * self.get_actual_production(),
            )
            print("DTE", self.DTE)
            print(
                "loan list",
                sum(self.loanList),
                self.loanList,
                "loan demand",
                self.loan_demand,
                "loan granted",
                self.loanObtained,
            )

    # ========================================
    # Capital stock evolution for consumer-goods firms
    # ========================================
    def update_capital_growth(self):
        """Update capital growth from purchases"""
        # For consumer-producers, capital growth = actual purchases (from capital firms)
        self.capital_growth = self.capital_purchase
        # print("consumer capital growth", self.capital_growth)
        # for consumer firm, capital growth is what they purchase
