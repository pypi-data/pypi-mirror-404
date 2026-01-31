import copy
from collections import OrderedDict

import ambr as am
import numpy as np
import numpy.random as random
import pandas as pd


class Bank(am.Agent):
    """A bank agent"""

    def setup(self):
        self.loans = 0
        self.numberOfUnemployed = 0
        self.numberOfEmployed = 0
        self.bankDataWriter = []
        self.iL = 0
        self.iD = 0.0001
        self.iCB = self.p.bankICB
        self.profit = 0
        self.actualSuppliedLoan = 0
        self.totalLoanSupply = 0
        self.totalLoanDemands = 0
        self.deposits = 0
        self.equities = 0
        self.DTE = 0
        self.B_cb = self.p.bankResInit
        self.reserves = self.p.bankResInit
        self.equity = 0
        self.NPL = 0
        self.R_cb = self.p.bankResInit
        self.F_cb = 0
        self.F_cb_i = 0
        self.Z_B = 0

    def agentAssign(self):
        # short out agents without loan_demand > 0
        # updateConsumerList = self.model.consumer_agents.select(self.model.consumer_agents.newCreditAsked > 0)
        updateCSFList = self.model.csfirm_agents.select(
            self.model.csfirm_agents.loan_demand > 0
        )
        updateCPList = self.model.cpfirm_agents.select(
            self.model.cpfirm_agents.loan_demand > 0
        )

        # print("DEBUG: updateCSFList.defaultProb shape:", updateCSFList.defaultProb.shape)
        # print("DEBUG: updateCPList.defaultProb shape:", updateCPList.defaultProb.shape)
        # print("DEBUG: greenEFirm.defaultProb shape:", self.model.greenEFirm.defaultProb.shape)
        # print("DEBUG: brownEFirm.defaultProb shape:", self.model.brownEFirm.defaultProb.shape)

        try:
            self.orderedAgentsInterestsRaw = np.argsort(
                np.concatenate(
                    [
                        updateCSFList.defaultProb,
                        updateCPList.defaultProb,
                        self.model.greenEFirm.defaultProb,
                        self.model.brownEFirm.defaultProb,
                    ]
                )
            )
        except ValueError as e:
            print(f"Error concatenating defaultProb: {e}")
            print(
                f"updateCSFList.defaultProb: {updateCSFList.defaultProb}, type: {type(updateCSFList.defaultProb)}, shape: {getattr(updateCSFList.defaultProb, 'shape', 'N/A')}"
            )
            print(
                f"updateCPList.defaultProb: {updateCPList.defaultProb}, type: {type(updateCPList.defaultProb)}, shape: {getattr(updateCPList.defaultProb, 'shape', 'N/A')}"
            )
            print(
                f"greenEFirm.defaultProb: {self.model.greenEFirm.defaultProb}, type: {type(self.model.greenEFirm.defaultProb)}, shape: {getattr(self.model.greenEFirm.defaultProb, 'shape', 'N/A')}"
            )
            print(
                f"brownEFirm.defaultProb: {self.model.brownEFirm.defaultProb}, type: {type(self.model.brownEFirm.defaultProb)}, shape: {getattr(self.model.brownEFirm.defaultProb, 'shape', 'N/A')}"
            )
            raise e
        self.orderedAgentsInterests = np.concatenate(
            [
                updateCSFList.id,
                updateCPList.id,
                self.model.greenEFirm.id,
                self.model.brownEFirm.id,
            ]
        )[self.orderedAgentsInterestsRaw]

    def _calculate_consumer_networth(self, agent):
        """
        This internal function of the Bank class is used to represent the demands
        between consumer agents and the bank

        ---
        Args:
            agent: The target consumer agent
        ---
        Returns:
        """

        if agent.getCovidStateAttr("state") != "dead":
            self.deposits += np.sum(agent.wealthList[-1])
            # self.loans += agent.obtainedCreditList[-1]
            self.profit += -np.sum(self.p.bankID * agent.get_deposit())

    def _calculate_firm_networth(self, agent):
        """
        This internal function of the Bank class is used to represent the demands
        between firm agents and the bank

        ---
        Args:
            agent: The target firm agent
        ---
        Returns:
        """

        self.totalLoanDemands += np.sum(agent.loan_demand)
        self.profit += agent.iL * np.sum(agent.loanList)
        self.deposits += np.sum(agent.depositList[-1])
        self.loans += np.sum(agent.loanList)
        self.totalBankruptFraction += np.sum(agent.defaultProb * np.sum(agent.loanList))

    def _calculate_running_loan(self, agent_id):
        """
        This internal function of the Bank class is used to represent the demands
        between agents and the bank

        ---
        Args:
            agent_id: The target agent id
        ---
        Returns:
        """
        # print("bank start")
        agent = self.agentList.select(self.agentList.getIdentity() == agent_id)[0]
        bankruptFraction = agent.defaultProb * np.sum(agent.loanList[0])

        L_CAR = 0
        if (
            bankruptFraction <= self.totalLoanSupply
            and self.runningLoan <= self.totalLoanSupply
        ):
            L_CAR = np.sum([agent.loan_demand])

        if self.Z_B < 0:
            agent.adjustAccordingToBankState(0)
            # print("option 1")
        elif 0 <= self.Z_B <= L_CAR:
            # print("option 2")
            agent.adjustAccordingToBankState(self.Z_B)
            self.runningLoan += self.Z_B
        else:
            # print("option 3")
            self.runningLoan += L_CAR
            agent.adjustAccordingToBankState(L_CAR)

    def sommaW(self, eps=1e-8):
        """
        This internal function of the Bank class is used to propagate the main functions of the bank
        """
        # Reserves calculation
        ## When the reserve is negative/lower than the RRR:
        if self.R_cb < self.p.gammaRRR * self.deposits:
            self.R_cb = self.p.gammaRRR * self.deposits  # set reserve to 0
            self.F_cb += (
                self.R_cb - self.deposits - self.loans + self.equities
            )  # request funding from CB
            self.F_cb_i = self.R_cb * (1 + self.p.bankICB_P)  # payoff the interest

        ## When the reserve is positive/bigger than the RRR:
        if self.R_cb > self.deposits - self.loans + self.equities:
            self.F_cb = 0  # set funding to 0
            self.F_cb_i = self.R_cb * (1 + self.p.bankICB_P)  # earn interest on reserve

        self.Z_B = self.R_cb - self.p.gammaRRR * self.deposits

        # Demands and Transactions
        # [self._calculate_wealth(agent) for agent in self.model.consumer_agents]
        # Consolidate consumer demands efficiently (Vectorized)
        live_consumers = [
            c for c in self.model.aliveConsumers if c.covidState["state"] != "dead"
        ]

        if live_consumers:
            # Sum wealth (wealthList[-1]) and deposits
            # Using generator expression for memory efficiency
            total_wealth = sum(c.wealthList[-1] for c in live_consumers)
            total_deposits = sum(c.deposit for c in live_consumers)

            self.deposits += total_wealth
            self.profit += -np.sum(self.p.bankID * total_deposits)
        [self._calculate_firm_networth(agent) for agent in self.model.cpfirm_agents]
        self._calculate_firm_networth(self.model.greenEFirm[0])
        self._calculate_firm_networth(self.model.brownEFirm[0])

        # Calculate Bank statistics
        self.profit += self.p.bankICB_P * (self.R_cb - self.F_cb)
        self.equities = self.loans - self.deposits + self.reserves
        self.equity = self.profit + self.equities
        self.totalLoanSupply = copy.copy(self.Z_B)
        self.DTE = self.deposits / (self.equities + eps)
        self.iL = self.DTE / 100
        self.agentAssign()
        self.runningLoan = 0
        list(map(self._calculate_running_loan, self.orderedAgentsInterests))
        self.actualSuppliedLoan += np.sum(self.runningLoan)

    def reset_bank(self):

        # Reset temporary variables
        self.agentList = (
            self.model.csfirm_agents
            + self.model.cpfirm_agents
            + self.model.greenEFirm
            + self.model.brownEFirm
        )
        consumers = self.model.aliveConsumers
        # Optimization: Pre-fetch arrays to avoid method call overhead
        is_employed = np.array([c.employed for c in consumers])
        # Direct dict access for covid state
        cov_states = np.array([c.covidState["state"] for c in consumers])
        # Attribute access for type (AMBER handles this or we list comp)
        cons_types = np.array([c.consumerType for c in consumers])

        is_worker = cons_types == "workers"
        not_dead = cov_states != "dead"

        # Unemployed: Worker AND Not Employed AND Not Dead
        # Employed: Worker AND Employed AND Not Dead
        self.numberOfUnemployed = np.sum((~is_employed) & is_worker & not_dead)
        self.numberOfEmployed = np.sum(is_employed & is_worker & not_dead)
        self.profit = 0
        self.totalLoanDemands = 0
        self.equities = 0
        self.actualSuppliedLoan = 0
        self.totalBankruptFraction = 0
        self.deposits = 0
        self.loans = 0
        self.NPL = 0
