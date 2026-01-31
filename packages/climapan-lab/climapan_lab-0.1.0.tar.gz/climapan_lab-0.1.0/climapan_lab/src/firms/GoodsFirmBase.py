import copy
from collections import OrderedDict

import ambr as am
import numpy as np
import numpy.random as random
from scipy.optimize import minimize

from ..utils import days_in_month

# ============================================================================
#                           GoodsFirmBase
# ============================================================================
# Role:
#   Base class with finance, production cost accounting, labor management,
#   loans/repayment, carbon-tax handling, and shock/lockdown utilities.
#
# Lifecycle (per month; orchestrated by the model):
#   1) plan:    set planned_production (in subclass), call production_budgeting()
#   2) hire:    model assigns workers; calculate_all_wages() builds wage bill
#   3) produce: subclass computes actual_production via production_function()
#   4) sell:    model matches demand → set/updateSoldProducts(), setPrice()
#   5) settle:  compute costs, profits, update capital value, progressPayback()
#   6) tax/div: updateProfitsAfterTax(), ownerIncome handled at model level
#
# Key state:
#   capital, energy, workersList, wages, price, deposit, loans (loanList),
#   DTE (debt-to-equity), iL (loan rate), iF (financial fragility proxy),
#   average_production_cost, planned/actual production, carbonTax etc.
# ============================================================================


