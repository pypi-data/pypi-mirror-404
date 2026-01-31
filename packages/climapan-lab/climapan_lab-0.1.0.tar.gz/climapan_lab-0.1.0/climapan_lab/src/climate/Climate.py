import copy

import ambr as am
import numpy as np

# ============================================================================
#                             Climate Module
# ============================================================================
# Purpose:
#   The Climate module tracks emissions, CO₂ concentrations, radiative forcing,
#   temperature changes, and potential climate shocks that affect the economy.
#
# Step-by-step per simulation month (called from EconModel.stepwise_after_production):
#   1) Aggregate emissions
#      - Collect emissions from all firms, scaled by their energy type (green vs. brown).
#      - Track both cumulative and per-step emissions.
#
#   2) Update carbon cycle
#      - Compute new CO₂ concentration with accumulation (alpha_c) and
#        mean-reversion toward a preindustrial baseline (beta_c).
#
#   3) Radiative forcing & temperature dynamics
#      - Compute radiative forcing from concentration ratios.
#      - Update temperature using e-folding dynamics based on climate sensitivity (CS).
#
#   4) Detect & trigger climate shocks
#      - If temperature exceeds threshold (relative to an earlier baseline),
#        activate a shock flag and compute mortality/impact under one of two modes:
#      - Aggregate Population Shock (AggPop) → mortality at population level.
#      - Idiosyncratic Shock → survival calculated individually.
#
#   5) Compute damages (optional post-processing)
#      - process_aggregate_damage() estimates two metrics:
#      - ETD (output/economic damages).
#      - ETM (labor/employment damages).
#
# Public interface (called by EconModel):
#   - initGDP(GDP): set baseline GDP for scaling damages.
#   - initAggregatedIncome(): set baseline household income for scaling shocks.
#   - progress(list_firm): advance emissions, climate state, and shocks by one step.
#   - getPM(), getAliveConsumersPostShock(): return shock magnitudes for AggPop/Idiosyncratic.
# ============================================================================


