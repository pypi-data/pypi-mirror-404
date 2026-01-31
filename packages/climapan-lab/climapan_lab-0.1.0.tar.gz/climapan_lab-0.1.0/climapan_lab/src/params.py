parameters = {
    "settings": "BAU",  # BAU, CT or CTR{a,b,c,d}
    "covid_settings": None,  # "BAU", "DIST", "LOCK", "VAX"
    "verboseFlag": False,
    "energySectorFlag": True,
    "climateModuleFlag": False,
    # Agents count (should be fixed)
    "c_agents": 5000,
    "capitalists": 150,
    "green_energy_owners": 12,
    "brown_energy_owners": 3,
    "b_agents": 1,
    "csf_agents": 6,
    "cpf_agents": 2,
    "g_agents": 1,
    # Time
    "start_date": "1980-01-01",
    "covid_start_date": "2020-01-01",
    "steps": 16435,  # + 365*2, # 8401, #4383 #36525
    "seed": 69,
    "capital_length": 20,
    # Consumer parameter
    "initialProbabilityToBeEmployed": 1,
    "unemploymentDole": 196.289062,  # (0, 1800)
    "minimumWage": 1800,
    "owner_endownment": 6241.40625,  # (2400, 20000)
    "worker_endownment": 2400,
    "wageAdjustmentRate": 0.001,  # in wage adjustment equation for C-firms #(0, 0.01)
    "subsistenceLevelOfConsumption": 49.5507812,  # (10, 50)
    "worker_additional_consumption": 5.09130859,  # (1, 50)int
    "owner_additional_consumption": 61,  # (50, 200)int
    "sick_reduction": 12,
    "consumption_growth": 0.00162,  # (0, 0.01)
    "consumption_var": 0.0719,  # (0, 0.1)
    "taxRate": 0.1,
    "incomeTaxRate": 0.1,
    "co2_price": 25,
    "co2_tax": 0.025,
    "ownerProportionFromProfits": 0.6558,  # (0, 1)
    "energyOwnerProportionFromProfits": 0.7944,  # (0, 1)
    "debtCancelledOnfinancialDifficulty": False,
    "bankResInit": 7.241e9,  # (0, 1e10)
    "bankIL": 0.1205,  # (0.0073, 0.2)
    "bankID": 0.0073,
    "bankICB": 0.002,
    "bankICB_P": 0.0075,
    "gammaRRR": 0.1,
    "iB": 0.1,
    "greenLoanRepayPeriod": 36,
    "brownLoanRepayPeriod": 36,
    "defaultProbAlpha": 1,
    # "targetInflation": 0.02,
    # "bankCredibility": 0.5,
    # "bankEquityEta": 0.08,
    # "inflationRateSensitivity": 0.1,
    "depreciationRate": 0.2,  # (0, 0.5)
    "forecast_discount_factor": 0.9067,  # (0, 1)
    "ETA_PRODUCTION_CAPITAL": (
        (2.15 - 1.0) / 2.15
    ),  # parameter regulating capital production, (calibrate the x inside of (x - 1)/x) #(1, 10)
    "ETA_PRODUCTION": (
        (2.0 - 1.0) / 2.0
    ),  # parameter regulating production function == might be the same value as the rho defined above #(1, 10)
    "mark_up_factor": 0.522,  # (0, 1)
    "mark_up_alpha": 0.556,  # (0.25, 1)
    "mark_up_beta": 0.444,  # (0, 0.75) #mark_up_alpha + mark_up_beta = 1
    # "capital_multiplier": 2.66,
    "capital_growth_rate": 0.0232,  # (0, 0.2)
    "mark_up_adjustment": 0.01,
    # Firms production parameter (fixed value)
    "rho_labour": 80,  # (10, 60)
    "rho_energy": 100,  # (60, 200)
    "rho_labour_K": 60,  # (30, 80)
    "rho_energy_K": 120,  # (80, 500)
    # beware these are the alphas of the production fucntion! of the C-firm
    "beta_labour": 0.25,
    "beta_capital": 0.4,
    "beta_energy": 0.35,
    # beware these are the alphas of the production fucntion! of the K-firm
    "beta_labour_K": 0.05,
    "beta_capital_K": 0.55,
    "beta_energy_K": 0.4,
    "reserve_ratio": 0.3,  # (0, 0.5)
    # For the energy sector
    "energy_price_growth": 0.0089,  # (0, 0.1)
    "base_green_energy_price": 60.254,  # (0, 200)
    "fossil_fuel_price": 1.514,  # (0, 100) (fossil_fuel_price < base_green_energy_price)
    "fossil_fuel_price_growth_rate": 0.00848,  # (0, 0.01)
    # None for turning off shock
    "climateShockMode": "None",
    # "climateShockMode": "Idiosyncratic",
    "climate_shock_start": 120,  # number of months until shock start to activate
    "climateWindSpeed": 0.7625,  # 0.9,
    "climateZetaGreen": 0.01,  # 0.01, # emission intensity green firms
    "climateZetaBrown": 0.5,  # 0.10, # emission intensity dirty firms
    "climateZetaAlpha": 0.2,
    "climateZetaBeta": 1e25,
    "CO2_offset": 8.03e9,
    "climateAlpha_conc": 0.00000015,  # 0.3, # parameter regulating emissions concentrations
    "climateBeta_conc": 0.7,  # 0.0005, # parameter regulating concentrations converge to pre-industrial levels
    "climateConc_t0": 1000,  # concentrations at the beginning of the simulation
    "climateConc_pre": 500,  # pre-industrial concentrations
    "climateGammaRF": 4.5,  # 1, # parameter regulating radiative force
    "climateSensitivity": 6.90625,  #
    "climateAlpha_phi": -42.7,  # in e-folding time equation phi = max(climateAlpha_phi + climateBeta_phiL*climateSensitivity + climateBeta_phiQ*climateSensitivity**2, 1)
    "climateBeta_phiL": 29.1,  # in e-folding time equation phi = max(climateAlpha_phi + climateBeta_phiL*climateSensitivity + climateBeta_phiQ*climateSensitivity**2, 1)
    "climateBeta_phiQ": 0.001,  # in e-folding time equation phi = max(climateAlpha_phi + climateBeta_phiL*climateSensitivity + climateBeta_phiQ*climateSensitivity**2, 1)
    "climateT0": 0,  # 1, # Temperature at time 0
    "climateAlpha_d": 0.05,  # Benchmark damage
    "climateSigma_d": 0.9,  # Storm sensitivity to atmospheric CO2 concentrations
    "climateEps_etd": -0.514,  # income elasticity of storm energy
    "climateGamma_etd": 1,  # a parameter for calculating Temperature damage on energy
    "climateBeta_d": 0.05,  # Benchmark mortality
    "climateEps_etm": -0.501,  # income elasticity of storm mortality and is calibrated following Toya and Skidmore 2007
    "climateGamnma_etm": 1,
    "psi_h": 0.1,
    "psi_f_g": 0.15,
    "psi_f_b": 0.25,
    "alpha_T": 1,
    "alpha_P": 1.5,
    "T_threshold": 10,
    "P_threshold": 15,
    ## Government
    "fiscal_time": 100,
    "csfirm_netWorth": 2750000,
    "cpfirm_netWorth": 82000000,
    "lumpSumState": True,
    "lumpSum": 100000,
    "csfirm_avgDeposit": 2000,
    "cpfirm_avgDeposit": 3000,
    "alpha_f": 0.1,
    "alpha_h": 0.1,
    ## Covid
    "production_cost": 500,
    "initialExposer": 1000,
    "dispersion_community": None,
    "overshoot_community": 1.2,
    "num_contacts_community": 20,
    "p_contact_community": 0.005,
    "dispersion_firms": None,
    "overshoot_firms": 1.2,
    "num_contacts_firms": 20,
    "p_contact_firms": 0.01,
    "p_mutation": 0.1,
    "T_susceptible_mild_mean": 8.5,  # 4.5
    "T_susceptible_mild_std": 1.5,
    "p_susceptible_mild_young": 0.9,
    "p_susceptible_mild_working": 0.9,
    "p_susceptible_mild_elderly": 0.9,
    "T_exposed_mild_mean": 3.1,  # 1.1
    "T_exposed_mild_std": 0.9,
    "p_exposed_mild_young": 0.7,
    "p_exposed_mild_working": 0.9,
    "p_exposed_mild_elderly": 0.9,
    "T_nonsym_recovered_mean": 8.0,
    "T_nonsym_recovered_std": 2.0,
    "T_mild_severe_mean": 10.6,  # 6.6
    "T_mild_severe_std": 4.9,
    "p_mild_severe_young": 0.005,
    "p_mild_severe_working": 0.7,
    "p_mild_severe_elderly": 0.25,
    "T_mild_recovered_mean": 8.0,
    "T_mild_recovered_std": 2.0,
    "T_severe_critical_mean": 1.5,
    "T_severe_critical_std": 2.0,
    "p_severe_critical_young": 0.001,
    "p_severe_critical_working": 0.01,
    "p_severe_critical_elderly": 0.8,
    "T_severe_recovered_mean": 18.1,
    "T_severe_recovered_std": 6.3,
    "T_critical_death_mean": 10.7,
    "T_critical_death_std": 4.8,
    "p_critical_death_young": 0.00001,
    "p_critical_death_working": 0.01,
    "p_critical_death_elderly": 0.2,
    "T_critical_recovered_mean": 18.1,
    "T_critical_recovered_std": 6.3,
    "p_recovered_immun_young": 0.99,
    "p_recovered_immun_working": 0.9,
    "p_recovered_immun_elderly": 0.7,
    ## Covid policies
    # Social Distancing
    "inf_threshold": 0.3,  # 0.6
    "p_sd": 0.1,  # (0,1)
    # Lock down
    "p_lockdown": 0.4,  # 0.5
    "duration_LD": 14,
    "num_C_firms_LD": 0.6,
    "num_K_firms_LD": 0.4,
    "pandemicWageTransfer": 3000,
    "lock_down_production_utilization": 0.6,
    # Vaccines
    "p_vax": 0.8,  # (0,8)
}
