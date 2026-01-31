import copy
import math

import ambr as am
import numpy as np
import numpy.random as random

from ..utils import lognormal

# ============================================================================
#                           Consumer Agent
# ============================================================================
# Role:
#   A single household/individual that:
#     - earns income (wages if worker, dividends if owner, interest on deposits),
#     - chooses desired consumption based on wealth and subsistence needs,
#     - updates deposits/wealth after transactions,
#     - holds employment status and firm attachment,
#     - carries an epidemiological state (COVID SEIR-like progression by age),
#     - can receive transfers, be hired/fired, and suffer climate-shock wealth loss.
#
# Key state:
#   deposit:     liquid wealth (savings); drives affordability and interest income
#   wage:        current wage if employed (or unemployment benefit)
#   income:      total income this step (interest + wage + possible owner dividend)
#   div:         dividend flow for owners (set by model after firm accounting)
#   desired_consumption: physical goods demand before market allocation
#   consumption: realized consumption expenditure (value; set during transactions)
#   employed:    employment flag for workers
#   belongToFirm: firm id if employed
#   consumerType: 'workers' | 'capitalists' | 'green_energy_owners' | 'brown_energy_owners'
#   covidState:   dict(state, t, duration, nextState) for disease progression
#   ageGroup:     'young' | 'working' | 'elderly' (affects disease transition probs)
#
# Update cycle (typical month):
#   desired_C()               → compute desired consumption
#   (model sales algorithm)   → sets self.consumption based on budgets/prices
#   update_wealth()           → realize income and subtract consumption value
#   progressCovid()           → progress epidemiological state daily
#
# Notes:
#   - This class is intentionally "thin" on market logic; it exposes getters/setters
#     that the model-level matching/transactions use.
#   - Keep all behavior deterministic given random draws and parameters in `self.p`.
# ============================================================================