class Climate(am.Agent):
    def setup(self):
        # ----------------------------------------
        # Parameters & Core State
        # ----------------------------------------
        self.climate_shock_start = (
            self.p.climate_shock_start
        )  # Month index after which shocks can fire

        # NOTE: The trailing commas below create 1-element tuples (kept as-is; do not change logic).
        # If you intended scalars, remove the trailing commas in the assignments.
        self.zeta_g = (
            self.p.climateZetaGreen,
        )  # Emission intensity for green tech (tuple)
        self.zeta_b = (
            self.p.climateZetaBrown,
        )  # Emission intensity for brown tech (tuple)

        # Carbon cycle parameters
        self.alpha_c = (
            self.p.climateAlpha_conc
        )  # Accumulation coefficient for concentration
        self.beta_c = (
            self.p.climateBeta_conc
        )  # Reversion rate to preindustrial concentration
        self.conc_t0 = self.p.climateConc_t0  # Baseline (preindustrial) concentration
        self.conc_t = copy.copy(self.conc_t0)  # Current concentration
        self.conc_pre = (
            self.p.climateConc_pre
        )  # Reference "pre" concentration (for mean reversion)

        # Forcing & temperature parameters
        self.gammaRF = self.p.climateGammaRF  # Radiative Forcing coefficient
        self.CS = (
            self.p.climateSensitivity
        )  # Equilibrium climate sensitivity (°C per CO2 doubling)

        # E-folding time (phi) as a function of CS (minimum 1 to avoid division by zero)
        self.phi = np.max(
            [
                self.p.climateAlpha_phi
                + self.p.climateBeta_phiL * self.CS
                + self.p.climateBeta_phiQ * self.CS**2,
                1,
            ]
        )

        # Emissions state
        self.EM = 0  # Cumulative emissions proxy (lifetime)
        self.step_EM = 0  # Emissions at the current step (month)

        # Temperature state
        self.T = self.p.climateT0  # Current temperature
        self.T_list = [self.T]  # Keep history for shock detection

        # Damage function parameters (used by process_aggregate_damage)
        self.alpha_d = self.p.climateAlpha_d
        self.sigma_d = self.p.climateSigma_d
        self.eps_etd = self.p.climateEps_etd
        self.gamma_etd = self.p.climateGamma_etd
        self.beta_d = self.p.climateBeta_d
        self.eps_etm = self.p.climateEps_etm
        self.gamma_etm = self.p.climateGamnma_etm  # NOTE: parameter name as provided

        # Forcing & damages placeholders
        self.RF = 0  # Radiative forcing
        self.ETD = 0  # Economic (output) damages
        self.ETM = 0  # Labor/employment-related damages

        # CO2 stock proxy (EM + offset)
        self.CO2 = self.EM + self.p.CO2_offset

        # Shock latch (read by EconModel to apply population/wealth losses)
        self.shockHappens = False

    def initGDP(self, GDP):
        """Store baseline GDP for normalization in damage functions or shock scaling."""
        self.GDP_t0 = GDP
        if self.p.verboseFlag:
            print("initial GDP", self.GDP_t0)

    def initAggregatedIncome(self):
        """Store baseline aggregate income (wage + non-wage) for later shock scaling."""
        self.aggregatedIncome_t0 = np.sum(
            list(self.model.aliveConsumers.income)
        ) + np.sum(list(self.model.aliveConsumers.wage))

    def progress(self, list_firm):
        """
        Advance the climate system by one economic period (called monthly from EconModel).

        Steps:
          1) Aggregate emissions from firms (green vs brown).
          2) Update CO2 concentration with accumulation & reversion.
          3) Compute radiative forcing and update temperature using e-folding time.
          4) If temperature jump condition met, compute & flag a climate shock.
        """

        # ----------------------------------------
        # (1) Emissions aggregation at t
        # ----------------------------------------
        self.workers_t = 0
        self.step_EM = 0

        # Scenario-specific injection: S3MOD (kept as in original code)
        if (
            (self.model.t >= self.model.fiscalDate)
            and self.p.covid_settings
            and self.p.settings == "S3MOD"
            and self.model.fiscal_count < 3
        ):
            # The commented block shows an alternative approach of boosting green production.
            # Here, we add a fixed green emissions proxy to EM as in the original logic.
            # """for firm in list_firm:
            #     if firm.getUseEnergy() == 'green':
            #         firm.update_actual_production(self.p.lumpSum / firm.getPrice())"""
            self.EM += self.p.climateZetaGreen * 1500

        # Sum emissions intensity * production across firms; count workers for damages
        for firm in list_firm:
            if firm.getUseEnergy() == "green":
                # NOTE: zeta_g is a tuple per setup; multiplication will broadcast accordingly.
                self.EM += np.sum(self.p.climateZetaGreen * firm.actual_production)
                self.step_EM += np.sum(self.p.climateZetaGreen * firm.actual_production)
            else:
                self.EM += self.p.climateZetaBrown * firm.actual_production
                self.step_EM += np.sum(self.p.climateZetaBrown * firm.actual_production)
            try:
                self.workers_t += np.sum(firm.getNumberOfLabours())
            except:
                # Some firm types may not have a labor accessor — ignore silently to preserve flow.
                pass

        # ----------------------------------------
        # (2) CO2 concentration update (simple box)
        # ----------------------------------------
        # CO2 stock proxy: monotone mapping from emissions + offset (original non-linear form preserved)
        self.CO2 = (
            np.log10(self.p.climateZetaBeta * self.EM)
            / np.log10(
                np.log10(self.p.climateZetaBeta * self.EM) * 1e9 + (self.p.CO2_offset)
            )
        ) * 1e9 + self.p.CO2_offset

        # Accumulation (alpha_c * CO2) and mean-reversion (beta_c * deviation from conc_pre)
        self.conc_t += np.sum(self.alpha_c * self.CO2)
        self.conc_t -= np.sum(self.beta_c * (self.conc_t - self.conc_pre))

        # ----------------------------------------
        # (3) Forcing & temperature update
        # ----------------------------------------
        # Radiative forcing is proportional to log(concentration ratio)
        self.RF = self.gammaRF * np.log10(self.conc_t / self.conc_t0)

        # Temperature follows a first-order lag toward equilibrium (scaled by CS)
        # T_t = (1 - 1/phi)*T_{t-1} + (1/phi) * (CS / (5.35*ln2)) * RF
        self.T = (1 - (1 / self.phi)) * self.T + (1 / self.phi) * (
            self.CS / (5.35 * np.log(2))
        ) * self.RF
        self.T_list.append(self.T)

        # ----------------------------------------
        # (4) Shock detection & triggering
        # ----------------------------------------
        # After enough months have elapsed (climate_shock_start), compare T to earlier T.
        if self.model.month_no > self.climate_shock_start:
            # print((self.T - self.T_list[-12]) / self.T_list[-12], self.T)
            if (self.T - self.T_list[-self.climate_shock_start]) / self.T_list[
                -self.climate_shock_start
            ] > 20:
                if self.p.climateShockMode == "AggPop":
                    self._induce_aggregate_population_climate_shock()
                    self.shockHappens = True
                elif self.p.climateShockMode == "Idiosyncratic":
                    self._induce_idiosyncratic_climate_shock()
                    self.shockHappens = True

    def _induce_aggregate_population_climate_shock(self):
        """
        Compute population-level mortality (PM) scaled by income and temperature.
        EconModel will then remove that many consumers and apply wealth losses.
        """
        aliveConsumers = self.model.aliveConsumers.select(
            self.model.aliveConsumers.isDead() != True
        )
        aggregatedIncome = np.sum(list(self.model.aliveConsumers.getIncome())) + np.sum(
            list(self.model.aliveConsumers.getWage())
        )
        # PM = baseline_mortality * pop_size * (income / baseline_income)^eps * (1 + sigma_d*T)^{wind_speed}
        self.PM = (
            self.p.currentMortality
            * len(aliveConsumers)
            * (aggregatedIncome / self.aggregatedIncome_t0) ** self.eps_etd
            * ((1 + self.sigma_d * self.T) ** self.p.climateWindSpeed)
        )

    def _induce_idiosyncratic_climate_shock(self):
        """
        Compute post-shock survivors using an omega factor based on temperature.
        EconModel will infer the number of deaths from the difference with current alive.
        """
        # Omega > 1 as temperature rises (per original formula); keep as provided.
        omega = 1 / (1 - 0.0028 * self.T**2)
        # NOTE: The selection condition uses Python truth evaluation; preserved as in source.
        self.aliveConsumersPostShock = omega * len(
            self.model.aliveConsumers.select(
                self.model.aliveConsumers.isDead() != True
                and self.model.aliveConsumers.isEmployed()
            )
        )

    def process_aggregate_damage(self):
        """
        Compute aggregate damages:
          - ETD (economic/output) as a function of GDP, concentration ratio, and parameters.
          - ETM (labor/employment) as a function of workers_t, GDP ratio, and parameters.
        These are stored as attributes and can be recorded/used elsewhere.
        """
        # Output damages (concentration ratio raised to gamma_etd, scaled by GDP and sigma_d)
        self.ETD = (
            self.alpha_d
            * self.model.GDP
            * ((self.model.GDP / self.GDP_t0) ** self.eps_etd)
            * self.sigma_d
            * ((self.conc_t / self.conc_t0) ** self.gamma_etd - 1)
        )
        self.ETM = (
            self.beta_d
            * self.workers_t
            * ((self.model.GDP / self.GDP_t0) ** self.eps_etd)
            * self.sigma_d
            * ((self.conc_t / self.conc_t0) ** self.gamma_etm - 1)
        )

    # ----------------------------------------
    # Getters used externally
    # ----------------------------------------
    def getPM(self):
        """Return population mortality (PM) computed for aggregate shocks."""
        return self.PM

    def getAliveConsumersPostShock(self):
        """Return the computed number of post-shock survivors for idiosyncratic shocks."""
        return self.aliveConsumersPostShock