class GoodsFirmBase(am.Agent):
    """A GoodsFirmBase agent"""

    def setup(self):

        # ----------------------------------------
        # Core firm stocks & finance
        # ----------------------------------------
        self.workersList = []  # IDs of employed workers
        self.wages = {}  # id → wage mapping for this firm
        self.price = 0  # initial price of produced goods (set by model)
        self.capital = 0  # physical units of installed capital
        self.energy = 0  # energy input planned/used this step
        self.deposit = 0  # cash / liquid assets
        self.equity = 0
        self.net_profit = 0
        self.non_loan = 0  # written-off part after bankruptcy

        # ----------------------------------------
        # Technology & policy parameters (snapshot from self.p)
        # ----------------------------------------
        self.iL = self.p.bankICB  # base loan rate (bank interbank proxy)
        self.beta_capital = self.p.beta_capital
        self.beta_labour = self.p.beta_labour
        self.beta_energy = self.p.beta_energy
        self.eta_production = self.p.ETA_PRODUCTION
        self.rho_labour = self.p.rho_labour
        self.rho_energy = self.p.rho_energy
        self.capital_growth_rate = self.p.capital_growth_rate
        self.carbon_tax_state = self.p.settings.find("CT") != -1
        self.div_ratio = self.p.ownerProportionFromProfits
        self.capital_depreciation = self.p.depreciationRate
        self.wage_factor = 1 / (1 + self.p.wageAdjustmentRate)

        # ----------------------------------------
        # Transient/accounting variables
        # ----------------------------------------
        self.wage_bill = 0
        self.unitWageBill = self.p.unemploymentDole
        self.capital_tracking = []  # rolling buffer of investment values
        self.actual_production = 0  # 10
        self.planned_production = 0
        self.average_production_cost = 0
        self.labour_demand = 0
        self.aggregate_demand = 0
        self.priceList = [1]

        # Capital purchase & valuation
        self.capital_investment = 0  # value variable
        self.capital_increase = 0  # physical variable
        self.capital_price = 1
        self.capital_value = self.capital * self.capital_price  # value variable
        self.cost_of_capital = 0  # value variable - amortized cost in avg cost calc
        self.capital_purchase = 0  # physical variable
        self.capital_demand = 0  # physical variable
        self.capital_growth = 0  # physical variable

        # Energy mix
        self.useEnergy = None  # 'green' or 'brown'
        self.brown_firm = self.useEnergy == "brown"

        # Data writer for quick diagnostics
        self.firmDataWriter = []  # [sold, wage_bill, n_workers] each step

        # Banking / leverage
        self.loanObtained = 0
        self.loan_demand = 0
        self.loanList = [0, 0]  # outstanding principals by "vintage"
        self.loanContractRemainingTime = {}  # vintage → months remaining
        self.DTE = 0  # debt-to-equity ratio
        self.iF = 0  # interest paid on loans
        self.reserve_ratio = self.p.reserve_ratio

        # Other accounting & flags
        self.depositList = [0, 0]
        self.sale_record = 0
        self.profits = 0
        self.fix_cost = 0
        self.ownerIncome = 0
        self.netWorth = 0
        self.countConsumers = 0
        self.countWorkers = 0
        self.carbonTax = 0
        self.defaultProb = 0
        self.bankrupt = False
        self.lockdown = False
        self.lockdownList = []
        self.payback = 0
        self.profit_margin = 0

        # Shortcuts to agent lists
        self.consumersList = self.model.consumer_agents
        self.sickList = self.model.consumer_agents

        # Taxes & sales
        self.tax = 0
        self.soldProducts = 1

        # ----------------------------------------
        # Rebuild worker roster if reloaded mid-run
        # ----------------------------------------
        self.workersList = []
        [
            self.workersList.append(aConsumer.id)
            for aConsumer in self.model.aliveConsumers
            if aConsumer.consumerType == "workers"
            and aConsumer.getBelongToFirm() == self.id
            and aConsumer.getCovidStateAttr("state") != "dead"
        ]
        for aConsumer in self.model.aliveConsumers:
            if aConsumer.getIdentity() in self.workersList:
                self.wages[aConsumer.getIdentity()] = aConsumer.getWage()

    # ========================================
    # Bankruptcy reset (re-entry with new balance sheet)
    # ========================================
    def bankrupt_reset(self):
        """Reset firm state after bankruptcy"""
        print("firm get bankrupt!!!", self.id)
        self.netWorth = 0
        self.loanObtained = 0
        self.loanList = [0, 0]
        self.loanContractRemainingTime = {}
        self.payback = 0
        self.bankrupt = False
        self.DTE = 0
        self.deposit = 0
        self.depositList = [0, 0]
        self.fiscal = 0
        self.brown_firm = self.useEnergy == "brown"

    # ========================================
    # CES-like production function (unit-consistent)
    # ========================================
    def production_function(self, inputs):
        """Define consumer goods production function"""
        capital_input, labour_input, energy_input = inputs
        production = (
            self.beta_capital * (capital_input) ** self.eta_production
            + self.beta_labour * (labour_input * self.rho_labour) ** self.eta_production
            + self.beta_energy * (energy_input * self.rho_energy) ** self.eta_production
        ) ** (1 / self.eta_production)
        return production

    # ========================================
    # Financing the plan (loan demand, deposits, logging)
    # ========================================
    def production_budgeting(self):
        """Decide funding for planned production; compute loan demand."""
        # print("capital stock", self.capital, self.capital_increase, self.capital_growth)
        # checking if production can be financed, otherwise taking loan if possible
        # Need enough cash to cover variable cost; allow some minimum leverage
        self.loan_demand = np.max(
            [
                self.get_average_production_cost() * self.planned_production
                - self.deposit * (1 - self.reserve_ratio),
                self.get_average_production_cost() * self.planned_production * 0.2,
            ]
        )
        # self.loan_demand = np.max([self.get_average_production_cost() * self.planned_production, 0])
        if self.loan_demand > 0:
            # Bank module will respond via adjustAccordingToBankState
            pass
        else:
            self.loanList.append(0)

            data = [self.getSoldProducts(), self.wage_bill, len(self.workersList)]
            self.firmDataWriter.append(data)

    # ========================================
    # Average production cost decomposition (wage, energy, capital)
    # ========================================
    def calculate_average_production_cost(self):
        """Function to derive production cost"""
        ## Wage Component
        # Wage Component
        # Wage component (use model-wide mean wage among workers)
        self.calculate_all_wages()

        # Optimization: Avoid re-selecting workers from global list
        # consumersList is likely self.model.aliveConsumers (shared)
        # We can use the cached 'workers' subset if available, or vectorize.

        # Original: self.consumersList.select(consumerType == "workers").getWage()
        # This is slow O(N).
        # We know who workers are: self.model.aliveConsumers where consumerType=='workers'
        # Even better, we performed wage updates in calculate_all_wages on self.workersList (IDs).

        # If we need the GLOBAL mean wage of workers:

        consumers = self.consumersList
        # Vectorized access (AMBER or AgentPy list)
        # If consumers is an AgentList, it has attribute access.
        # wages = consumers.wage  <-- but we need to filter by type "workers"

        # Fast way:
        # wages = np.array(consumers.wage)
        # types = np.array(consumers.consumerType)
        # mean_wage = np.mean(wages[types == "workers"])

        # Even faster: The Bank or Model likely knows this?
        # But to be safe and local:

        # Note: 'consumersList' is passed to firm.
        # If we use list comprehension it is faster than .select()

        # However, calling this for EVERY firm is wasteful if it's the same global value.
        # But assuming we must keep it local:

        # Gather all wages of workers.
        # Since we just updated wages, we can iterate self.wages (dict of {id: wage})
        # IF self.wages contains ALL workers.
        # In `calculate_all_wages`, we iterate `consumersList`, filter by `workersList` (global active workers?),
        # and update `self.wages`.
        # So `self.wages` SHOULD contain the latest wages of relevant workers.
        # CHECK: Is self.wages specific to this firm or global? Base class has `self.wages = {}`.
        # Each firm calculates wages for... who?
        # In `calculate_all_wages`, it iterates `self.consumersList` (passed in Init).
        # If `consumersList` is ALL consumers, then every firm calculates wages for ALL consumers?
        # That would be redundant!
        # `GoodsFirmBase` calls `calculate_all_wages`... wait.
        # If every firm calls `calculate_all_wages` and it loops over ALL consumers, that is O(Firms * Consumers).
        # That explains why `calculate_all_wages` was slow!
        # I optimized the loop, but the architecture seems to have every firm updating every consumer??
        # If so, `mean_wage` is just `np.mean(list(self.wages.values()))`.

        if self.wages:
            mean_wage = np.mean(list(self.wages.values()))
        else:
            mean_wage = 0  # Should not happen if workers exist
        # it is probably best to just sum the wage instead of taking average and multiply with number of labour

        ## Energy Component
        # Energy component (price depends on current mix)
        energy_price = (
            self.model.brownEFirm[-1].getPrice()
            if self.brown_firm
            else self.model.greenEFirm[-1].getPrice()
        )
        energy_cost = self.get_energy() * energy_price
        # print("energy break down: ", self.id, self.getUseEnergy(), self.get_energy(), energy_price)

        ## Capital Component
        # Capital component (amortize recent investment over a rolling window)
        # Need to default value of past periods to 0
        if len(self.capital_tracking) > self.p.capital_length:
            self.capital_tracking.pop(0)
        self.capital_tracking.append(np.sum(self.capital_investment))

        cost_of_capital = np.sum(self.capital_tracking) / self.p.capital_length
        self.cost_of_capital = cost_of_capital
        ##Need to also store the price of capital together with the period so we can do multiplication

        # Unit cost and fixed cost (wage+capital, excluding variable energy)
        self.average_production_cost = (
            mean_wage * self.getNumberOfLabours() + energy_cost + cost_of_capital
        ) / (self.get_actual_production())
        # print(self.id, " cost of each type: ", self.getUseEnergy(), " wage ", mean_wage * self.getNumberOfLabours(),
        #      " energy ", energy_cost,
        #      " capital ", cost_of_capital, "-", self.capital_price,
        #      " production ", self.get_actual_production())

        self.fix_cost = mean_wage * self.getNumberOfLabours() + cost_of_capital

    # ========================================
    # Loan amortization & delinquency evolution (monthly)
    # ========================================
    def payLoan(self):
        """Amortize current loans with available payback amount"""
        if -self.payback > 0:
            payback = copy.copy(self.payback)
            for loan_id in [
                i for i in range(len(self.loanList)) if self.loanList[i] > 0
            ]:
                if payback == 0:
                    break
                if -payback <= self.loanList[loan_id]:
                    self.loanList[loan_id] += np.sum(payback)
                    payback = 0
                else:
                    self.loanList[loan_id] = 0
                    payback += np.sum(self.loanList[loan_id])
                # Contract time and default trigger
                if (
                    self.loanList[loan_id] > 0
                    and self.loanContractRemainingTime[loan_id] <= 0
                ):
                    self.bankrupt = True
                elif self.loanList[loan_id] > 0:
                    self.loanContractRemainingTime[loan_id] -= 1
                else:
                    self.loanContractRemainingTime.pop(loan_id)
        else:
            # No payment this step; still age contracts and check default
            for loan_id in [
                i for i in range(len(self.loanList)) if self.loanList[i] > 0
            ]:
                if (
                    self.loanList[loan_id] > 0
                    and self.loanContractRemainingTime[loan_id] <= 0
                ):
                    self.bankrupt = True
                elif self.loanList[loan_id] > 0:
                    self.loanContractRemainingTime[loan_id] -= 1
                else:
                    self.loanContractRemainingTime.pop(loan_id)

    # ========================================
    # Profits after corporate + carbon tax
    # ========================================
    def updateProfitsAfterTax(self, isC02Taxed=False):
        """Apply corporate tax and optionally carbon tax"""
        carbonTax = copy.copy(self.carbonTax) if isC02Taxed else 0
        if self.profits > 0:
            self.net_profit = (1 - self.p.taxRate) * self.profits - carbonTax
            self.updateTax(self.p.taxRate * self.profits + carbonTax)
        else:
            self.net_profit = 1 * self.profits - carbonTax
            self.updateTax(carbonTax)

    # ========================================
    # Bank response (called after bank computes obtainedCredit)
    # ========================================
    def adjustAccordingToBankState(self, obtainedCredit, eps=1e-8):
        """Check bank _calculate_running_loan for the function"""
        ## Credit obtained via bank
        # If a loan is granted, create a new vintage with a repayment horizon
        # if obtainedCredit > 0 and len(self.loanContractRemainingTime) == 0:
        if obtainedCredit > 0:
            self.loanObtained = obtainedCredit
            self.loanList.append(np.sum([self.getLoan()]))

            if self.useEnergy == "green":
                self.loanContractRemainingTime[len(self.loanList) - 1] = (
                    self.p.greenLoanRepayPeriod
                )
            else:
                self.loanContractRemainingTime[len(self.loanList) - 1] = (
                    self.p.brownLoanRepayPeriod
                )

        ## Adjust deposit and networth
        # Cash in, update NW and leverage
        self.updateDeposit(np.sum(obtainedCredit))  # adjust deposit if loan is granted
        self.depositList[-1] = self.deposit
        self.netWorth = self.depositList[-1] - sum(self.loanList)

        ## Update other financial variables
        self.DTE = sum(self.loanList) / (self.netWorth + 1e-8)
        self.iF = np.max([0, self.DTE / 100])
        if self.DTE < 0:
            self.defaultProb = 1
        else:
            self.defaultProb = 1 - np.exp(-self.p.defaultProbAlpha * self.DTE)
        # print("default Prob: ", self.defaultProb)
        self.iL = np.max([0, self.p.bankICB * (1 + self.defaultProb)])

        data = [self.soldProducts, self.wage_bill, len(self.workersList)]
        self.firmDataWriter.append(data)

    # ========================================
    # Capital stock & valuation update (depreciation + new investment)
    # ========================================
    def update_capital_value(self):
        """Update capital stock with depreciation and new investment"""
        # depreciation update
        self.set_capital(self.get_capital() * (1 - self.capital_depreciation))

        # reflect the purchase of new capital
        # Add newly purchased units (from capital_growth / transactions)
        self.update_capital_increase(np.sum(self.capital_growth))
        self.set_capital(self.get_capital() + self.get_capital_increase())

        # new value of capital
        # Revalue
        self.capital_value = self.get_capital() * self.capital_price

    # ========================================
    # Bankruptcy condition + re-entry logic (keeps sector composition)
    # ========================================
    def setBankruptcy(self):
        """Handle bankruptcy and firm re-entry"""
        if self.getBankrupt() == True or self.getNetWorth() < 0:
            self.model.bankrupt_count += 1
            self.non_loan = np.sum([self.loanList])

            # Rebirth policy: keep minimum counts of brown/green firms
            if "ConsumerGoods" in str(self):
                self.model.numCSFirmBankrupt += 1
                if (
                    np.sum(self.model.csfirm_agents.getUseEnergy() == "brown") > 2
                    and np.sum(self.model.csfirm_agents.getUseEnergy() == "green") > 2
                ):
                    if np.random.rand() < 0.5:
                        # Release all workers
                        for wid in self.workersList:
                            self.model.aliveConsumers.select(
                                self.model.aliveConsumers.getIdentity() == wid
                            ).receiveFiring()
                        self.useEnergyType("brown")
                        self.bankrupt_reset()
                    else:
                        for wid in self.workersList:
                            self.model.aliveConsumers.select(
                                self.model.aliveConsumers.getIdentity() == wid
                            ).receiveFiring()
                        self.useEnergyType("green")
                        self.bankrupt_reset()
                elif np.sum(self.model.csfirm_agents.getUseEnergy() == "brown") <= 2:
                    for wid in self.workersList:
                        self.model.aliveConsumers.select(
                            self.model.aliveConsumers.getIdentity() == wid
                        ).receiveFiring()
                    self.useEnergyType("brown")
                    self.bankrupt_reset()
                elif np.sum(self.model.csfirm_agents.getUseEnergy() == "green") <= 2:
                    for wid in self.workersList:
                        self.model.aliveConsumers.select(
                            self.model.aliveConsumers.getIdentity() == wid
                        ).receiveFiring()
                    self.useEnergyType("green")
                    self.bankrupt_reset()
            elif "CapitalGoods" in str(self):
                self.model.numCPFirmBankrupt += 1
                if (
                    np.sum(self.model.cpfirm_agents.getUseEnergy() == "brown") > 1
                    and np.sum(self.model.cpfirm_agents.getUseEnergy() == "green") > 1
                ):
                    if np.random.rand() < 0.5:
                        for wid in self.workersList:
                            self.model.aliveConsumers.select(
                                self.model.aliveConsumers.getIdentity() == wid
                            ).receiveFiring()
                        self.useEnergyType("brown")
                        self.bankrupt_reset()
                    else:
                        for wid in self.workersList:
                            self.model.aliveConsumers.select(
                                self.model.aliveConsumers.getIdentity() == wid
                            ).receiveFiring()
                        self.useEnergyType("green")
                        self.bankrupt_reset()
                elif np.sum(self.model.cpfirm_agents.getUseEnergy() == "brown") <= 1:
                    for wid in self.workersList:
                        self.model.aliveConsumers.select(
                            self.model.aliveConsumers.getIdentity() == wid
                        ).receiveFiring()
                    self.useEnergyType("brown")
                    self.bankrupt_reset()
                elif np.sum(self.model.cpfirm_agents.getUseEnergy() == "green") <= 1:
                    for wid in self.workersList:
                        self.model.aliveConsumers.select(
                            self.model.aliveConsumers.getIdentity() == wid
                        ).receiveFiring()
                    self.useEnergyType("green")
                    self.bankrupt_reset()

    # ========================================
    # Build wage bill (handles sick leave, lockdown, tax withholding)
    # ========================================
    def calculate_all_wages(self):
        """Calculate wages for all workers including sick leave and lockdown adjustments"""
        # Initialize the total wage bill and calculate the number of days in the current month
        self.wage_bill = 0
        self.wage_factor *= 1 + self.p.wageAdjustmentRate

        # Move invariant calculations OUT of the loop
        self.daysInMonth = days_in_month(
            int(str(self.model.today).split("-")[1]),
            int(str(self.model.today).split("-")[0]),
        )
        days = self.daysInMonth
        lockdown_days = len(self.lockdownList)
        unemployment_dole = self.p.unemploymentDole
        pandemic_transfer = self.p.pandemicWageTransfer

        # Optimization: Pre-compute worker set for O(1) lookup
        # self.workersList contains IDs of active workers
        workers_set = set(self.workersList)

        for aConsumer in self.consumersList:
            # Check if the consumer's identity is not in the workersList (i.e., not an active worker)
            # Use direct ID access avoid method call
            if aConsumer.id not in workers_set:
                continue

            # If the consumer's identity is not in the wages dictionary, add it and set the initial wage
            if aConsumer.id not in self.wages:
                self.wages[aConsumer.id] = aConsumer.getWage()

            wages = self.wages[aConsumer.id]
            # print("wage paid", wages)

            # Note: Logic assumes the commented out/overwritten wage calculation
            # from original code was ineffective for the payment, but used for accounting?
            # Preserving original flow logic but cleaning up

            sick_leaves = aConsumer.getSickLeaves()
            len_sick_leaves = len(sick_leaves)

            # Wage Setting
            if aConsumer.getEmploymentState():
                # The logic in original block lines 479-495 calculated a 'wage' that was
                # strictly OVERWRITTEN by line 498.
                # We retain the final calculation for payment.

                # Apply firm's wage factor and income tax withholding
                wage = (
                    wages
                    / (1 - self.p.incomeTaxRate)
                    * self.wage_factor
                    * (1 - self.p.incomeTaxRate)
                )

                # Update the consumer's wage
                aConsumer.setWage(wage)
                self.updateTax(wage * self.p.incomeTaxRate)
                # Update the total wage bill for this time step
                self.wage_bill += wage - (unemployment_dole / days) * len_sick_leaves

    # ========================================
    # Energy back-out from CES target (given L,K and planned Q)
    # ========================================
    def optimize_energy(self, labour, capital):
        """Calculate optimal energy input given labour, capital, and planned production"""
        energy = (1 / self.rho_energy) * (
            (
                self.planned_production**self.eta_production
                - (self.beta_labour * (self.rho_labour * labour) ** self.eta_production)
                - (self.beta_capital * (capital) ** self.eta_production)
            )
            / self.beta_energy
        ) ** (1 / self.eta_production)
        if (
            (
                self.planned_production**self.eta_production
                - (self.beta_labour * (self.rho_labour * labour) ** self.eta_production)
                - (self.beta_capital * (capital) ** self.eta_production)
            )
            / self.beta_energy
        ) < 0:
            energy = 0
        return energy

    # ========================================
    # Monthly payback, carbon tax pass-through, and risk metrics
    # ========================================
    def progressPayback(self, eps=1e-8):
        """Calculate loan payments and apply carbon tax surcharge to price"""
        # Amortization with simple annuity formula if there are active loans
        if len(self.loanContractRemainingTime) > 0:
            self.payback = (
                self.iL
                * np.sum([self.loanList])
                / (
                    1
                    - (1 + self.iL)
                    ** (list(self.loanContractRemainingTime.values())[0])
                )
            )
        else:
            self.payback = 0

        if self.p.verboseFlag:
            print("payback value", self.payback)

        # Carbon tax pass-through into price if brown and CT active
        brown_firm_coefficient = (
            self.brown_firm * self.p.climateZetaBrown * self.p.co2_price
        )
        carbon_tax = (
            brown_firm_coefficient
            * self.carbon_tax_state
            * self.get_actual_production()
        )
        self.setPrice(
            self.getPrice() + np.sum(carbon_tax / (self.get_actual_production()))
        )
        self.payLoan()

        ## Update other financial variables
        # Update risk metrics after payment
        self.DTE = sum(self.loanList) / (self.netWorth + eps)
        self.iF = np.max([0, self.DTE / 100])
        # print("default probability factor", self.DTE)
        if self.DTE < 0:
            self.defaultProb = 1
        else:
            self.defaultProb = 1 - np.exp(-self.p.defaultProbAlpha * self.DTE)
        self.iL = np.max([0, self.p.bankICB * (1 + self.defaultProb)])
        # print("default Prob: ", self.defaultProb, " ", self.DTE)

    # ========================================
    # Fire workers (used on shutdown/bankruptcy)
    # ========================================
    def fire(self):
        """Fire all workers (used on shutdown/bankruptcy)"""
        # function for firm to fire workers
        for (
            id
        ) in (
            self.workersList
        ):  # this line require an update mechanic to fire worker since the worker list shrink as we fire
            worker = self.model.aliveConsumers.select(
                self.model.aliveConsumers.getIdentity() == id
            )
            worker.receiveFiring()
            self.workersList.remove(id)

    # ========================================
    # Shocks & lockdown utilities
    # ========================================
    def setLockDown(self):
        """Activate lockdown state"""
        self.lockdown = True
        self.lockdownList.append(self.model.today)

    def unsetLockDown(self):
        """Deactivate lockdown state"""
        self.lockdown = False

    def resetLockDown(self):
        """Clear lockdown history"""
        self.lockdownList = []

    # ========================================
    # Fiscal transfer hook (e.g., targeted support)
    # ========================================
    def gov_transfer(self, value):
        """Receive government transfer"""
        self.updateDeposit(value)
        self.depositList[-1] = self.deposit
        self.netWorth += self.depositList[-1]
        self.model.government_agents.expenditure += value

    # ----------------------------------------
    # Small helpers/getters
    # ----------------------------------------
    def get_actual_production(self):
        return self.actual_production

    def getNumberOfLabours(self):
        return len(self.workersList)

    def update_actual_production(self, value):
        self.actual_production += value

    def getPrice(self):
        return self.price

    def getNetProfit(self):
        return self.net_profit

    def getIdentity(self):
        return self.id

    def getLoan(self):
        return self.loanObtained

    # ----------------------------------------
    # Demand aggregation helpers
    # ----------------------------------------
    def get_aggregate_demand(self):
        return self.aggregate_demand

    def set_aggregate_demand(self, value):
        self.aggregate_demand = value

    def update_aggregate_demand(self, value):
        self.aggregate_demand += value

    # ----------------------------------------
    # Simple setters/getters
    # ----------------------------------------
    def set_energy(self, value):
        self.set_energy = value

    def get_energy(self):
        return self.energy

    def set_capital(self, capital):
        self.capital = capital

    def get_capital(self):
        return self.capital

    def set_actual_production(self, actual_production):
        self.actual_production = actual_production

    def get_actual_production(self):
        return self.actual_production

    def set_capital_investment(self, capital_investment):
        self.capital_investment = capital_investment

    def get_capital_investment(self):
        return self.capital_investment

    def setSoldProducts(self, soldProducts):
        self.soldProducts = np.sum(soldProducts)

    def updateSoldProducts(self, soldProducts):
        self.soldProducts += np.sum(soldProducts)

    def getSoldProducts(self):
        return self.soldProducts

    def setPrice(self, price):
        self.price = price

    def getPrice(self):
        return self.price

    def useEnergyType(self, energyType):
        self.useEnergy = energyType

    def getUseEnergy(self):
        return self.useEnergy

    def getBankrupt(self):
        return self.bankrupt

    def getDeposit(self):
        return self.deposit

    def set_sale_record(self, sale):
        self.sale_record = sale

    def update_sale_record(self, value):
        self.sale_record += value

    def getNetWorth(self):
        return self.netWorth

    def getTax(self):
        return self.tax

    def setTax(self, tax):
        self.tax = tax

    def updateTax(self, value):
        self.tax += value

    def updateDeposit(self, value):
        self.deposit += value

    def append2DepositList(self, deposit):
        self.depositList.append(deposit)

    def get_average_production_cost(self):
        return self.average_production_cost

    def update_capital_increase(self, value):
        self.capital_increase = np.max([0, value])

    def get_capital_increase(self):
        return self.capital_increase

    def get_capital_demand(self):
        return self.capital_demand

    def set_capital_price(self, value):
        # firm will get this info when doing transaction, capital firm know their price
        # Provided by capital-goods firm during transaction
        self.capital_price = value

    def getOwnerIncome(self):
        return self.ownerIncome

    def reset_non_loan(self):
        self.non_loan = 0