class Consumer(am.Agent):
    """A consumer agent"""

    def setup(self):
        # ----------------------------------------
        # Parameter snapshot & defaults
        # ----------------------------------------
        self.consumptionSubsistenceLevel = (
            self.p.subsistenceLevelOfConsumption
        )  # minimum physical good demand
        self.worker_additional_consumption = (
            self.p.worker_additional_consumption
        )  # additional consumption if employed
        self.owner_additional_consumption = (
            self.p.owner_additional_consumption
        )  # additional consumption if owner
        self.iD = self.p.bankID  # deposit interest rate (per step)
        self.consumption_growth = (
            self.p.consumption_growth
        )  # drift in desired consumption
        self.employed = False
        self.reset()  # reset endogenous storages

        # Epidemiology container (SEIR-like with extra states)
        self.covidState = {
            "state": None,
            "t": None,
            "duration": None,
            "nextState": None,
        }

        # Initial wealth and type flags
        self.deposit = 1500  # starting liquid wealth
        self.growth_factor = 1  # multiplicative consumption trend
        self.consumerType = None  # set later by model: workers/owners/etc.

        # what else do I need

    # ----------------------------------------
    # (Re)initialize endogenous state (used at birth/reset)
    # ----------------------------------------
    def reset(self):
        self.owner = False
        self.memoryLengthForUnemplymentRate = 5
        self.memoryLengthForEmplymentState = 10
        self.wage = self.p.minimumWage  # baseline wage (or dole if unemployed)
        self.income = 0  # total income flow realized this step
        self.div = 0  # owner dividend (if owner)
        self.wealthList = [0]  # time series of deposits
        self.desired_consumption = self.consumptionSubsistenceLevel  # physical units
        self.consumption = 0  # realized spending (value)
        self.employmentStateStorage = [1]  # short memory of employment status
        self.unemploymentRateStorage = [0]  # memory of perceived unemployment (local)
        self.employed = False
        self.belongToFirm = None
        self.dead = False
        self.sickLeaves = []  # dates while sick (for accounting)
        self.price = 0  # last faced consumer good price

    # ----------------------------------------
    # Desired consumption rule (physical units)
    # ----------------------------------------
    def desired_C(self):
        """Calculate desired consumption based on wealth and subsistence needs"""
        sick_reduction = self.p.sick_reduction  # reduction in consumption if sick
        sick = self.model.covidState  # model-level COVID flag

        # Base demand: subsistence + add-on (higher if employed/owner),
        # bounded by 80% of current deposits in real terms
        base_consumption = self.consumptionSubsistenceLevel + np.min(
            [
                self.employed * self.worker_additional_consumption
                + self.owner * self.owner_additional_consumption,
                0.8 * self.deposit / self.price,
            ]
        )

        # Drift up over time; subtract a penalty if the economy is in COVID state
        self.growth_factor *= 1 + self.consumption_growth
        self.desired_consumption = (
            self.growth_factor * base_consumption - sick_reduction * sick
        )
        # if sick == True:
        # print("sick reduction", sick, sick_reduction)

    # ----------------------------------------
    # Wealth/income accounting (called after transactions)
    # ----------------------------------------
    def update_wealth(self):
        """Update wealth after income and consumption"""
        # Income = deposit interest + wage (if worker) + owner's minimum wage proxy + dividends
        self.income = (
            self.deposit * self.iD
            + self.isWorker() * self.getWage()
            + self.owner * (self.p.minimumWage + self.getDiv())
        )
        # if self.owner: print("owner income", self.income)

        # Update deposits after paying for consumption (note: consumption is value, not units)
        self.deposit += (
            self.income - self.consumption
        )  # consumption is value variable, updated in transaction
        self.wealthList.append(self.deposit)

    # ----------------------------------------
    # Employment status (set by firms / model)
    # ----------------------------------------
    def receiveHiring(self, firmID):
        """Process hiring by a firm"""
        if self.getConsumerType() == "workers":
            self.setEmployment(True)
            self.setWage(self.p.minimumWage)  # may be overridden by firm logic
            self.belongToFirm = firmID
            self.updateMemoryAfterHiringFiring()

    def receiveFiring(self):
        """Process firing by a firm"""
        if self.getConsumerType() == "workers":
            self.setEmployment(False)
            self.setWage()  # fall back to unemployment dole
            self.belongToFirm = None
            self.updateMemoryAfterHiringFiring()

    def updateMemoryAfterHiringFiring(self):
        """Update employment memory after hiring/firing"""
        # Append 1/0 for employed/unemployed to short memory
        if self.employed:
            self.employmentStateStorage.append(1.0)
        else:
            self.employmentStateStorage.append(0.0)

        # Keep memory bounded
        if len(self.employmentStateStorage) > self.memoryLengthForEmplymentState:
            self.employmentStateStorage.pop(0)

    def updateMemory(self, unemplRate):
        """Track recent unemployment rates (used in wage formation early on)"""
        self.unemploymentRateStorage.append(unemplRate)
        if len(self.unemploymentRateStorage) > self.memoryLengthForUnemplymentRate:
            self.unemploymentRateStorage.pop(0)

    # ----------------------------------------
    # Consumption (value) setters/getters
    # ----------------------------------------
    def setConsumption(self, value):
        """Set realized consumption value"""
        self.consumption = value

    def getConsumption(self):
        """Get realized consumption value"""
        return self.consumption

    def get_desired_consumption(self):
        """Get desired consumption in physical units"""
        return self.desired_consumption

    # ----------------------------------------
    # Wealth setters/getters
    # ----------------------------------------
    def update_deposit(self, amount):
        """Adjust deposit by amount"""
        self.deposit += amount

    def set_deposit(self, deposit):
        """Set deposit to specific value"""
        self.deposit = deposit

    def wealth_loss(self, loss_percentage):
        """Apply wealth loss (used during climate shocks)"""
        self.deposit *= 1 - loss_percentage

    def get_deposit(self):
        """Get current deposit level"""
        return self.deposit

    # ----------------------------------------
    # Employment and identity helpers
    # ----------------------------------------
    def getEmploymentState(self):
        """Check if employed worker"""
        return self.employed and self.consumerType == "workers"

    def getUnemploymentState(self):
        """Check if unemployed worker"""
        return not self.employed and self.consumerType == "workers"

    def setEmployment(self, value):
        """Set employment status"""
        self.employed = value

    def isWorker(self):
        """Check if consumer is a worker"""
        return self.consumerType == "workers"

    def getSumEmploymentState(self):
        return self.sumEmploymentState

    def getIdentity(self):
        """Get agent ID"""
        return self.id

    def getFinancialDifficultyIndicator(self):
        return self.financialDifficultyIndicator

    # ----------------------------------------
    # Wage rule (with early-period heuristic)
    # ----------------------------------------
    def setWage(self, wage=None):
        """Set wage with unemployment dole fallback"""
        if self.employed:
            if self.model.t < 32:
                # Early period: wage responds to recent unemployment memory
                self.wage = self.p.minimumWage * (1 + self.unemploymentRateStorage[-1])
            else:
                # Later: bound by unemployment dole
                if wage > self.p.unemploymentDole:
                    self.wage = wage
                else:
                    self.wage = self.p.unemploymentDole
        else:
            # Unemployed: dole
            self.wage = self.p.unemploymentDole

    def getIncome(self):
        """Get total income this period"""
        return self.income

    def getWage(self):
        """Get current wage"""
        return self.wage

    # ----------------------------------------
    # Type/ownership helpers
    # ----------------------------------------
    def setConsumerType(self, consumerType):
        """Set consumer type (workers/capitalists/energy owners)"""
        self.consumerType = consumerType

    def getConsumerType(self):
        """Get consumer type"""
        return self.consumerType

    def getBelongToFirm(self):
        """Get firm ID if employed"""
        return self.belongToFirm

    def setDiv(self, div):
        """Set dividend (only for owners)"""
        if self.owner:
            self.div = div

    def getDiv(self):
        """Get dividend income"""
        return self.div

    # ----------------------------------------
    # Government transfer
    # ----------------------------------------
    def gov_transfer(self, value):
        """Receive government transfer"""
        self.deposit += value

    # ----------------------------------------
    # Demographics
    # ----------------------------------------
    def setAgeGroup(self, ageGroup):
        """Set age group (young/working/elderly)"""
        self.ageGroup = ageGroup

    def getAgeGroup(self):
        """Get age group"""
        return self.ageGroup

    # ============================================================================
    # Epidemiology state: helpers + transitions (daily progression)
    # ============================================================================

    def setCovidState(self, state=None, time=None, duration=None, nextState=None):
        """Set COVID state with transition parameters"""
        # Full update if state + time provided
        if state is not None and time is not None:
            self.covidState["state"] = state
            self.covidState["t"] = time
            self.covidState["duration"] = duration
            self.covidState["nextState"] = nextState
        # Quick re-init to susceptible
        elif state == "susceptible":
            self.covidState = {
                "state": "susceptible",
                "t": None,
                "duration": None,
                "nextState": None,
            }
        # Reset to None
        else:
            self.covidState = {
                "state": None,
                "t": None,
                "duration": None,
                "nextState": None,
            }

    def getCovidState(self):
        """Get full COVID state dict"""
        return self.covidState

    def getCovidStateAttr(self, attr):
        """Get specific COVID state attribute"""
        try:
            return self.covidState[attr]
        except KeyError:
            raise SyntaxError(
                f"No such attribute '{attr}'. Please select from: {list(self.covidState.keys())}"
            )

    # ----------------------------------------
    # Infection via contacts (firm + community)
    # ----------------------------------------
    def propagateContact(self, inf_f, inf_c, p_firm, p_community):
        """Calculate infection probability from contacts"""
        if inf_f > 0 or inf_c > 0:
            # Probability of at least one successful transmission across contacts
            p_infection = 1 - ((1 - p_firm) ** inf_f) * ((1 - p_community) ** inf_c)
            if np.random.rand() <= p_infection:
                self.setCovidState(
                    "exposed",
                    self.model.t,
                    lognormal(
                        self.p.T_susceptible_mild_mean, self.p.T_susceptible_mild_std
                    ),
                    "mild",
                )

    # ----------------------------------------
    # State-specific progressors (called by progressCovid)
    # ----------------------------------------
    def _progressCovidExposedState(self):
        """Progress from exposed state"""
        self.setSickLeaves(str(self.model.today))
        if self.covidState["duration"] is None:
            # Choose branch to 'mild' or 'infected non-symptomatic' by age
            if self.getAgeGroup() == "young":
                if np.random.rand() < self.p.p_exposed_mild_young:
                    self.setCovidState(
                        "exposed",
                        self.covidState["t"],
                        lognormal(
                            self.p.T_exposed_mild_mean, self.p.T_exposed_mild_std
                        ),
                        "mild",
                    )
                else:
                    self.setCovidState(
                        "infected non-sympotomatic",
                        self.covidState["t"],
                        lognormal(
                            self.p.T_nonsym_recovered_mean,
                            self.p.T_nonsym_recovered_std,
                        ),
                        "recovered",
                    )
            elif self.getAgeGroup() == "working":
                if np.random.rand() < self.p.p_exposed_mild_working:
                    self.setCovidState(
                        "exposed",
                        self.covidState["t"],
                        lognormal(
                            self.p.T_exposed_mild_mean, self.p.T_exposed_mild_std
                        ),
                        "mild",
                    )
                else:
                    self.setCovidState(
                        "infected non-sympotomatic",
                        self.covidState["t"],
                        lognormal(
                            self.p.T_nonsym_recovered_mean,
                            self.p.T_nonsym_recovered_std,
                        ),
                        "recovered",
                    )
            elif self.getAgeGroup() == "elderly":
                if np.random.rand() < self.p.p_exposed_mild_elderly:
                    self.setCovidState(
                        "exposed",
                        self.covidState["t"],
                        lognormal(
                            self.p.T_exposed_mild_mean, self.p.T_exposed_mild_std
                        ),
                        "mild",
                    )
                else:
                    self.setCovidState(
                        "infected non-sympotomatic",
                        self.covidState["t"],
                        lognormal(
                            self.p.T_nonsym_recovered_mean,
                            self.p.T_nonsym_recovered_std,
                        ),
                        "recovered",
                    )
        else:
            # If duration was set earlier, transition when time is up
            if self.model.t >= self.covidState["t"] + self.getCovidStateAttr(
                "duration"
            ):
                self.setCovidState(self.covidState["nextState"], self.model.t)

    def _progressCovidInfectedNonsympotomaticState(self):
        """Progress from infected non-symptomatic state"""
        self.setSickLeaves(str(self.model.today))
        if self.model.t >= self.covidState["t"] + self.getCovidStateAttr("duration"):
            self.setCovidState(self.covidState["nextState"], self.model.t)

    def _progressCovidMildState(self):
        """Progress from mild symptoms state"""
        self.setSickLeaves(str(self.model.today))
        if self.covidState["duration"] is None:
            # Age-specific branch to 'severe' vs 'recovered' with vaccination modifier
            if self.getAgeGroup() == "young":
                if np.random.rand() < self.p.p_mild_severe_young * (
                    (1 - self.p.p_vax) ** int(self.p.covid_settings == "VAX")
                ):
                    self.setCovidState(
                        "mild",
                        self.model.t,
                        lognormal(self.p.T_mild_severe_mean, self.p.T_mild_severe_std),
                        "severe",
                    )
                else:
                    self.setCovidState(
                        "infected non-sympotomatic",
                        self.model.t,
                        lognormal(
                            self.p.T_mild_recovered_mean, self.p.T_mild_recovered_std
                        ),
                        "recovered",
                    )
            elif self.getAgeGroup() == "working":
                if np.random.rand() < self.p.p_mild_severe_working * (
                    (1 - self.p.p_vax) ** int(self.p.covid_settings == "VAX")
                ):
                    self.setCovidState(
                        "mild",
                        self.model.t,
                        lognormal(self.p.T_mild_severe_mean, self.p.T_mild_severe_std),
                        "severe",
                    )
                else:
                    self.setCovidState(
                        "infected non-sympotomatic",
                        self.model.t,
                        lognormal(
                            self.p.T_mild_recovered_mean, self.p.T_mild_recovered_std
                        ),
                        "recovered",
                    )
            elif self.getAgeGroup() == "elderly":
                if np.random.rand() < self.p.p_mild_severe_elderly * (
                    (1 - self.p.p_vax) ** int(self.p.covid_settings == "VAX")
                ):
                    self.setCovidState(
                        "mild",
                        self.model.t,
                        lognormal(self.p.T_mild_severe_mean, self.p.T_mild_severe_std),
                        "severe",
                    )
                else:
                    self.setCovidState(
                        "infected non-sympotomatic",
                        self.model.t,
                        lognormal(
                            self.p.T_mild_recovered_mean, self.p.T_mild_recovered_std
                        ),
                        "recovered",
                    )
        else:
            if self.model.t >= self.covidState["t"] + self.getCovidStateAttr(
                "duration"
            ):
                self.setCovidState(self.covidState["nextState"], self.model.t)

    def _progressCovidSevereState(self):
        """Progress from severe symptoms state"""
        self.setSickLeaves(str(self.model.today))
        if self.covidState["duration"] is None:
            # Branch to 'critical' or 'recovered' by age
            if self.getAgeGroup() == "young":
                if np.random.rand() < self.p.p_severe_critical_young:
                    self.setCovidState(
                        "severe",
                        self.model.t,
                        lognormal(
                            self.p.T_severe_critical_mean, self.p.T_severe_critical_std
                        ),
                        "critical",
                    )
                else:
                    self.setCovidState(
                        "severe",
                        self.model.t,
                        lognormal(
                            self.p.T_severe_recovered_mean,
                            self.p.T_severe_recovered_std,
                        ),
                        "recovered",
                    )
            elif self.getAgeGroup() == "working":
                if np.random.rand() < self.p.p_severe_critical_working:
                    self.setCovidState(
                        "severe",
                        self.model.t,
                        lognormal(
                            self.p.T_severe_critical_mean, self.p.T_severe_critical_std
                        ),
                        "critical",
                    )
                else:
                    self.setCovidState(
                        "severe",
                        self.model.t,
                        lognormal(
                            self.p.T_severe_recovered_mean,
                            self.p.T_severe_recovered_std,
                        ),
                        "recovered",
                    )
            elif self.getAgeGroup() == "elderly":
                if np.random.rand() < self.p.p_severe_critical_elderly:
                    self.setCovidState(
                        "severe",
                        self.model.t,
                        lognormal(
                            self.p.T_severe_critical_mean, self.p.T_severe_critical_std
                        ),
                        "critical",
                    )
                else:
                    self.setCovidState(
                        "severe",
                        self.model.t,
                        lognormal(
                            self.p.T_severe_recovered_mean,
                            self.p.T_severe_recovered_std,
                        ),
                        "recovered",
                    )
        else:
            if self.model.t >= self.covidState["t"] + self.getCovidStateAttr(
                "duration"
            ):
                self.setCovidState(self.covidState["nextState"], self.model.t)

    def _progressCovidCriticalState(self):
        """Progress from critical state"""
        self.setSickLeaves(str(self.model.today))
        if self.covidState["duration"] is None:
            # Branch to death vs recovery by age
            if self.getAgeGroup() == "young":
                if np.random.rand() < self.p.p_critical_death_young:
                    self.setCovidState(
                        "critical",
                        self.model.t,
                        lognormal(
                            self.p.T_critical_death_mean, self.p.T_critical_death_std
                        ),
                        "dead",
                    )
                else:
                    self.setCovidState(
                        "critical",
                        self.model.t,
                        lognormal(
                            self.p.T_critical_recovered_mean,
                            self.p.T_critical_recovered_std,
                        ),
                        "recovered",
                    )
            elif self.getAgeGroup() == "working":
                if np.random.rand() < self.p.p_critical_death_working:
                    self.setCovidState(
                        "critical",
                        self.model.t,
                        lognormal(
                            self.p.T_critical_death_mean, self.p.T_critical_death_std
                        ),
                        "dead",
                    )
                else:
                    self.setCovidState(
                        "critical",
                        self.model.t,
                        lognormal(
                            self.p.T_critical_recovered_mean,
                            self.p.T_critical_recovered_std,
                        ),
                        "recovered",
                    )
            elif self.getAgeGroup() == "elderly":
                if np.random.rand() < self.p.p_critical_death_elderly:
                    self.setCovidState(
                        "critical",
                        self.model.t,
                        lognormal(
                            self.p.T_critical_death_mean, self.p.T_critical_death_std
                        ),
                        "dead",
                    )
                else:
                    self.setCovidState(
                        "critical",
                        self.model.t,
                        lognormal(
                            self.p.T_critical_recovered_mean,
                            self.p.T_critical_recovered_std,
                        ),
                        "recovered",
                    )
        else:
            if self.model.t >= self.covidState["t"] + self.getCovidStateAttr(
                "duration"
            ):
                self.setCovidState(self.covidState["nextState"], self.model.t)

    def _progressCovidRecoveredState(self):
        """Progress from recovered state to immunity or susceptible"""
        # With some probability, move to temporary immunity; otherwise reset to None
        if self.getAgeGroup() == "young":
            if np.random.rand() < self.p.p_recovered_immun_young:
                self.setCovidState("immunized", self.model.t, 180)
            else:
                self.setCovidState()
        elif self.getAgeGroup() == "working":
            if np.random.rand() < self.p.p_recovered_immun_working:
                self.setCovidState("immunized", self.model.t, 180)
            else:
                self.setCovidState()
        elif self.getAgeGroup() == "elderly":
            if np.random.rand() < self.p.p_recovered_immun_elderly:
                self.setCovidState("immunized", self.model.t, 180)
            else:
                self.setCovidState()

    def _progressCovidImmunizedState(self):
        """Progress from immunized state"""
        # Immunity wears off after 'duration' days
        if self.model.t >= self.covidState["t"] + self.getCovidStateAttr("duration"):
            self.setCovidState()

    def _progressCovidDeadState(self):
        """Handle COVID death"""
        # Reset agent economic activity if dead (model will prune later)
        self.covid_death += 1
        self.reset()

    def progressCovid(self):
        """Main COVID progression dispatcher by current state"""
        if self.covidState["state"] == "exposed":
            self._progressCovidExposedState()
        elif self.covidState["state"] == "infected non-sympotomatic":
            self._progressCovidInfectedNonsympotomaticState()
        elif self.covidState["state"] == "mild":
            self._progressCovidMildState()
        elif self.covidState["state"] == "severe":
            self._progressCovidSevereState()
        elif self.covidState["state"] == "critical":
            self._progressCovidCriticalState()
        elif self.covidState["state"] == "recovered":
            self._progressCovidRecoveredState()
            self.resetSickLeaves()
        elif self.covidState["state"] == "immunized":
            # Mutation risk while immunized (re-exposure)
            if np.random.rand() < self.p.p_mutation * (
                (1 - self.p.p_vax) ** int(self.p.covid_settings == "VAX")
            ):
                self.setCovidState("exposed", self.model.t)
            else:
                self._progressCovidImmunizedState()
        elif self.covidState["state"] == "dead":
            self._progressCovidDeadState()

    # ----------------------------------------
    # Sick leave bookkeeping
    # ----------------------------------------
    def setSickLeaves(self, date):
        """Record sick leave date"""
        self.sickLeaves.append(date)

    def getSickLeaves(self):
        """Get list of sick leave dates"""
        return self.sickLeaves

    def resetSickLeaves(self):
        """Clear sick leave records"""
        self.sickLeaves = []

    # ----------------------------------------
    # Convenience flags
    # ----------------------------------------
    def isDead(self):
        """Check if consumer is dead"""
        return self.dead

    def isEmployed(self):
        """Check if consumer is employed"""
        return self.employed

    # ----------------------------------------
    # Credit placeholders (unused in snippet but kept for compatibility)
    # ----------------------------------------
    def setObtainedCredit(self, obtainedCredit):
        """Set obtained credit amount"""
        self.obtainedCredit = obtainedCredit
        self.obtainedCreditList[-1] = np.sum([obtainedCredit])

    def getObtainedCredit(self):
        """Get obtained credit amount"""
        return self.obtainedCredit

    # ----------------------------------------
    # Reset mortality
    # ----------------------------------------
    def setDead(self):
        """Zero-out economic state and mark as dead"""
        self.deposit = 0
        self.div = 0
        self.wealthList = [0]
        self.desired_consumption = 0
        self.consumption = 0
        self.employed = False
        self.belongToFirm = None
        self.wage = 0
        self.income = 0
        self.dead = True
