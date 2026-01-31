import copy
from collections import OrderedDict

import ambr as am
import numpy as np
import numpy.random as random

# ============================================================================
#                           EnergyFirmBase
# ============================================================================
# Role:
#   - Shared base class for energy firms in the model.
#   - Tracks capital, deposits, loans, prices, and production.
#   - Each step, it:
#       1) Decides how much capital it needs (calculate_input_demand)
#       2) Checks financing needs vs. deposits (production_budgeting)
#       3) Produces enough energy to meet firms' energy_demand (produce)
#       4) Updates price (price_setting) and computes profits (compute_net_profit)
#       5) Services loans and updates risk metrics (progressPayback / payLoan)
#   - Exposes many getters/setters used by the rest of the model.
#   - Applies carbon tax surcharge to brown energy (progressPayback -> price bump).
# ============================================================================


class EnergyFirmBase(am.Agent):
    """A EnergyFirmBase agent"""

    def setup(self):
        # ----------------------------------------
        # Core state
        # ----------------------------------------
        self.capital = 0  # Initial Physical capital stock
        self.deposit = 20000  # Initial Financial cash/deposits buffer
        self.net_profit = 0  # Initial Profit after tax
        self.useEnergy = "brown"  # Either "brown" or "green"

        # ----------------------------------------
        # Parameters (from self.p)
        # ----------------------------------------
        self.iL = self.p.bankICB  # Loan interest baseline (bank ICB)
        self.capital_growth_rate = self.p.capital_growth_rate
        self.capital_depreciation = self.p.depreciationRate
        self.base_price = 0  # Initial price (if used by children)
        self.energy_price_growth = 0  # Trend/growth in price (if used)
        self.div_ratio = (
            self.p.energyOwnerProportionFromProfits
        )  # Payout ratio to owners

        # ----------------------------------------
        # Transient / book-keeping
        # ----------------------------------------
        self.capital_tracking = []  # Rolling tracker for capex costs (amortized)
        self.actual_production = 1000  # Energy output (units)
        self.average_production_cost = 0  # Average cost per unit

        # Debt / credit state
        self.loanList = [0, 0]  # Outstanding loans (vector of amounts)
        self.loanContractRemainingTime = {}  # loan_id -> months left
        self.loanObtained = 0  # Last obtained credit
        self.loan_demand = 0
        self.DTE = 0  # Debt-to-equity proxy
        self.iF = 0  # Firm interest spread component

        # Financial accounts
        self.depositList = [0, 0]  # Historical deposits (for stats)
        self.sale_record = 0
        self.profits = 0
        self.ownerIncome = 0
        self.netWorth = 0

        # Demand/tax/carbon
        self.countConsumers = 0
        self.tax = 0
        self.carbonTax = 0
        self.energy_demand = 0  # Aggregate energy demand from other firms

        # Policy environment
        self.carbon_tax_state = self.p.settings.find("CT") != -1
        self.brown_firm = self.useEnergy == "brown"

        # Capital formation channels (value vs. physical)
        self.capital_investment = 0  # value variable
        self.capital_increase = 0  # physical variable
        self.capital_price = 1  # Price of one unit of capital
        self.capital_value = self.capital * self.capital_price  # value variable
        self.cost_of_capital = 0  # value variable
        self.capital_purchase = 0  # physical variable
        self.capital_demand = 0  # physical variable

    # ========================================
    # Step 1: Input demand (how much capital we need to maintain/expand)
    # ========================================
    def calculate_input_demand(self):
        """Decide how much capital is needed for replacement and growth"""
        # Capital needs: replacement (depreciation) + desired growth
        self.capital_demand = self.get_capital() * (
            self.capital_growth_rate + self.capital_depreciation
        )

    # ========================================
    # Step 2: Financing (do we need a loan to cover production costs?)
    # ========================================
    def production_budgeting(self):
        """Decide how much external financing is needed to cover current production"""
        # checking if production can be financed, otherwise taking loan if possible
        # Required working capital: cost to produce planned output minus available deposits
        self.loan_demand = np.max(
            [
                self.get_average_production_cost() * self.get_actual_production()
                - self.deposit,
                0,
            ]
        )
        if self.loan_demand > 0:
            # NOTE: This directly appends the gap; the bank module later adjusts terms.
            self.loanList.append(
                self.get_average_production_cost() * self.get_actual_production()
                - self.deposit
            )
        else:
            self.loanList.append(0)

    # ========================================
    # Step 3: Production (energy should meet economy's energy_demand)
    # ========================================
    def produce(self):
        """Produce enough energy to satisfy demand with a small buffer"""
        # Energy firm should fully satisfy consumption
        # Heuristic: produce enough to satisfy demand with a small buffer (5)
        self.set_actual_production(5 + self.get_energy_demand())

    # ========================================
    # Costing & pricing
    # ========================================
    def calculate_average_production_cost(self):
        """Calculate average production cost with amortized capital costs"""
        ## Capital Component
        # Roll window for capital spending to smooth cost of capital in APC
        # Need to default value of past periods to 0
        if len(self.capital_tracking) > self.p.capital_length:
            self.capital_tracking.pop(0)
        self.capital_tracking.append(np.sum(self.capital_investment))

        cost_of_capital = np.sum(self.capital_tracking) / self.p.capital_length
        ##Need to also store the price of capital together with the period so we can do multiplication
        self.average_production_cost = (cost_of_capital) / (
            self.get_actual_production()
        )

    def price_setting(self):
        """Set price with multiplicative growth (can be overridden by subclasses)"""
        # Assuming fixed price
        # Default: multiplicative growth on price
        self.price = self.price * (1 + self.energy_price_growth)

    # ========================================
    # Profit & payout (after paying financing costs and taxes)
    # ========================================
    def compute_net_profit(self, eps=1e-8):
        """Calculate profit after financing costs, taxes, and owner payouts"""
        # function to calculate profit

        # 1) Update financing/payback; may also bump price via carbon surcharge
        # determint loan payback
        self.progressPayback()

        # 2) Operating profit + interest on deposits + payback sign convention
        #    (self.payback is negative outflow -> adding it reduces profits)
        # Calculating Profit
        self.profits = (
            self.p.bankID * self.deposit
            + self.get_actual_production()
            * (self.getPrice() - self.get_average_production_cost())
            + self.payback
        )  # - self.inn

        # 3) Apply taxes (and carbon tax if brown & carbon tax active)
        # Net Profit after Tax
        self.updateProfitsAfterTax(isC02Taxed=self.carbon_tax_state * self.brown_firm)

        # 4) Retained earnings into deposits
        self.updateDeposit(self.net_profit)

        # 5) Owner dividends (only from positive net profit)
        # pay income to firm owner
        self.ownerIncome = np.max([0, self.net_profit * self.div_ratio])
        self.updateDeposit(-self.ownerIncome)

    # ========================================
    # Debt service mechanics
    # ========================================
    def payLoan(self):
        """Amortize current loans with available payback amount"""
        # Amortize current loans with available payback amount (if negative)
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
                # Contract expiration check -> bankruptcy flag if unpaid
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
            # No payback this period; just tick down remaining times and check default
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

    def updateProfitsAfterTax(self, isC02Taxed=False):
        """Apply ordinary profit tax and optionally add carbon tax component"""
        carbonTax = copy.copy(self.carbonTax) if isC02Taxed else 0
        if self.profits > 0:
            self.net_profit = (1 - self.p.taxRate) * self.profits - carbonTax
            self.setTax(self.p.taxRate * self.profits + carbonTax)
        else:
            self.net_profit = 1 * self.profits - carbonTax
            self.setTax(carbonTax)

    def adjustAccordingToBankState(self, obtainedCredit, eps=1e-8):
        """Bank module sets obtainedCredit; we record it, open a contract, and recompute leverage."""
        # Check bank _calculate_running_loan for the function

        ## Credit obtained via bank
        # Record new loan if credit was obtained and no active contracts (simple assumption)
        if obtainedCredit > 0 and len(self.loanContractRemainingTime) == 0:
            self.loanObtained = obtainedCredit
            self.loanList.append((np.sum([self.getLoan()])))

            # Contract tenor depends on energy type
            if self.useEnergy == "green":
                self.loanContractRemainingTime[len(self.loanList) - 1] = (
                    self.p.greenLoanRepayPeriod
                )
            else:
                self.loanContractRemainingTime[len(self.loanList) - 1] = (
                    self.p.brownLoanRepayPeriod
                )

        ## Adjust deposit and networth
        # Add cash from the loan to deposits and recompute net worth
        self.updateDeposit(np.sum(obtainedCredit))  # updateDeposit with loan
        # print("update deposit", np.sum(obtainedCredit) + self.net_profit, np.sum(obtainedCredit))
        self.depositList[-1] = self.deposit
        self.netWorth = self.depositList[-1] - sum(self.loanList)

        ## Update other financial variables
        # Risk metrics & loan pricing
        self.DTE = sum(self.loanList) / (
            (self.deposit + self.get_capital() * self.capital_price)
            - sum(self.loanList)
        )
        self.iF = np.max([0, self.DTE / 100])
        if self.DTE < 0:
            self.defaultProb = 1
        else:
            self.defaultProb = 1 - np.exp(-self.p.defaultProbAlpha * self.DTE)
        self.iL = np.max([0, self.p.bankICB * (1 + self.defaultProb)])

    # ========================================
    # Capital stock updates (depreciation + new purchases)
    # ========================================
    def update_capital_value(self):
        """Update capital stock with depreciation and new investment"""
        # 1) Depreciate current stock
        # depreciation update
        self.set_capital(self.get_capital() * (1 - self.capital_depreciation))

        # 2) Add new physical capital (from growth target)
        # reflect the purchase of new capital
        self.update_capital_increase(self.capital_growth)
        self.set_capital(self.get_capital() + self.get_capital_increase())

        # 3) Revalue
        # new value of capital
        self.capital_value = self.get_capital() * self.capital_price

    # ========================================
    # Financing feedback into prices (carbon surcharge + loan service)
    # ========================================
    def progressPayback(self):
        """Calculate loan payments and apply carbon tax surcharge to price"""
        # Amortization formula for level payments if a contract exists; else 0
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
        # print(0", self.payback)

        # Carbon surcharge: add CO2 price component to unit price if brown firm
        brown_firm_coefficient = (
            self.brown_firm * self.p.climateZetaBrown * self.p.co2_price
        )
        carbon_tax = (
            brown_firm_coefficient
            * self.carbon_tax_state
            * self.get_actual_production()
        )
        # print("energy production ", self.get_actual_production())
        self.setPrice(
            self.getPrice() + np.sum(carbon_tax / (self.get_actual_production()))
        )
        self.payLoan()

        ## Update other financial variables
        self.DTE = sum(self.loanList) / (
            (self.deposit + self.get_capital() * self.capital_price)
            - sum(self.loanList)
        )
        self.iF = np.max([0, self.DTE / 100])
        if self.DTE < 0:
            self.defaultProb = 1
        else:
            self.defaultProb = 1 - np.exp(-self.p.defaultProbAlpha * self.DTE)
        self.iL = np.max([0, self.p.bankICB * (1 + self.defaultProb)])

    def update_capital_growth(self):
        """Update capital growth from purchases"""
        self.capital_growth = self.capital_purchase

    # ----------------------------------------
    # Getters / Setters (helpers)
    # ----------------------------------------
    def get_actual_production(self):
        return self.actual_production

    def get_average_production_cost(self):
        return self.average_production_cost

    def getPrice(self):
        return self.price

    def getNetProfit(self):
        return self.net_profit

    def update_capital_increase(self, value):
        self.capital_increase = np.max([0, value])

    def set_capital(self, capital):
        self.capital = capital

    def get_capital(self):
        return self.capital

    def get_capital_increase(self):
        return self.capital_increase

    def get_capital_demand(self):
        return self.capital_demand

    def set_capital_price(self, value):
        # firm will get this info when doing transaction, capital firm know their price
        # Capital goods firm sets this during transactions
        self.capital_price = value

    def getIdentity(self):
        return self.id

    def getLoan(self):
        return self.loanObtained

    def getPrice(self):
        return self.price

    def setPrice(self, price):
        self.price = price

    def getOwnerIncome(self):
        return self.ownerIncome

    def getDeposit(self):
        return self.deposit

    def setDeposit(self, deposit):
        self.deposit = deposit

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

    def getUseEnergy(self):
        return self.useEnergy

    def getSoldProducts(self):
        # For energy firms, "sold products" == actual production
        return self.get_actual_production()

    def set_actual_production(self, actual_production):
        self.actual_production = actual_production

    def get_actual_production(self):
        return self.actual_production

    def set_capital_investment(self, capital_investment):
        self.capital_investment = capital_investment

    def get_capital_investment(self):
        return self.capital_investment

    def set_energy_demand(self, energy_demand):
        self.energy_demand = energy_demand

    def get_energy_demand(self):
        return self.energy_demand

    def updateDeposit(self, value):
        # Only add positive inflows (outflows are handled explicitly)
        if value > 0:
            self.deposit += value

    def append2DepositList(self, deposit):
        self.depositList.append(deposit)
