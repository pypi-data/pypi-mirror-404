"""
CliMaPan-Lab: Climate-Pandemic Economic Modeling Laboratory
Main Economic Model Implementation

This module contains the core EconModel class that orchestrates the agent-based
simulation with climate and pandemic dynamics.
"""

import copy
import math
from collections import OrderedDict
from datetime import date, timedelta

import ambr as am

# Apply monkeypatch for ambr v0.1.5 compatibility
try:
    from . import ambr_patch
except ImportError:
    pass

import numpy as np

from .banks.Bank import Bank
from .climate import Climate
from .consumers.Consumer import Consumer
from .firms.BrownEnergyFirm import BrownEnergyFirm
from .firms.CapitalGoodsFirm import CapitalGoodsFirm
from .firms.ConsumerGoodsFirm import ConsumerGoodsFirm
from .firms.GreenEnergyFirm import GreenEnergyFirm
from .governments.Goverment import Government
from .utils import _merge_edgelist, gini, listToArray, lognormal, normal

# ============================================================================
#                              EconModel
# ============================================================================
# Purpose:
#   Quick "follow-through" of the full model loop so a reader can
#   understand where each subsystem fits (economy, COVID, climate,
#   finance, government).
#
# Time scale:
#   - One model step = 1 day.
#   - "Monthly" blocks run on the day before rollover to day 1 (i.e., when tomorrow is the 1st).
#
# Main Flow:
#   0) setup(): Initialize agents and state
#   1) step(): Daily execution with monthly economic cycles
#   2) update(): Record metrics for analysis
#   3) Helper routines: Markets, COVID, climate, policy
# ============================================================================


