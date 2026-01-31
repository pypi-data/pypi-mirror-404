# Government
import ambr as am
import numpy as np
import pandas as pd


class Government(am.Agent):
    """A government agent"""

    def setup(self):
        self.taxRate = self.p.taxRate
        self.expenditure = 0
        self.totalTaxes = 0
        self.fiscal = 0
        self.tax = 0
        self.budget = 0
        self.transfer = 0
        self.bond = 0
        self.bond_list = [0]
        self.iB = self.p.iB

    def checkConsistency(self):
        return self.expenditure == self.totalTaxes

    def agentAssign(self):
        # short out agents without loanDemand > 0
        # updateConsumerList = self.model.consumer_agents.select(self.model.consumer_agents.newCreditAsked > 0)
        updateCSFList = self.model.csfirm_agents.select(
            self.model.csfirm_agents.bankrupt == True
        )
        updateCPList = self.model.cpfirm_agents.select(
            self.model.cpfirm_agents.bankrupt == True
        )

        # self.orderedAgentsInterestsRaw = np.argsort(np.concatenate([updateCSFList.defaultProb, updateCPList.defaultProb, self.model.greenEFirm.defaultProb, self.model.brownEFirm.defaultProb]))
        # self.orderedAgentsInterests = np.concatenate([updateCSFList.id, updateCPList.id, self.model.greenEFirm.id, self.model.brownEFirm.id])[self.orderedAgentsInterestsRaw]

    # def _calculate_wealth(self, agent):
    #     if agent.getEmploymentState():
    #         self.numberOfEmployed += 1
    #         if self.numberOfUnemployed > 0:
    #             self.numberOfUnemployed -= 1
    #     else:
    #         self.numberOfUnemployed += 1
    #         if self.numberOfEmployed > 0:
    #             self.numberOfEmployed -= 1

    #         wealth = agent.getWealth()

    def _calculate_firm_bailout(self, agent):
        """
        This internal function of the Bank class is used to represent the demands
        between firm agents and the bank

        ---
        Args:
            agent: The target firm agent
        ---
        Returns:
        """
        if agent.getNetWorth() < 0:
            self.expenditure -= np.sum(agent.getNetWorth())

    ### Direct Transfers to Households:
    def transfer_expenditure(self, value):
        self.transfer += value

    ### put the government calculation here (unemployment dole, tax)
    def E_Gov(self):
        unemployed_count = np.sum(self.model.aliveConsumers.getUnemploymentState() == 1)
        self.expenditure = (
            self.p.unemploymentDole * float(unemployed_count) + self.fiscal
        )
        return self.expenditure

    def UE_Gov(self):
        unemployed_count = np.sum(self.model.aliveConsumers.getUnemploymentState() == 1)
        self.ue_gov = self.p.unemploymentDole * float(unemployed_count)
        return self.ue_gov

    def update_budget(self, value):
        self.budget += value

    # budget balance condition:
    ### Government issue bond to cover any deficit:
    def issue_bond(self):
        if self.tax >= self.expenditure + (1 + self.iB) * np.sum(self.bond_list):
            self.bond = 0
        else:
            self.bond = (
                self.expenditure + (1 + self.iB) * np.sum(self.bond_list) - self.tax
            )
