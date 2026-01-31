"""
CliMaPan-Lab Example: Scenario Analysis
Data Loading and Processing for Different Economic Scenarios

This module provides utilities for loading and processing simulation results
from different economic scenarios for comparative analysis.
"""

import numpy as np
import pandas as pd


class load_data:

    def __init__(self, result, results_base_path="results"):
        """
        Load simulation data from results directory.

        Args:
            result: Name of the result directory
            results_base_path: Base path for results (default: "results")
        """
        self.data_folder = f"{results_base_path}/{result}"
        self.data_table = pd.read_csv(
            f"{self.data_folder}/single_run.csv.gz", compression="gzip"
        )
        self.consumption = np.load(
            f"{self.data_folder}/Consumption.npy", allow_pickle=True
        )
        self.employment = np.load(f"{self.data_folder}/Employed.npy", allow_pickle=True)
        self.unemployment = np.load(f"{self.data_folder}/UnemploymentRate.npy")
        self.bi = np.load(f"{self.data_folder}/BrownInvestments.npy", allow_pickle=True)
        self.gi = np.load(f"{self.data_folder}/GreenInvestments.npy", allow_pickle=True)
        self.gdp = np.load(f"{self.data_folder}/GDP.npy", allow_pickle=True)
        self.loans = np.load(f"{self.data_folder}/Loans.npy", allow_pickle=True)
        self.banklqr = np.load(f"{self.data_folder}/BankLDR.npy", allow_pickle=True)
        self.bankdeposit = np.load(
            f"{self.data_folder}/BankDeposits.npy", allow_pickle=True
        )
        self.csdeposit = np.load(f"{self.data_folder}/CSDeposit.npy", allow_pickle=True)
        self.cpdeposit = np.load(f"{self.data_folder}/CPDeposit.npy", allow_pickle=True)
        self.csdefaultP = np.load(
            f"{self.data_folder}/CSCreditDefaultRisk.npy", allow_pickle=True
        )
        self.cpdefaultP = np.load(
            f"{self.data_folder}/CPCreditDefaultRisk.npy", allow_pickle=True
        )
        self.csprofit = np.load(
            f"{self.data_folder}/CSNetProfits.npy", allow_pickle=True
        )
        self.cpprofit = np.load(
            f"{self.data_folder}/CPNetProfits.npy", allow_pickle=True
        )
        self.fiscal = np.load(f"{self.data_folder}/FiscalPolicy.npy", allow_pickle=True)
        self.csnetworth = np.load(
            f"{self.data_folder}/CSNetWorth.npy", allow_pickle=True
        )
        self.dte = np.load(
            f"{self.data_folder}/BankLoanOverEquity.npy", allow_pickle=True
        )
        self.non_loan = np.load(
            f"{self.data_folder}/NonPerformingLoan.npy", allow_pickle=True
        )
        self.bankdte = np.load(f"{self.data_folder}/BankDTE.npy", allow_pickle=True)
        self.csloanpayment = np.load(
            f"{self.data_folder}/CSLoanPayment.npy", allow_pickle=True
        )
        self.cploanpayment = np.load(
            f"{self.data_folder}/CPLoanPayment.npy", allow_pickle=True
        )
        self.cswage = np.load(f"{self.data_folder}/CSWageBill.npy", allow_pickle=True)
        self.cpwage = np.load(f"{self.data_folder}/CPWageBill.npy", allow_pickle=True)
        self.cscost = np.load(
            f"{self.data_folder}/CSProductionCost.npy", allow_pickle=True
        )
        self.cpcost = np.load(
            f"{self.data_folder}/CPProductionCost.npy", allow_pickle=True
        )
        self.csinvestment = np.load(
            f"{self.data_folder}/CSCapitalInvestment.npy", allow_pickle=True
        )
        self.csprice = np.load(f"{self.data_folder}/CSPrice.npy", allow_pickle=True)
        self.cpprice = np.load(f"{self.data_folder}/CPPrice.npy", allow_pickle=True)
        self.csucost = np.load(f"{self.data_folder}/CSUCost.npy", allow_pickle=True)
        self.cpucost = np.load(f"{self.data_folder}/CPUCost.npy", allow_pickle=True)
        self.cpsale = np.load(f"{self.data_folder}/CPSale.npy", allow_pickle=True)
        self.cssale = np.load(f"{self.data_folder}/CSSale.npy", allow_pickle=True)
        self.cssoldproduct = np.load(
            f"{self.data_folder}/CSSoldProducts.npy", allow_pickle=True
        )
        self.cpsoldproduct = np.load(
            f"{self.data_folder}/CPSoldProducts.npy", allow_pickle=True
        )
        self.csbankrupt = np.load(
            f"{self.data_folder}/CSNumBankrupt.npy", allow_pickle=True
        )
        self.cpbankrupt = np.load(
            f"{self.data_folder}/CPNumBankrupt.npy", allow_pickle=True
        )
        self.expenditure = np.load(
            f"{self.data_folder}/Expenditures.npy", allow_pickle=True
        )
        self.uexpenditure = np.load(
            f"{self.data_folder}/UnemploymentExpenditure.npy", allow_pickle=True
        )
        self.cscapacity = np.load(
            f"{self.data_folder}/CScapacity.npy", allow_pickle=True
        )
        self.cpcapacity = np.load(
            f"{self.data_folder}/CPcapacity.npy", allow_pickle=True
        )
        self.csk = np.load(f"{self.data_folder}/CSCapital.npy", allow_pickle=True)
        self.wage = np.load(f"{self.data_folder}/Wage.npy", allow_pickle=True)
        self.tax = np.load(f"{self.data_folder}/TotalTaxes.npy", allow_pickle=True)
        self.deposit = np.load(
            f"{self.data_folder}/BankDeposits.npy", allow_pickle=True
        )
        self.loan_demand = np.load(
            f"{self.data_folder}/TotalLoanDemand.npy", allow_pickle=True
        )
        self.BankEquity = np.load(
            f"{self.data_folder}/BankEquity.npy", allow_pickle=True
        )
        self.inflation = np.load(
            f"{self.data_folder}/InflationRate.npy", allow_pickle=True
        )
        self.geprofit = np.load(
            f"{self.data_folder}/GENetProfits.npy", allow_pickle=True
        )
        self.beprofit = np.load(
            f"{self.data_folder}/BENetProfits.npy", allow_pickle=True
        )
        self.profitmargin = np.load(
            f"{self.data_folder}/CSMargin.npy", allow_pickle=True
        )

        try:
            self.infectdaily = np.load(
                f"{self.data_folder}/Infection.npy", allow_pickle=True
            )
        except FileNotFoundError:
            self.infectdaily = np.zeros(120)
        try:
            self.susceptible = np.load(
                f"{self.data_folder}/Susceptible.npy", allow_pickle=True
            )
        except FileNotFoundError:
            self.susceptible = np.zeros(120)
        try:
            self.recover = np.load(f"{self.data_folder}/Rcover.npy", allow_pickle=True)
        except FileNotFoundError:
            self.recover = np.zeros(120)
        try:
            self.mild = np.load(f"{self.data_folder}/mild.npy", allow_pickle=True)
        except FileNotFoundError:
            self.mild = np.zeros(120)
        try:
            self.critical = np.load(
                f"{self.data_folder}/critical.npy", allow_pickle=True
            )
        except FileNotFoundError:
            self.critical = np.zeros(120)
        try:
            self.severe = np.load(f"{self.data_folder}/severe.npy", allow_pickle=True)
        except FileNotFoundError:
            self.severe = np.zeros(120)
        try:
            self.exposed = np.load(f"{self.data_folder}/Exposed.npy", allow_pickle=True)
        except FileNotFoundError:
            self.exposed = np.zeros(120)
        try:
            self.dead = np.load(f"{self.data_folder}/Dead.npy", allow_pickle=True)
        except FileNotFoundError:
            self.dead = np.zeros(120)
        try:
            self.emit = np.load(
                f"{self.data_folder}/ClimateC02Concentration.npy", allow_pickle=True
            )
        except FileNotFoundError:
            self.emit = np.zeros(120)
        try:
            self.temp = np.load(
                f"{self.data_folder}/ClimateTemperature.npy", allow_pickle=True
            )
        except FileNotFoundError:
            self.temp = np.zeros(120)

    def tolist(self):
        for key, value in self.__dict__.items():
            if isinstance(value, np.ndarray):
                self.__dict__[key] = value.tolist()

    def prep(self, cov=False, climate=False):
        self.gdp = [x for x in self.gdp if x is not None]
        self.inflation = [x for x in self.inflation if x is not None]
        self.tax = [x for x in self.tax if x is not None]
        self.BankEquity = [x for x in self.BankEquity if x is not None]
        self.bankdte = [x for x in self.bankdte if x is not None]
        self.bankdeposit = [x for x in self.bankdeposit if x is not None]
        self.deposit = [x for x in self.deposit if x is not None]
        self.banklqr = [x for x in self.banklqr if x is not None]
        self.employment = [x for x in self.employment if x is not None]
        self.unemployment = [x for x in self.unemployment if str(x) != "nan"]
        self.uexpenditure = [x for x in self.uexpenditure if x is not None]
        self.consumption = [x for x in self.consumption if x is not None]
        self.expenditure = [x for x in self.expenditure if x is not None]
        self.loans = [x for x in self.loans if x is not None]
        self.cpdeposit = [x for x in self.cpdeposit if x is not None]
        self.csdeposit = [x for x in self.csdeposit if x is not None]
        self.csdefaultP = [x for x in self.csdefaultP if x is not None]
        self.cpdefaultP = [x for x in self.cpdefaultP if x is not None]
        self.csprofit = [x for x in self.csprofit if x is not None]
        self.cpprofit = [x for x in self.cpprofit if x is not None]
        self.fiscal = [x for x in self.fiscal if x is not None]
        self.bi = [x for x in self.bi if x is not None]
        self.gi = [x for x in self.gi if x is not None]
        self.dte = [x for x in self.dte if x is not None]
        self.non_loan = [x for x in self.non_loan if x is not None]
        self.emit = [x for x in self.emit if x is not None]
        self.temp = [x for x in self.temp if x is not None]
        self.loan_demand = [x for x in self.loan_demand if x is not None]
        self.csloanpayment = [x for x in self.csloanpayment if x is not None]
        self.cploanpayment = [x for x in self.cploanpayment if x is not None]
        self.cswage = [x for x in self.cswage if x is not None]
        self.cpwage = [x for x in self.cpwage if x is not None]
        self.cscost = [x for x in self.cscost if x is not None]
        self.cpcost = [x for x in self.cpcost if x is not None]
        self.csinvestment = [x for x in self.csinvestment if x is not None]
        self.csprice = [x for x in self.csprice if x is not None]
        self.cpprice = [x for x in self.cpprice if x is not None]
        self.csucost = [x for x in self.csucost if x is not None]
        self.cpucost = [x for x in self.cpucost if x is not None]
        self.cssale = [x for x in self.cssale if x is not None]
        self.cssoldproduct = [x for x in self.cssoldproduct if x is not None]
        self.cpsoldproduct = [x for x in self.cpsoldproduct if x is not None]
        self.cscapacity = [x for x in self.cscapacity if x is not None]
        self.cpcapacity = [x for x in self.cpcapacity if x is not None]
        self.csbankrupt = [x for x in self.csbankrupt if x is not None]
        self.cpbankrupt = [x for x in self.cpbankrupt if x is not None]
        self.csk = [x for x in self.csk if x is not None]
        self.wage = [x for x in self.wage if x is not None]
        self.beprofit = [x for x in self.beprofit if x is not None]
        self.geprofit = [x for x in self.geprofit if x is not None]
        self.profitmargin = [x for x in self.profitmargin if x is not None]
        if cov:
            self.infectdaily = [x for x in self.infectdaily if x is not None]
            self.susceptible = [x for x in self.susceptible if x is not None]
            self.recover = [x for x in self.recover if x is not None]
            self.mild = [x for x in self.mild if x is not None]
            self.critical = [x for x in self.critical if x is not None]
            self.severe = [x for x in self.severe if x is not None]
            self.exposed = [x for x in self.exposed if x is not None]
            self.dead = [x for x in self.dead if x is not None]

        # self.consumption = np.sum(self.consumption, axis=1)
        # self.consumption = np.sum(self.consumption)
        self.csdeposit = np.sum(self.csdeposit, axis=1)
        self.cpdeposit = np.sum(self.cpdeposit, axis=1)
        self.csloanpayment = np.sum(self.csloanpayment, axis=1)
        self.cploanpayment = np.sum(self.cploanpayment, axis=1)
        self.cswage = np.sum(self.cswage, axis=1)
        self.cpwage = np.sum(self.cpwage, axis=1)
        self.cscost = np.sum(self.cscost, axis=1)
        self.cpcost = np.sum(self.cpcost, axis=1)
        self.csprofit = np.sum(self.csprofit, axis=1)
        self.cpprofit = np.sum(self.cpprofit, axis=1)
        self.csinvestment = np.sum(self.csinvestment, axis=1)
        self.csprice = np.mean(self.csprice, axis=1)
        self.cpprice = np.mean(self.cpprice, axis=1)
        self.csucost = np.mean(self.csucost, axis=1)
        self.cpucost = np.mean(self.cpucost, axis=1)
        self.csdefaultP = np.mean(self.csdefaultP, axis=1)
        self.cpdefaultP = np.mean(self.cpdefaultP, axis=1)
        self.cscapacity = np.sum(self.cscapacity, axis=1)
        self.cpcapacity = np.sum(self.cpcapacity, axis=1)
        self.csk = np.sum(self.csk, axis=1)
        self.cpsoldproduct = np.sum(self.cpsoldproduct, axis=1)
        self.cssoldproduct = np.sum(self.cssoldproduct, axis=1)
        """if climate:
            self.temp = [value for sublist in self.temp for value in sublist]"""
        self.geprofit = np.sum(self.geprofit, axis=1)
        self.beprofit = np.sum(self.beprofit, axis=1)
        for i in range(len(self.dte)):
            if climate:
                self.temp[i] = self.temp[i][0]
                self.emit[i] = self.emit[i][0]
            self.loan_demand[i] = self.loan_demand[i][0]
            self.dte[i] = self.dte[i][0]
            self.loans[i] = self.loans[i][0]
            self.BankEquity[i] = self.BankEquity[i][0]
            self.bankdte[i] = self.bankdte[i][0]
            self.non_loan[i] = self.non_loan[i][0]
            self.consumption[i] = np.sum(self.consumption[i])
            self.banklqr[i] = self.banklqr[i][0]

        """
        Calculate the credit growth (percentage change) based on self.loans.
        If the previous loan value is 0, the growth rate will be 0 for that period.
        """
        if len(self.loans) < 2:
            print("Not enough data to calculate growth.")
            return

        self.credit_growth = []
        for i in range(1, len(self.loans)):
            if self.loans[i - 1] == 0:
                # Handle division by zero by setting growth rate to 0
                growth_rate = 0
            else:
                growth_rate = (
                    (self.loans[i] - self.loans[i - 1]) / self.loans[i - 1]
                ) * 100

            self.credit_growth.append(growth_rate)

        # Optionally, insert a placeholder (e.g., 0) for the first period where growth is undefined
        self.credit_growth.insert(
            0, 0
        )  # Inserting 0 for the first period since it's the start of the series

    def smooth(self):
        pass