class EconModel(am.Model):

    def setup(self):
        """Initialize the agents and network of the model."""

        # ----------------------------------------
        # Global / simulation-wide state
        # ----------------------------------------

        # Initiate variables
        np.random.seed(self.p.seed)

        # --- Population composition counters ---
        self.num_worker = 0
        self.num_owner = 0

        # --- Prices / inflation / consumption variance ---
        self.fossil_fuel_price = self.p.fossil_fuel_price
        # self.expectedInflationRate = self.p.bankCredibility * self.p.targetInflation
        self.consumption_var = self.p.consumption_var
        # self.expectedInflationRateList = []
        self.averagePriceList = [0.5]

        # --- Firm failure / bankruptcy bookkeeping ---
        self.numCSFirmBankrupt = 0
        self.numCPFirmBankrupt = 0
        self.bankrupt_count = 0
        self.bankrupt_list = []
        self.bankrupt_total_count = 0

        # --- Banking & taxes ---
        self.bankIL = self.p.bankIL
        self.inflationRate = 0
        self.totalCarbonTaxes = 0
        self.totalTaxes = 0
        self.inflationRateList = []

        # --- Pandemic policy state ---
        self.covidState = False
        self.lockdown = False
        self.lockdown_scale = self.p.lock_down_production_utilization

        # --- Fiscal policy triggers ---
        self.fiscalDate = np.inf
        self.fiscal_count = 0

        # --- Epidemiological aggregates (daily resolution) ---
        self.num_infection = 0
        self.num_death = 0
        self.num_susceptible = 0
        self.num_exposed = 0
        self.num_mild = 0
        self.num_severe = 0
        self.num_critical = 0
        self.num_recover = 0
        # self.covid_infect = 0
        self.covid_death = 0
        self.covid_new = 0

        # --- Accounting aggregates ---
        self.total_good = 0
        self.sale = 0
        self.ksale = 0
        self.cssale = 0
        self.expenditure = 0
        self.ue_gov = 0

        # --- Calendrical state ---
        self.month_no = 0
        self.demand_fluctuation = 0

        # --- Initial endowments & policy multipliers ---
        self.owner_endownment = self.p.owner_endownment
        self.worker_endownment = self.p.worker_endownment
        self.alpha_h = self.p.alpha_h
        self.alpha_f = self.p.alpha_f

        # ----------------------------------------
        # Agent creation and attributes
        # ----------------------------------------

        ## Initiate consumer agents
        self.consumer_agents = am.AgentList(self, self.p.c_agents, Consumer)

        # Assign age groups with small random deviations
        # Vectorized age group assignment
        rands = np.random.normal(0, 0.1, len(self.consumer_agents))

        self.consumer_agents.select(rands < -0.1).call("setAgeGroup", "young")
        self.consumer_agents.select(rands > 0.15).call("setAgeGroup", "elderly")
        self.consumer_agents.select((rands >= -0.1) & (rands <= 0.15)).call(
            "setAgeGroup", "working"
        )

        # Assign working-age consumers into economic roles
        count = 0
        self.workingAgeConsumers = [
            idx
            for idx in range(len(self.consumer_agents))
            if self.consumer_agents[idx].getAgeGroup() == "working"
        ]
        for i in self.workingAgeConsumers:
            if count < self.p.capitalists:
                # Capitalists (general owners of CS/CP firms)
                self.consumer_agents[i].setConsumerType("capitalists")
                self.consumer_agents[i].owner = self.consumer_agents[
                    i
                ].consumerType not in ["workers", None]
                self.consumer_agents[i].update_deposit(self.owner_endownment)
                self.num_owner += 1
            elif count < self.p.capitalists + self.p.green_energy_owners:
                # Owners of GREEN energy sector
                self.consumer_agents[i].setConsumerType("green_energy_owners")
                self.consumer_agents[i].owner = self.consumer_agents[
                    i
                ].consumerType not in ["workers", None]
                self.consumer_agents[i].update_deposit(self.owner_endownment)
                self.num_owner += 1
            elif (
                count
                < self.p.capitalists
                + self.p.green_energy_owners
                + self.p.brown_energy_owners
            ):
                # Owners of BROWN energy sector
                self.consumer_agents[i].setConsumerType("brown_energy_owners")
                self.consumer_agents[i].owner = self.consumer_agents[
                    i
                ].consumerType not in ["workers", None]
                self.consumer_agents[i].update_deposit(self.owner_endownment)
                self.num_owner += 1
            else:
                # Residual working-age consumers become workers
                self.consumer_agents[i].setConsumerType("workers")
                self.num_worker += 1
                self.consumer_agents[i].update_deposit(self.worker_endownment)
            count += 1

        # Alive (non-dead) population view
        self.aliveConsumers = self.consumer_agents.select(
            self.consumer_agents.getCovidStateAttr("state") != "dead"
        )
        self.aliveConsumers = self.aliveConsumers.select(
            self.aliveConsumers.isDead() != True
        )

        ## Initiate bank agents
        self.bank_agents = am.AgentList(self, 1, Bank)

        ## Initiate Government agents
        self.government_agents = am.AgentList(self, self.p.g_agents, Government)

        ## Initiate firm agents

        ### Consumption goods firms (CS)
        self.csfirm_agents = am.AgentList(self, self.p.csf_agents, ConsumerGoodsFirm)
        # Ensure we have at least one of each energy type if we have multiple firms
        if len(self.csfirm_agents) >= 2:
            # Assign first firm to brown, second to green, rest randomly
            self.csfirm_agents[0].useEnergyType("brown")
            self.csfirm_agents[0].brown_firm = True
            self.csfirm_agents[1].useEnergyType("green")
            self.csfirm_agents[1].brown_firm = False

            # Vectorized assignment for remainder
            rest_agents = am.AgentList(self, self.csfirm_agents[2:])
            if len(rest_agents) > 0:
                probs = np.random.uniform(0, 1, len(rest_agents))
                brown_mask = probs < 0.5

                brown_agents = rest_agents.select(brown_mask)
                brown_agents.call("useEnergyType", "brown")
                for agent in brown_agents:
                    agent.brown_firm = True  # Manual attribute update

                green_agents = rest_agents.select(~brown_mask)
                green_agents.call("useEnergyType", "green")
                for agent in green_agents:
                    agent.brown_firm = False
        else:
            # Single firm random assignment
            if np.random.uniform(0, 1) < 0.5:
                self.csfirm_agents.call("useEnergyType", "brown")
                for agent in self.csfirm_agents:
                    agent.brown_firm = True
            else:
                self.csfirm_agents.call("useEnergyType", "green")
                for agent in self.csfirm_agents:
                    agent.brown_firm = False

        ### Capital goods firms (CP)
        self.cpfirm_agents = am.AgentList(self, self.p.cpf_agents, CapitalGoodsFirm)
        # Ensure we have at least one of each energy type if we have multiple firms
        # Ensure we have at least one of each energy type if we have multiple firms
        if len(self.cpfirm_agents) >= 2:
            # Assign first firm to brown, second to green, rest randomly
            self.cpfirm_agents[0].useEnergyType("brown")
            self.cpfirm_agents[0].capital = 5000
            self.cpfirm_agents[0].brown_firm = True

            self.cpfirm_agents[1].useEnergyType("green")
            self.cpfirm_agents[1].capital = 4200
            self.cpfirm_agents[1].brown_firm = False

            # Vectorized assignment for remainder
            rest_agents = am.AgentList(self, self.cpfirm_agents[2:])
            if len(rest_agents) > 0:
                probs = np.random.beta(3, 7, len(rest_agents))
                brown_mask = probs < 0.5

                brown_agents = rest_agents.select(brown_mask)
                brown_agents.call("useEnergyType", "brown")
                for agent in brown_agents:
                    agent.capital = 5000
                    agent.brown_firm = True

                green_agents = rest_agents.select(~brown_mask)
                green_agents.call("useEnergyType", "green")
                for agent in green_agents:
                    agent.capital = 4200
                    agent.brown_firm = False
        else:
            # Single firm random assignment
            if np.random.beta(3, 7) < 0.5:
                self.cpfirm_agents.call("useEnergyType", "brown")
                for agent in self.cpfirm_agents:
                    agent.capital = 5000
                    agent.brown_firm = True
            else:
                self.cpfirm_agents.call("useEnergyType", "green")
                for agent in self.cpfirm_agents:
                    agent.capital = 4200
                    agent.brown_firm = False

        ### Energy firms
        self.greenEFirm = am.AgentList(self, 1, GreenEnergyFirm)
        self.brownEFirm = am.AgentList(self, 1, BrownEnergyFirm)

        # Cluster goods firms
        self.firms = self.csfirm_agents + self.cpfirm_agents
        self.totalFirms = self.firms + self.greenEFirm + self.brownEFirm

        # ----------------------------------------
        # National accounts initialization
        # ----------------------------------------
        self.GDP = 0
        for firm in self.totalFirms:
            self.GDP += np.sum([firm.getSoldProducts() * firm.getPrice()])
            self.sale += np.sum([firm.getSoldProducts() * firm.getPrice()])
        for firm in self.csfirm_agents:
            self.cssale += np.sum([firm.getSoldProducts() * firm.getPrice()])
        for firm in self.cpfirm_agents:
            self.ksale += np.sum([firm.getSoldProducts() * firm.getPrice()])
        self.GDP += np.sum([self.expenditure])

        # ----------------------------------------
        # Climate module (optional)
        # ----------------------------------------
        if self.p.climateModuleFlag:
            self.climateModule = am.AgentList(self, 1, Climate)
            self.climateShockMode = copy.deepcopy(self.p.climateShockMode)
            self.climateModule.initGDP(self.GDP)

        # ----------------------------------------
        # Initial values at time 0
        # ----------------------------------------
        self.gini = gini(
            np.array(
                [(self.consumer_agents.getWage()) + (self.consumer_agents.getIncome())]
            )
        )
        self.consumption_gini = gini(np.array(self.consumer_agents.getConsumption()))
        self.fossil_fuel_price = copy.copy(self.p.fossil_fuel_price)
        self.today = date.fromisoformat(self.p.start_date) + timedelta(days=self.t - 1)
        self.tomorrow = self.today + timedelta(days=1)

        # ----------------------------------------
        # Epidemic and fiscal policy timing
        # ----------------------------------------
        if not self.p.covid_settings:
            self.covidStartDate = np.inf
            self.fiscalDate = np.inf
        else:
            self.covidStartDate = (
                date.fromisoformat(self.p.covid_start_date)
                - date.fromisoformat(self.p.start_date)
            ).days  # 7305
            if self.p.settings in ["BAIL", "INJECTION", "S2BAU", "S3MOD"]:
                self.fiscalDate = self.p.fiscal_time + self.covidStartDate
            else:
                self.fiscalDate = np.inf

    def step(self):
        """Define the models' events per simulation step."""
        self.initiate_step()

        # Check end of month
        # Before COVID start date: only run monthly blocks on month rollover
        if self.t <= self.covidStartDate:
            if int(str(self.tomorrow).split("-")[-1]) == 1:
                self.month_no += 1
                self.stepwise_forecast()
                self.stepwise_produce()
                self.stepwise_after_production()
                self.stepwise_termination()
        else:
            # After COVID starts: daily epidemic updates + monthly economic cycles
            if not int(str(self.tomorrow).split("-")[-1]) == 1:
                # Within-month day: only propagate COVID
                if self.num_infection != 0:
                    self._propagate_covid()
            else:
                # Month rollover: run full economic cycle
                self.month_no += 1
                self.stepwise_forecast()
                self.stepwise_produce()
                self.stepwise_after_production()
                # Trigger discretionary fiscal policy for selected scenarios
                if (
                    (self.t >= self.fiscalDate)
                    and self.p.covid_settings
                    and self.p.settings in ["BAIL", "INJECTION", "S2BAU", "S3MOD"]
                    and self.fiscal_count < 3
                ):
                    self.fiscal_count += 1
                    self._fiscal_policy()
                    print("implement fiscal policy")
                self.stepwise_termination()

    def initiate_step(self):
        """
        This internal function of the model is used to reset temporary variables or
        to accumulate variable every step
        """
        # Advance calendar
        self.today += timedelta(days=1)
        self.tomorrow += timedelta(days=1)

        # Refresh alive population views
        self.aliveConsumers = self.aliveConsumers.select(
            self.aliveConsumers.getCovidStateAttr("state") != "dead"
        )
        self.aliveConsumers = self.aliveConsumers.select(
            self.aliveConsumers.isDead() != True
        )
        self.workingAgeConsumers = [
            idx
            for idx in range(len(self.aliveConsumers))
            if self.aliveConsumers[idx].getAgeGroup() == "working"
        ]

        # Daily demand fluctuation
        self.demand_fluctuation = normal(1, self.consumption_var)

        # Reset fiscal aggregates
        self.totalCarbonTaxes = 0
        self.totalTaxes = 0
        self.bank_agents.reset_bank()

        [self.csfirm_agents[i].setTax(0) for i in range(len(self.csfirm_agents))]
        [self.cpfirm_agents[i].setTax(0) for i in range(len(self.cpfirm_agents))]

        # Monthly fossil fuel price growth
        if int(str(self.tomorrow).split("-")[-1]) == 1:
            self.fossil_fuel_price *= np.sum(1 + self.p.fossil_fuel_price_growth_rate)

        # Check covid start date
        if self.t == self.covidStartDate:
            self.covidState = True
            self._init_covid_exposure()

        # Reset contact every new day
        if self.p.covid_settings:
            # Count epidemiological states efficiently
            from collections import Counter

            states = [c.covidState["state"] for c in self.aliveConsumers]
            counts = Counter(states)

            self.num_susceptible = counts["susceptible"]
            self.num_exposed = counts["exposed"]
            self.num_mild = counts["mild"]
            self.num_severe = counts["severe"]
            self.num_critical = counts["critical"]
            self.num_recover = counts["recovered"] + counts["immunized"]
            self.num_death = counts["dead"]

            # Total infection (all except susceptible, recovered, immunized, dead, None)
            # effectively: exposed + mild + severe + critical + infected non-sympotomatic
            self.num_infection = (
                counts["exposed"]
                + counts["mild"]
                + counts["severe"]
                + counts["critical"]
                + counts["infected non-sympotomatic"]
            )

        # Terminate or continue Covid State:
        # print("covid state", self.covidState)
        if self.p.covid_settings:
            if (self.num_infection / self.p.c_agents) <= 0.002:
                self.covidState = False
            else:
                self.covidState = True

    def stepwise_forecast(self):
        """
        This internal function of the model is used to make forecast for some of the
        agents for the upcoming time step, if neccessary
        """

        # Firm forecasting demand
        self._csf_forecast_demand()
        self._cpf_forecast_demand()
        [
            self.csfirm_agents[i].calculate_input_demand()
            for i in range(len(self.csfirm_agents))
        ]
        [
            self.cpfirm_agents[i].calculate_input_demand()
            for i in range(len(self.cpfirm_agents))
        ]
        if self.t > 31:
            [
                self.csfirm_agents[i].production_budgeting()
                for i in range(len(self.csfirm_agents))
            ]
            [
                self.cpfirm_agents[i].production_budgeting()
                for i in range(len(self.cpfirm_agents))
            ]

        # Energy firm demand
        self._energy_demand()

        self.brownEFirm.calculate_input_demand()
        self.greenEFirm.calculate_input_demand()
        if self.t > 1:
            self.brownEFirm.production_budgeting()
            self.greenEFirm.production_budgeting()

        # Consumer Demand
        if self.t > 31:
            for i in self.workingAgeConsumers:
                self.aliveConsumers[i].desired_C()

    def stepwise_produce(self):
        """
        This internal function of the model is used to propagate the production of the firm
        agents
        """

        # Energy market opens
        self.brownEFirm.produce()
        self.greenEFirm.produce()
        self.brownEFirm.price_setting()
        self.greenEFirm.price_setting()

        # Labour market opens
        self._hire()

        # Check covid start date
        if self.t > self.covidStartDate and self.num_infection != 0:
            self._propagate_covid()
        # [firm.hire() for firm in np.random.permutation(self.firms)]

        # We probably need a function to make sure unemployed ppl receive benefit here

        # Goods and Capital firm opens
        [self.csfirm_agents[i].produce() for i in range(len(self.csfirm_agents))]
        [self.cpfirm_agents[i].produce() for i in range(len(self.cpfirm_agents))]

        # Scenario S3MOD: temporary lumpsum that raises green CS output
        if (
            (self.t >= self.fiscalDate)
            and self.p.covid_settings
            and self.p.settings == "S3MOD"
            and self.fiscal_count < 3
        ):
            print(
                len(
                    self.csfirm_agents.select(
                        self.csfirm_agents.getUseEnergy() == "green"
                    )
                )
            )
            for i in range(
                len(
                    self.csfirm_agents.select(
                        self.csfirm_agents.getUseEnergy() == "green"
                    )
                )
            ):
                print("lumpsum_update")
                print(self.csfirm_agents[i].get_actual_production())
                self.csfirm_agents[i].update_actual_production(
                    self.p.lumpSum / self.csfirm_agents[i].getPrice()
                )
                print(self.csfirm_agents[i].get_actual_production())

    def stepwise_after_production(self, eps=1e-8):
        """
        This internal function of the model is used to do jobs after production
        """

        # Firms transaction and accounting

        self.bank_agents.sommaW()
        [self.csfirm_agents[i].price_setting() for i in range(len(self.csfirm_agents))]
        [self.cpfirm_agents[i].price_setting() for i in range(len(self.cpfirm_agents))]
        self._csf_transaction()
        self._cpf_transaction()

        # CS firms: profits, capital updates, NPL accounting
        for i in range(len(self.csfirm_agents)):
            self.csfirm_agents[i].compute_net_profit()
            self.csfirm_agents[i].update_capital_growth()

            self.bank_agents.NPL += self.csfirm_agents[i].non_loan
            self.bank_agents.profit -= (1 + self.bankIL) * self.csfirm_agents[
                i
            ].non_loan
            self.csfirm_agents[i].reset_non_loan()

        # CP firms: profits, capital updates, NPL accounting
        for i in range(len(self.cpfirm_agents)):
            self.cpfirm_agents[i].compute_net_profit()
            self.cpfirm_agents[i].update_capital_growth()

            self.bank_agents.NPL += self.cpfirm_agents[i].non_loan
            self.cpfirm_agents[i].reset_non_loan()
        self.bank_agents.profit -= (1 + self.bankIL) * self.csfirm_agents[i].non_loan

        if self.p.verboseFlag:
            print("____bank profit", self.bank_agents.profit)
            print("___bank DTE", self.bank_agents.DTE)
            # print("capital firm growth", self.cpfirm_agents[i].capital, self.cpfirm_agents[i].capital_growth)
            print("total non loan", self.bank_agents.NPL)

        # Energy firms: profits and capital growth
        self.brownEFirm.compute_net_profit()
        self.greenEFirm.compute_net_profit()
        self.brownEFirm.update_capital_growth()
        self.greenEFirm.update_capital_growth()
        self.totalFirms.update_capital_value()

        ## Accounting owner's income
        self.capitalistsIncome = (
            (
                sum([i for i in self.cpfirm_agents.getOwnerIncome() if i >= 0])
                + sum([i for i in self.csfirm_agents.getOwnerIncome() if i >= 0])
            )
            / self.p.capitalists
            * (1 - self.p.incomeTaxRate)
        )
        # print("capitalist income", self.capitalistsIncome)
        self.totalTaxes += (
            (
                sum([i for i in self.cpfirm_agents.getOwnerIncome() if i >= 0])
                + sum([i for i in self.csfirm_agents.getOwnerIncome() if i >= 0])
            )
            / self.p.capitalists
            * self.p.incomeTaxRate
        )
        self.greenEnergyOwnersIncome = (
            (sum([i for i in self.greenEFirm.getOwnerIncome() if i >= 0]))
            / self.p.green_energy_owners
            * (1 - self.p.incomeTaxRate)
        )
        self.totalTaxes += (
            (sum([i for i in self.greenEFirm.getOwnerIncome() if i >= 0]))
            / self.p.green_energy_owners
            * self.p.incomeTaxRate
        )
        # print("green income", self.greenEnergyOwnersIncome)
        self.brownEnergyOwnersIncome = (
            (sum([i for i in self.brownEFirm.getOwnerIncome() if i >= 0]))
            / self.p.brown_energy_owners
            * (1 - self.p.incomeTaxRate)
        )
        # print("brown income", self.brownEnergyOwnersIncome)
        self.totalTaxes += (
            (sum([i for i in self.brownEFirm.getOwnerIncome() if i >= 0]))
            / self.p.brown_energy_owners
            * self.p.incomeTaxRate
        )

        ## Climate progression
        if self.p.climateModuleFlag:
            self.climateModule.progress(self.totalFirms)
            self._induce_climate_shock()
            if self.t == 31:
                self.climateModule.initAggregatedIncome()

        ## Accounting taxes and corresponding policies
        self._carbon_tax_policy()
        self.government_agents.update_budget(self.totalTaxes)

        ## Accounting consumers
        for i in self.workingAgeConsumers:
            if self.aliveConsumers[i].getConsumerType() == "capitalists":
                self.aliveConsumers[i].setDiv(self.capitalistsIncome)
            elif (
                self.p.energySectorFlag
                and self.aliveConsumers[i].getConsumerType() == "green_energy_owners"
            ):
                self.aliveConsumers[i].setDiv(self.greenEnergyOwnersIncome)
            elif (
                self.p.energySectorFlag
                and self.aliveConsumers[i].getConsumerType() == "brown_energy_owners"
            ):
                self.aliveConsumers[i].setDiv(self.brownEnergyOwnersIncome)
        self.aliveConsumers.update_wealth()  # this might be wrong, pay attention

    def stepwise_termination(self):
        """
        This internal function of the model is used to clean up and summarize stepwise variables
        """

        self.bankrupt_count = 0
        ## Check firms insolvency and update firms after bankruptcy, and bank injection
        if self.t > 365:

            self.csfirm_agents.setBankruptcy()
            self.cpfirm_agents.setBankruptcy()

        if len(self.bankrupt_list) > 11:
            self.bankrupt_list.pop(0)
        self.bankrupt_list.append(self.bankrupt_count)
        self.bankrupt_total_count = np.sum(self.bankrupt_list)
        # print(self.bankrupt_total_count)

        ## Bank and Government accounting
        self.expenditure = np.sum(self.government_agents.E_Gov())
        self.ue_gov = np.sum(self.government_agents.UE_Gov())

        # Rebuild national accounts
        self.GDP = 0
        self.cssale = 0
        self.ksale = 0

        for firm in self.totalFirms:
            self.GDP += np.sum([firm.getSoldProducts() * firm.getPrice()])
        for firm in self.csfirm_agents:
            self.cssale += np.sum([firm.getSoldProducts() * firm.getPrice()])
        for firm in self.cpfirm_agents:
            self.ksale += np.sum([firm.getSoldProducts() * firm.getPrice()])

        self.GDP += np.sum([self.expenditure])

        # Update inequality metrics
        income_combined = (
            self.aliveConsumers.getWage() + self.aliveConsumers.getIncome()
        )
        self.gini = gini(income_combined)
        self.consumption_gini = gini(self.aliveConsumers.getConsumption())

        # Reset lockdown flags
        self.csfirm_agents.resetLockDown()
        self.cpfirm_agents.resetLockDown()

    def update(self, eps=1e-8):
        """Record metrics for analysis"""
        super().update()
        if int(str(self.tomorrow).split("-")[-1]) == 1:
            # Monthly recording of all major indicators
            # Record date as string for better compatibility
            self.record("date", str(self.today))
            self.record("GDP", float(self.GDP))  # Ensure float scalar
            self.record("Gini", float(self.gini))  # Ensure float scalar
            self.record("People", int(len(self.aliveConsumers)))
            self.record("Gini Consumption", float(self.consumption_gini))

            # For array-like data, convert to Python lists to avoid Polars/numpy interaction issues with sparse data
            # ambr handles list of lists better than list of numpy arrays mixed with None
            self.record(
                "UnemplDole",
                listToArray(self.aliveConsumers.getWage())[
                    self.aliveConsumers.getWage() == self.p.unemploymentDole
                ].tolist(),
            )
            self.record("Unemployment Expenditure", float(self.ue_gov))
            self.record(
                "Owners Income", listToArray(self.aliveConsumers.getDiv()).tolist()
            )
            self.record("Wage", listToArray(self.aliveConsumers.getWage()).tolist())
            # self.record('Average Income', listToArray( np.mean(self.aliveConsumers.getIncome())))
            self.record(
                "Employed", listToArray(self.aliveConsumers.isEmployed()).tolist()
            )
            self.record(
                "Consumer Type",
                listToArray(self.aliveConsumers.getConsumerType()).tolist(),
            )
            self.record(
                "UnemploymentRate",
                float(
                    np.sum(
                        listToArray(self.aliveConsumers.getUnemploymentState()), axis=0
                    )
                    / (self.p.c_agents - self.num_owner)
                ),
            )
            self.record(
                "Consumption",
                listToArray(self.aliveConsumers.getConsumption()).tolist(),
            )
            self.record(
                "Desired Consumption",
                listToArray(self.aliveConsumers.get_desired_consumption()).tolist(),
            )

            # Bank metrics
            self.record("Loans", listToArray(self.bank_agents.loans).tolist())
            self.record(
                "Bank totalLoanSupply",
                listToArray(self.bank_agents.totalLoanSupply).tolist(),
            )
            self.record("Bank Equity", listToArray(self.bank_agents.equity).tolist())
            self.record(
                "Bank Deposits", listToArray(self.bank_agents.deposits).tolist()
            )
            self.record(
                "Bank LDR",
                listToArray(
                    self.bank_agents.loans / (self.bank_agents.deposits + eps)
                ).tolist(),
            )
            self.record(
                "Bank Loan Demands",
                listToArray(self.bank_agents.totalLoanDemands).tolist(),
            )
            self.record(
                "Bank Loan Over Equity",
                listToArray(
                    self.bank_agents.actualSuppliedLoan
                    / (self.bank_agents.equity + eps)
                ).tolist(),
            )
            self.record("Bank DTE", listToArray(self.bank_agents.DTE).tolist())
            self.record(
                "Non Performing Loan", listToArray(self.bank_agents.NPL).tolist()
            )
            # self.record('Expected Inflation Rate', listToArray(self.expectedInflationRateList))
            self.record("Inflation Rate", listToArray(self.inflationRateList).tolist())
            self.record(
                "Total Loan Demand",
                listToArray(self.bank_agents.totalLoanDemands).tolist(),
            )

            # CS Firm metrics
            self.record("CS Num Bankrupt", int(self.numCSFirmBankrupt))
            self.record(
                "CS V Cost",
                listToArray(self.csfirm_agents.get_average_production_cost()).tolist(),
            )
            self.record(
                "CS U Cost",
                listToArray(self.csfirm_agents.get_average_production_cost()).tolist(),
            )
            self.record(
                "CS Firm Loans", listToArray(self.csfirm_agents.loanObtained).tolist()
            )
            self.record(
                "CS Net Profits", listToArray(self.csfirm_agents.net_profit).tolist()
            )
            self.record(
                "CS Capital", listToArray(self.csfirm_agents.get_capital()).tolist()
            )
            self.record(
                "CS Net Worth", listToArray(self.csfirm_agents.getNetWorth()).tolist()
            )
            self.record(
                "CS Number of Workers",
                listToArray(self.csfirm_agents.countWorkers).tolist(),
            )
            self.record(
                "CS Number of Consumers",
                listToArray(self.csfirm_agents.countConsumers).tolist(),
            )
            self.record("CS Price", listToArray(self.csfirm_agents.getPrice()).tolist())
            self.record(
                "CS Sold Products",
                listToArray(self.csfirm_agents.getSoldProducts()).tolist(),
            )
            self.record("CS Sale", listToArray(self.cssale).tolist())
            self.record("CS iL", listToArray(self.csfirm_agents.iL).tolist())
            self.record("CS iF", listToArray(self.csfirm_agents.iF).tolist())
            self.record(
                "CS Loan Obtained",
                listToArray(self.csfirm_agents.loanObtained).tolist(),
            )
            self.record(
                "CS Deposit", listToArray(self.csfirm_agents.getDeposit()).tolist()
            )
            self.record(
                "CS Margin", listToArray(self.csfirm_agents.profit_margin).tolist()
            )
            self.record(
                "CS Capital Investment",
                listToArray(self.csfirm_agents.get_capital_investment()).tolist(),
            )
            self.record(
                "CS Production Cost",
                listToArray(
                    self.csfirm_agents.get_average_production_cost()
                    * self.csfirm_agents.get_actual_production()
                ).tolist(),
            )
            self.record(
                "CS Capacity",
                listToArray(self.csfirm_agents.get_actual_production()).tolist(),
            )
            self.record(
                "CS Wage Bill", listToArray(self.csfirm_agents.wage_bill).tolist()
            )
            self.record(
                "CS Loan Payment", listToArray(self.csfirm_agents.payback).tolist()
            )
            self.record(
                "CS Credit Default Risk",
                listToArray(self.csfirm_agents.defaultProb).tolist(),
            )

            # CP Firm metrics
            self.record(
                "CP Credit Default Risk",
                listToArray(self.cpfirm_agents.defaultProb).tolist(),
            )
            self.record("CP Num Bankrupt", int(self.numCPFirmBankrupt))
            self.record(
                "CP Firm Loans", listToArray(self.cpfirm_agents.loanObtained).tolist()
            )
            self.record(
                "CP Net Profits", listToArray(self.cpfirm_agents.net_profit).tolist()
            )
            self.record(
                "CP Net Worth", listToArray(self.cpfirm_agents.getNetWorth()).tolist()
            )
            self.record(
                "CP Capital", listToArray(self.cpfirm_agents.get_capital()).tolist()
            )
            self.record("CP Price", listToArray(self.cpfirm_agents.getPrice()).tolist())
            self.record(
                "CP Sold Products",
                listToArray(self.cpfirm_agents.getSoldProducts()).tolist(),
            )
            self.record("CP Sale", listToArray(self.ksale).tolist())
            self.record(
                "CP Number of Workers",
                listToArray(self.cpfirm_agents.countWorkers).tolist(),
            )
            self.record(
                "CP Number of Consumers",
                listToArray(self.cpfirm_agents.countConsumers).tolist(),
            )
            self.record(
                "CP V Cost",
                listToArray(self.cpfirm_agents.get_average_production_cost()).tolist(),
            )
            self.record(
                "CP U Cost",
                listToArray(self.cpfirm_agents.get_average_production_cost()).tolist(),
            )
            self.record("CP iL", listToArray(self.cpfirm_agents.iL).tolist())
            self.record("CP iF", listToArray(self.cpfirm_agents.iF).tolist())
            self.record(
                "CP Loan Obtained",
                listToArray(self.cpfirm_agents.loanObtained).tolist(),
            )
            self.record(
                "CP Deposit", listToArray(self.cpfirm_agents.getDeposit()).tolist()
            )
            self.record(
                "CP Production Cost",
                listToArray(
                    self.cpfirm_agents.get_average_production_cost()
                    * self.cpfirm_agents.get_actual_production()
                ).tolist(),
            )
            self.record(
                "CP Capacity",
                listToArray(self.cpfirm_agents.get_actual_production()).tolist(),
            )
            self.record(
                "CP Wage Bill", listToArray(self.cpfirm_agents.wage_bill).tolist()
            )
            self.record(
                "CP Loan Payment", listToArray(self.cpfirm_agents.payback).tolist()
            )

            # Governments
            self.record(
                "Fiscal Policy", listToArray(self.government_agents.fiscal).tolist()
            )
            self.record("Expenditures", listToArray(self.expenditure).tolist())
            self.record("Total Taxes", listToArray(self.totalTaxes).tolist())
            self.record("Budget", listToArray(self.government_agents.budget).tolist())

            # Covid
            self.record("Deaths", listToArray(self.covid_death).tolist())

            # Investments
            greenCapitalMeanPrice = np.mean(
                list(
                    self.cpfirm_agents.select(
                        self.cpfirm_agents.getUseEnergy() == "green"
                    ).getPrice()
                )
            )
            brownCapitalMeanPrice = np.mean(
                list(
                    self.cpfirm_agents.select(
                        self.cpfirm_agents.getUseEnergy() == "brown"
                    ).getPrice()
                )
            )
            greenInvestment = greenCapitalMeanPrice * (
                np.sum(
                    [
                        self.csfirm_agents.select(
                            self.csfirm_agents.getUseEnergy() == "green"
                        ).get_capital_investment()
                    ]
                )
                + np.sum(
                    [
                        self.cpfirm_agents.select(
                            self.cpfirm_agents.getUseEnergy() == "green"
                        ).get_capital_investment()
                    ]
                )
                + np.sum([self.greenEFirm.get_capital_investment()])
            )
            brownInvestment = brownCapitalMeanPrice * (
                np.sum(
                    [
                        self.csfirm_agents.select(
                            self.csfirm_agents.getUseEnergy() == "brown"
                        ).get_capital_investment()
                    ]
                )
                + np.sum(
                    [
                        self.cpfirm_agents.select(
                            self.cpfirm_agents.getUseEnergy() == "brown"
                        ).get_capital_investment()
                    ]
                )
                + np.sum([self.brownEFirm.get_capital_investment()])
            )
            self.record("Green Investments", greenInvestment)
            self.record("Brown Investments", brownInvestment)
            self.record("Investment", greenInvestment + brownInvestment)

            # Energy firms
            self.record("GE Net Profits", listToArray(self.greenEFirm.net_profit))
            self.record("GE Price", listToArray(self.greenEFirm.getPrice()))
            self.record(
                "GE Capital Demand", listToArray(self.greenEFirm.get_capital_demand())
            )
            self.record("GE Deposit", listToArray(self.greenEFirm.getDeposit()))
            self.record("BE Net Profits", listToArray(self.brownEFirm.net_profit))
            self.record("BE Price", listToArray(self.brownEFirm.getPrice()))
            self.record(
                "BE Capital Demand", listToArray(self.brownEFirm.get_capital_demand())
            )
            self.record("BE Deposit", listToArray(self.brownEFirm.getDeposit()))

            # Climate module
            if self.p.climateModuleFlag:
                self.record("Climate C02 Taxes", listToArray(self.totalCarbonTaxes))
                self.record("Climate C02", listToArray(self.climateModule.CO2))
                self.record("Climate EM", listToArray(self.climateModule.EM))
                self.record(
                    "Climate EM Stepwise", listToArray(self.climateModule.step_EM)
                )
                self.record(
                    "Climate C02 Concentration", listToArray(self.climateModule.conc_t)
                )
                self.record(
                    "Climate Radiative Forcing", listToArray(self.climateModule.RF)
                )
                self.record("Climate Temperature", listToArray(self.climateModule.T))

            # Data writers
            try:
                if (
                    len(self.bank_agents.bankDataWriter) > 0
                    and len(self.bank_agents.bankDataWriter[0]) > 0
                ):
                    self.record(
                        "BankDataWriter",
                        listToArray(self.bank_agents.bankDataWriter)[-1][-1],
                    )
                if (
                    len(self.csfirm_agents.firmDataWriter) > 0
                    and len(self.csfirm_agents.firmDataWriter[0]) > 0
                ):
                    self.record(
                        "CSFirmDataWriter",
                        listToArray(self.csfirm_agents.firmDataWriter)[-1][-1],
                    )
                if (
                    len(self.cpfirm_agents.firmDataWriter) > 0
                    and len(self.cpfirm_agents.firmDataWriter[0]) > 0
                ):
                    self.record(
                        "CPFirmDataWriter",
                        listToArray(self.cpfirm_agents.firmDataWriter)[-1][-1],
                    )
            except:
                self.record(
                    "BankDataWriter", listToArray(self.bank_agents.bankDataWriter)
                )
                self.record(
                    "CSFirmDataWriter", listToArray(self.csfirm_agents.firmDataWriter)
                )
                self.record(
                    "CPFirmDataWriter", listToArray(self.cpfirm_agents.firmDataWriter)
                )
        elif self.p.covid_settings is not None and self.t > self.covidStartDate:
            # Daily COVID recording
            self.record(
                "Covid State",
                listToArray(self.consumer_agents.getCovidStateAttr("state")),
            )
            self.record("Infection", listToArray(self.num_infection))
            self.record("Exposed", listToArray(self.num_exposed))
            self.record("Susceptible", listToArray(self.num_susceptible))
            self.record("Recover", listToArray(self.num_recover))
            self.record("Dead", listToArray(self.num_death))
            self.record("mild", listToArray(self.num_mild))
            self.record("severe", listToArray(self.num_severe))
            self.record("critical", listToArray(self.num_critical))

    def end(self):
        """Record evaluation measures at the end of the simulation."""

    # ========================================
    # Market Helper Routines
    # ========================================

    def _csf_forecast_demand(self):
        """Aggregate household desired consumption and distribute to CS firms"""
        # Vectorized aggregation: Select consumers by working age index list
        # self.workingAgeConsumers contains indices of working age consumers
        working_consumers = self.aliveConsumers[self.workingAgeConsumers]
        aggregated_demand = np.sum(working_consumers.get_desired_consumption())

        # Vectorized firm update: set demand proportional to market share
        self.csfirm_agents.call("prepareForecast")

        market_shares = self.csfirm_agents.market_share
        if isinstance(market_shares, list):
            market_shares = np.array(market_shares)

        demands = aggregated_demand * market_shares

        # Iterate to set since we don't have a direct vector setter for this specific calculation pattern yet
        # (Could use batch_update if we constructed a dict, but this loop is simple enough for now
        # given we need to multiply scalar * vector)
        for i, firm in enumerate(self.csfirm_agents):
            firm.set_aggregate_demand(demands[i])

    def _csf_transaction(self):
        """Consumer-goods market clearing: households buy from firms sorted by price"""
        self.total_good = 0
        ordered_price = OrderedDict()
        self.countConsumersPerCompanyC = {}

        # Build price list and reset sale records
        for i in range(len(self.csfirm_agents)):
            # set counter for # consumers per company
            self.countConsumersPerCompanyC[i] = 0
            ordered_price[i] = self.csfirm_agents[i].getPrice()
            self.csfirm_agents[i].set_sale_record(0)

        # lambda is mapping item to item[1]; the function indicates that we're sorting based on the price, not the name of the companies
        ordered_price = OrderedDict(
            sorted(ordered_price.items(), key=lambda item: item[1])
        )

        # Prepare ordered production by firm
        self.orderedCompaniesProductionC = OrderedDict()
        total_production = 0
        for (
            company,
            price,
        ) in (
            ordered_price.items()
        ):  # this will be wrong since we will reintroduce price later
            # print("sale price", price)
            if not self.csfirm_agents[company].lockdown:
                self.orderedCompaniesProductionC[company] = self.csfirm_agents[
                    company
                ].get_actual_production()
                total_production += self.orderedCompaniesProductionC[company]
                self.orderedCompaniesProductionC[
                    company
                ] *= self.demand_fluctuation ** (self.demand_fluctuation < 1)

        # Households purchase from cheapest firms first
        for i in np.random.permutation(self.workingAgeConsumers):
            aConsumer = self.aliveConsumers[i]
            aConsumer.setConsumption(0)
            purchase = 0
            desired_consumption = (
                aConsumer.get_desired_consumption() * self.demand_fluctuation
            )

            # Pre-calculate offset for firm ID mapping
            # The 'company' key in orderedCompaniesProductionC comes from loop index 'i' (0 to n_firms-1)
            # The code below previously searched for identity == company + offset
            # But wait, self.csfirm_agents is a list/sequence.
            # If 'company' is just the index 'i' from the first loop (line 1014),
            # then we can just access self.csfirm_agents[company] directly!

            # The original code used:
            # chosenFirm = self.csfirm_agents.select(getIdentity() - offset == company)
            # If company 'i' corresponds to csfirm_agents[i], then getIdentity() should match.

            # So 'company' IS the index.

            # Optimization: Direct access
            for company, production in self.orderedCompaniesProductionC.items():
                if purchase >= desired_consumption:
                    break

                chosenFirm = self.csfirm_agents[company]

                # Double check identity if paranoid, but structure implies index alignment
                # (The original code searched for identity - offset == company)

                if production == 0:
                    continue

                else:
                    price = ordered_price[company]
                    aConsumer.price = price
                    self.countConsumersPerCompanyC[company] += 1
                    # Budget-constrained purchase
                    if (production - desired_consumption) >= 0:
                        if price > 0:
                            purchase = np.max(
                                [
                                    np.min(
                                        [
                                            desired_consumption,
                                            (aConsumer.deposit + aConsumer.getIncome())
                                            / price,
                                        ]
                                    ),
                                    0,
                                ]
                            )
                        else:
                            purchase = desired_consumption
                        # if aConsumer.owner:
                        # print("purchase amount", purchase, (aConsumer.deposit + aConsumer.getIncome()) / price, desired_consumption, aConsumer.deposit, aConsumer.getIncome(), price, aConsumer.consumerType)
                        self.orderedCompaniesProductionC[company] = (
                            production - purchase
                        )
                        chosenFirm.updateSoldProducts(np.sum(purchase))
                        production -= np.sum(purchase)
                        actual_consumption = purchase
                        self.total_good += purchase
                    else:
                        # Partial fulfillment
                        self.orderedCompaniesProductionC[company] = 0
                        actual_consumption = production
                        chosenFirm.updateSoldProducts(np.sum(production))
                        self.total_good += production
                        production = 0

                    aConsumer.setConsumption(actual_consumption * price)
                    # print("consumer demand", aConsumer.desired_consumption, actual_consumption)
                    chosenFirm.update_sale_record(actual_consumption)
                break
            # print("total product sale", chosenFirm.getSoldProducts())
        if self.p.verboseFlag:
            print("total sale", self.total_good, total_production)

    def _cpf_forecast_demand(self):
        """Build brown/green capital demand from CS+Energy firms"""
        self.cpfirm_agents.call("prepareForecast")

        firmsList = self.csfirm_agents + self.brownEFirm + self.greenEFirm

        # Vectorized aggregation
        # Assuming `useEnergy` is an attribute 'brown' or 'green'
        use_energy = firmsList.useEnergy
        capital_demands = firmsList.get_capital_demand()  # Vectorized call

        # Check if returned as list or numpy array, convert if needed
        if isinstance(use_energy, list):
            use_energy = np.array(use_energy)
        if isinstance(capital_demands, list):
            capital_demands = np.array(capital_demands)

        b_mask = use_energy == "brown"
        b_aggregated_demand = np.sum(capital_demands[b_mask])
        g_aggregated_demand = np.sum(capital_demands[~b_mask])

        # Vectorized assignment
        # CP firms also have `useEnergy`
        cp_use_energy = self.cpfirm_agents.useEnergy
        if isinstance(cp_use_energy, list):
            cp_use_energy = np.array(cp_use_energy)

        cp_b_mask = cp_use_energy == "brown"

        # Set demands using loops for now to be safe until bulk setter is confirmed safe
        # self.cpfirm_agents.select(cp_b_mask).call("set_aggregate_demand", b_aggregated_demand)
        # self.cpfirm_agents.select(~cp_b_mask).call("set_aggregate_demand", g_aggregated_demand)

        for firm in self.cpfirm_agents:
            if firm.useEnergy == "brown":
                firm.set_aggregate_demand(b_aggregated_demand)
            else:
                firm.set_aggregate_demand(g_aggregated_demand)

    def _cpf_transaction(self):
        """Capital-goods market clearing: CP sells to CS+Energy firms"""
        self.firmsList = self.csfirm_agents + self.brownEFirm + self.greenEFirm
        for i in range(len(self.cpfirm_agents)):
            chosenFirm = self.cpfirm_agents[i]
            price = chosenFirm.getPrice()
            chosenFirm.set_sale_record(0)
            # print("capital price", price)
            K_production = chosenFirm.get_actual_production()

            for j in np.random.permutation(len(self.firmsList)):
                aFirm = self.firmsList[j]
                # Tech-matched transactions only
                if aFirm.useEnergy == self.cpfirm_agents[i].useEnergy:
                    aFirm = self.firmsList[j]
                    K_consumption = aFirm.get_capital_demand()
                    # print("K firm demand", K_consumption, K_production)
                    aFirm.set_capital_investment(0)

                    if K_consumption == 0:
                        break

                    if K_production == 0:
                        break

                    # Fulfill demand up to available production
                    if (K_production - K_consumption) >= 0:
                        chosenFirm.updateSoldProducts(np.sum(K_consumption))
                        K_production = K_production - K_consumption
                    else:
                        K_consumption = K_production
                        chosenFirm.updateSoldProducts(np.sum(K_production))
                        K_production = 0

                    aFirm.capital_purchase = K_consumption
                    aFirm.set_capital_investment(np.sum(K_consumption * price))
                    aFirm.set_capital_price(price)
                    chosenFirm.update_sale_record(K_consumption)
                    # print("machine sale", aFirm.capital_purchase)

    def _energy_demand(self):
        """Aggregate energy demand from CS+CP firms by technology"""
        b_aggregated_demand = 0
        g_aggregated_demand = 0

        self.firmsList = self.csfirm_agents + self.cpfirm_agents
        for i in np.random.permutation(len(self.firmsList)):
            aFirm = self.firmsList[i]
            if aFirm.useEnergy == "brown":
                b_aggregated_demand += aFirm.get_energy()
            else:
                g_aggregated_demand += aFirm.get_energy()

        self.brownEFirm.set_energy_demand(b_aggregated_demand)
        self.greenEFirm.set_energy_demand(g_aggregated_demand)

    # ========================================
    # COVID Helper Routines
    # ========================================

    def _make_random_contacts(self):
        """Generate random daily contacts in the community"""
        eps = 1e-8
        infection_rate = self.model.num_infection / (
            len(self.model.aliveConsumers) + eps
        )
        num_contacts_community = self.p.num_contacts_community
        dist = (infection_rate > self.p.inf_threshold) * (
            self.p.covid_settings == "DIST"
        )
        lock = self.lockdown
        if dist:
            num_contacts_community = self.p.num_contacts_community / 2
        if lock:
            num_contacts_community = self.p.num_contacts_community / 4
        # Preprocessing
        contact_list = dict()
        pop_size = int(len(self.aliveConsumers))  # Number of people
        if pop_size > 0:
            p1 = []  # Initialize the "sources"
            p2 = []  # Initialize the "targets"

            # Precalculate contacts
            n_all_contacts = int(
                pop_size * num_contacts_community * self.p.overshoot_community
            )  # The overshoot is used so we won't run out of contacts if the Poisson draws happen to be higher than the expected value
            all_contacts = np.random.choice(
                pop_size, n_all_contacts, replace=True
            )  # Choose people at random
            if self.p.dispersion_community is None:
                p_count = np.random.poisson(
                    num_contacts_community, pop_size
                )  # Draw the number of Poisson contacts for this person
            else:
                p_count = (
                    np.random.negative_binomial(
                        n=self.p.dispersion_community,
                        p=self.p.dispersion_community
                        / (num_contacts_community / 1 + self.p.dispersion_community),
                        size=pop_size,
                    )
                    * 1
                )  # Or, from a negative binomial
            p_count = np.array((p_count / 2.0).round(), dtype=np.int32)

            # Make contacts
            count = 0
            for p in range(pop_size):
                n_contacts = p_count[p]
                these_contacts = all_contacts[
                    count : count + n_contacts
                ]  # Assign people
                count += n_contacts
                p1.extend([p] * n_contacts)
                p2.extend(these_contacts)

            contact_list.update(_merge_edgelist(p1, p2, None))

        return contact_list

    def _make_random_contacts_in_firms(self):
        """Generate random daily contacts inside each firm"""
        eps = 1e-8
        infection_rate = self.model.num_infection / (
            len(self.model.aliveConsumers) + eps
        )
        num_contacts_firms = self.p.num_contacts_firms
        dist = (infection_rate > self.p.inf_threshold) * (
            self.p.covid_settings == "DIST"
        )
        if dist:
            num_contacts_firms = self.p.num_contacts_firms / 2
        contact_list = dict()
        for firm in self.firms:
            # Preprocessing
            pop_size = int(len(firm.workersList))  # Number of people
            if not firm.lockdown and pop_size > 0:
                p1 = []  # Initialize the "sources"
                p2 = []  # Initialize the "targets"

                # Precalculate contacts
                n_all_contacts = int(
                    pop_size * num_contacts_firms * self.p.overshoot_firms
                )  # The overshoot is used so we won't run out of contacts if the Poisson draws happen to be higher than the expected value
                all_contacts = np.random.choice(
                    pop_size, n_all_contacts, replace=True
                )  # Choose people at random
                if self.p.dispersion_firms is None:
                    p_count = np.random.poisson(
                        num_contacts_firms, pop_size
                    )  # Draw the number of Poisson contacts for this person
                else:
                    p_count = (
                        np.random.negative_binomial(
                            n=self.p.dispersion_firms,
                            p=self.p.dispersion_firms
                            / (num_contacts_firms / 1 + self.p.dispersion_firms),
                            size=pop_size,
                        )
                        * 1
                    )  # Or, from a negative binomial
                p_count = np.array((p_count / 2.0).round(), dtype=np.int32)

                # Make contacts
                count = 0
                for p in range(pop_size):
                    n_contacts = p_count[p]
                    these_contacts = all_contacts[
                        count : count + n_contacts
                    ]  # Assign people
                    count += n_contacts
                    p1.extend([p] * n_contacts)
                    p2.extend(these_contacts)

                if len(contact_list) > 0:
                    contact_list["p1"] = np.concatenate(
                        [
                            contact_list["p1"],
                            (_merge_edgelist(p1, p2, firm.workersList, 1)["p1"]),
                        ]
                    )
                    contact_list["p2"] = np.concatenate(
                        [
                            contact_list["p2"],
                            (_merge_edgelist(p1, p2, firm.workersList, 1)["p2"]),
                        ]
                    )
                else:
                    contact_list.update(_merge_edgelist(p1, p2, firm.workersList, 1))
            else:
                continue

        return contact_list

    def _propagate_contacts(self, contact_list_f, contact_list_c, eps=1e-8):
        """Spread infections through firm and community contacts"""
        contacts_firm = np.argwhere(contact_list_f["p1"] == self.id)
        contacts_community = np.argwhere(contact_list_c["p1"] == self.id)
        infected_contact_firm = self.model.aliveConsumers.select(
            [
                self.model.aliveConsumers.getIdentity()
                == contact_list_f["p2"][np.sum(el)]
                and self.model.aliveConsumers.getCovidStateAttr("state")
                in [
                    "exposed",
                    "infected non-sympotomatic",
                    "mild",
                    "severe",
                    "critical",
                ]
                for el in contacts_firm
            ]
        )
        infected_contact_community = self.model.aliveConsumers.select(
            [
                self.model.aliveConsumers.getIdentity()
                == contact_list_c["p2"][np.sum(el)]
                and self.model.aliveConsumers.getCovidStateAttr("state")
                in [
                    "exposed",
                    "infected non-sympotomatic",
                    "mild",
                    "severe",
                    "critical",
                ]
                for el in contacts_community
            ]
        )
        inf_f = len(infected_contact_firm)
        inf_c = len(infected_contact_community)
        infection_rate = self.model.num_infection / (
            len(self.model.aliveConsumers) + eps
        )
        p_firm = self.p.p_contact_firms * self.p.p_sd ** (
            (infection_rate > self.p.inf_threshold) * (self.p.covid_settings == "DIST")
        )
        p_community = self.p.p_contact_community * self.p.p_sd ** (
            (infection_rate > self.p.inf_threshold) * (self.p.covid_settings == "DIST")
        )
        # print("infection rate", infection_rate, "firm and community", p_firm, p_community)
        self.aliveConsumers.select(
            self.aliveConsumers.getCovidStateAttr("state") == "susceptible"
        ).propagateContact(inf_f, inf_c, p_firm, p_community)

    def _init_covid_exposure(self):
        """Initialize COVID states for population"""
        print("start covid")
        count = 0
        for i in range(len(self.aliveConsumers)):
            if self.aliveConsumers[i].getCovidStateAttr("state") == None:
                self.aliveConsumers[i].setCovidState("susceptible", self.t, None, None)
        for i in np.random.permutation(range(len(self.aliveConsumers))):
            count += 1
            if count <= self.p.initialExposer:
                self.aliveConsumers[i].setCovidState(
                    "mild",
                    self.t,
                    lognormal(self.p.T_mild_severe_mean, self.p.T_mild_severe_std),
                    "severe",
                )
            else:
                break

    def _propagate_covid(self, eps=1e-8):
        """Daily progression of COVID spread & lockdown policy enforcement"""
        # print("propagate covid")
        if self.p.covid_settings == "LOCK":
            if (
                self.num_infection / len(self.aliveConsumers) + eps
            ) > self.p.p_lockdown and not self.lockdown:
                # Trigger lockdown
                self.lockdownCount = 1
                self.lockdown = True
                count_C = 0
                count_K = 0
                for csfirm in np.random.permutation(self.csfirm_agents):
                    if (
                        count_C / len(self.csfirm_agents) + eps
                    ) < self.p.num_C_firms_LD:
                        csfirm.setLockDown()

                for cpfirm in np.random.permutation(self.cpfirm_agents):
                    if (
                        count_K / len(self.cpfirm_agents) + eps
                    ) < self.p.num_K_firms_LD:
                        cpfirm.setLockDown()
            else:
                if self.lockdown:
                    # Maintain lockdown
                    self.lockdownCount += 1
                    if self.lockdownCount >= self.p.duration_LD:
                        self.lockdown = False
                        self.csfirm_agents.unsetLockDown()
                        self.cpfirm_agents.unsetLockDown()
                else:
                    # Normal spread through contacts
                    contact_list1 = self._make_random_contacts()
                    contact_list2 = self._make_random_contacts_in_firms()
                    self._propagate_contacts(contact_list2, contact_list1)
        else:
            contact_list1 = self._make_random_contacts()
            contact_list2 = self._make_random_contacts_in_firms()
            self._propagate_contacts(contact_list2, contact_list1)

        self.aliveConsumers.progressCovid()

    # ========================================
    # Policy Helper Routines
    # ========================================

    def _carbon_tax_policy(self, eps=1e-8):
        """Carbon tax collection and redistribution"""
        self.totalCarbonTaxes += np.sum([firm.carbonTax for firm in self.totalFirms])
        self.totalTaxes += np.sum(list(self.csfirm_agents.getTax()))
        self.totalTaxes += np.sum(list(self.cpfirm_agents.getTax()))
        self.totalTaxes += np.sum(list(self.brownEFirm.getTax()))
        self.totalTaxes += np.sum(list(self.greenEFirm.getTax()))

        if self.p.settings.find("CTRa") != -1:
            # Lump-sum redistribution
            sharedCO2Tax = self.totalCarbonTaxes / (self.p.c_agents)
            self.capitalistsIncome += np.sum(sharedCO2Tax) * (
                self.p.capitalists
                - len(
                    self.aliveConsumers.select(
                        self.aliveConsumers.getConsumerType() == "capitalists"
                    )
                )
            )
            self.greenEnergyOwnersIncome += np.sum(sharedCO2Tax) * (
                self.p.green_energy_owners
                - len(
                    self.aliveConsumers.select(
                        self.aliveConsumers.getConsumerType() == "green_energy_owners"
                    )
                )
            )
            self.brownEnergyOwnersIncome += np.sum(sharedCO2Tax) * (
                self.p.brown_energy_owners
                - len(
                    self.aliveConsumers.select(
                        self.aliveConsumers.getConsumerType() == "brown_energy_owners"
                    )
                )
            )
        elif self.p.settings.find("CTR") != -1:
            redistributive_policy = (np.sum(self.totalCarbonTaxes) * self.p.co2_tax) / (
                self.GDP + eps
            )
            if self.p.settings.find("CTRb") != -1:
                # Proportional to income
                self.capitalistsIncome += np.sum(
                    self.capitalistsIncome * redistributive_policy
                ) * (
                    self.p.capitalists
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType() == "capitalists"
                        )
                    )
                )
                self.greenEnergyOwnersIncome += np.sum(
                    self.greenEnergyOwnersIncome * redistributive_policy
                ) * (
                    self.p.green_energy_owners
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType()
                            == "green_energy_owners"
                        )
                    )
                )
                self.brownEnergyOwnersIncome += np.sum(
                    self.brownEnergyOwnersIncome * redistributive_policy
                ) * (
                    self.p.brown_energy_owners
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType()
                            == "brown_energy_owners"
                        )
                    )
                )
            elif self.p.settings.find("CTRc") != -1:
                # Flat transfer based on average
                self.capitalistsIncome += np.sum(
                    redistributive_policy
                    * np.mean(
                        [self.aliveConsumers.getWage(), self.aliveConsumers.getIncome()]
                    )
                ) * (
                    self.p.capitalists
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType() == "capitalists"
                        )
                    )
                )
                self.greenEnergyOwnersIncome += np.sum(
                    redistributive_policy
                    * np.mean(
                        [self.aliveConsumers.getWage(), self.aliveConsumers.getIncome()]
                    )
                ) * (
                    self.p.green_energy_owners
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType()
                            == "green_energy_owners"
                        )
                    )
                )
                self.brownEnergyOwnersIncome += np.sum(
                    redistributive_policy
                    * np.mean(
                        [self.aliveConsumers.getWage(), self.aliveConsumers.getIncome()]
                    )
                ) * (
                    self.p.brown_energy_owners
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType()
                            == "brown_energy_owners"
                        )
                    )
                )
            elif self.p.settings.find("CTRd") != -1:
                # Progressive redistribution
                self.capitalistsIncome += np.sum(
                    1 / (self.capitalistsIncome + eps) * redistributive_policy
                ) * (
                    self.p.capitalists
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType() == "capitalists"
                        )
                    )
                )
                self.greenEnergyOwnersIncome += np.sum(
                    1 / (self.greenEnergyOwnersIncome + eps) * redistributive_policy
                ) * (
                    self.p.green_energy_owners
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType()
                            == "green_energy_owners"
                        )
                    )
                )
                self.brownEnergyOwnersIncome += np.sum(
                    1 / (self.brownEnergyOwnersIncome + eps) * redistributive_policy
                ) * (
                    self.p.brown_energy_owners
                    - len(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType()
                            == "brown_energy_owners"
                        )
                    )
                )
        else:
            self.totalTaxes += self.totalCarbonTaxes

    def _hire(self):
        """Match unemployed workers to firms with vacancies"""
        self.workingConsumers = self.aliveConsumers.select(
            self.aliveConsumers.isWorker() == True
        )
        for worker in self.workingConsumers:
            if worker.isEmployed() != True:
                suitable_firm_found = False

                for firm in np.random.permutation(self.firms):
                    labour_demand = firm.labour_demand
                    if firm.getNumberOfLabours() < labour_demand:
                        worker.receiveHiring(firm.id)
                        firm.workersList.append(worker.id)
                        firm.wages[worker.id] = worker.getWage()
                        suitable_firm_found = True
                        break
                if not suitable_firm_found:
                    break

    def _fiscal_policy(self):
        """Government fiscal support to households and firms"""
        if self.scenario == "1":
            # Household transfers
            [
                self.aliveConsumers.gov_transfer(
                    self.alpha_h
                    * np.mean(
                        self.aliveConsumers.select(
                            self.aliveConsumers.getConsumerType() == "workers"
                        ).getIncome()
                    )
                )
            ]
        if self.scenario == "1":
            # Firm transfers based on revenue threshold
            for firm in self.firms:
                revenue = firm.soldProducts * firm.getPrice()
                transfer_threshold = self.p.transfer_threshold
                if revenue < transfer_threshold * firm.fix_cost:
                    self.firms.gov_transfer(self.alpha_f * firm.fix_cost)

    def _induce_climate_shock(self):
        """Apply climate shock mortality and wealth losses"""
        # Climate shock application.
        # Two modes:
        #  - "AggPop": use aggregate population mortality PM from climate module (same probability across agents)
        #  - "Idiosyncratic": use individual survival outcomes from climate module (heterogeneous)
        if (
            self.climateShockMode == "AggPop"
            and self.climateModule.shockHappens[0] == True
        ):
            print("start shock")
            # Number of deaths implied by climate module's population mortality (PM)
            deadIDs = np.random.permutation(self.aliveConsumers.getIdentity())[
                : np.max([int(self.climateModule.getPM()[0]), 0])
            ]
            # Fractional wealth loss applied uniformly to survivors (proxy for asset damages)
            loss_percentage = np.max([int(self.climateModule.getPM()[0]), 0]) / len(
                self.aliveConsumers
            )
            # Mark selected agents as dead
            [
                self.aliveConsumers.select(
                    self.aliveConsumers.getIdentity() == ID
                ).setDead()
                for ID in deadIDs
            ]
            # Rebuild alive population view and working-age subset
            self.aliveConsumers = self.aliveConsumers.select(
                self.aliveConsumers.isDead() != True
            )
            self.workingAgeConsumers = [
                idx
                for idx in range(len(self.aliveConsumers))
                if self.aliveConsumers[idx].getAgeGroup() == "working"
            ]
            # Apply proportional wealth loss to survivors
            self.aliveConsumers.wealth_loss(loss_percentage)
            aliveIDs = self.aliveConsumers.getIdentity()
            print(
                f"Climate shock happens: {np.max([int(self.climateModule.getPM()[0]), 0])} people died!"
            )
            # Remove deceased workers from firms' rosters
            for firm in self.firms:
                if len(firm.workersList) > 0:
                    for workerID in firm.workersList:
                        if workerID not in aliveIDs:
                            firm.workersList.remove(workerID)
            # Reset shock flag so it does not re-trigger immediately
            self.climateModule.shockHappens = False

        elif (
            self.climateShockMode == "Idiosyncratic"
            and self.climateModule.shockHappens[0] == True
        ):
            # Number of deaths implied by individual survival outcomes: alive_post_shock provided by climate module
            deadIDs = np.random.permutation(self.aliveConsumers.getIdentity())[
                : np.max(
                    [
                        int(
                            len(self.aliveConsumers)
                            - self.climateModule.getAliveConsumersPostShock()[0]
                        ),
                        0,
                    ]
                )
            ]
            [
                self.aliveConsumers.select(
                    self.aliveConsumers.getIdentity() == ID
                ).setDead()
                for ID in deadIDs
            ]
            # Fractional wealth loss computed from realized death share (proxy for distributed damages)
            loss_percentage = np.max(
                [
                    int(
                        len(self.aliveConsumers)
                        - self.climateModule.getAliveConsumersPostShock()[0]
                    ),
                    0,
                ]
            ) / len(self.aliveConsumers)
            # Refresh alive/working-age views
            self.aliveConsumers = self.aliveConsumers.select(
                self.aliveConsumers.isDead() != True
            )
            self.workingAgeConsumers = [
                idx
                for idx in range(len(self.aliveConsumers))
                if self.aliveConsumers[idx].getAgeGroup() == "working"
            ]
            # Apply proportional wealth loss to survivors
            self.aliveConsumers.wealth_loss(loss_percentage)
            aliveIDs = self.aliveConsumers.getIdentity()
            # Update firms' worker lists after mortality
            for firm in self.firms:
                if len(firm.workersList) > 0:
                    for workerID in firm.workersList:
                        if workerID not in aliveIDs:
                            firm.workersList.remove(workerID)
            # Reset shock flag
            self.climateModule.shockHappens = False
