"""
CliMaPan-Lab: Climate-Pandemic Economic Modeling Laboratory
============================================================
Main Simulation Runner

This script orchestrates economic model simulations with various scenarios and settings.
Supports single runs, multiple runs (batch over seeds), and sensitivity analysis via
parameter sweeps.

Key Features:
  - Single experiment or batch simulations
  - Multi-parameter sweep capability (Cartesian product)
  - Parallel execution via joblib
  - Flexible output formats (CSV, NumPy, pickle)
  - Optional visualization generation
"""

import argparse
import copy
import json
import os
import pickle
import warnings
from datetime import datetime
from itertools import product

import ambr as am
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

warnings.filterwarnings("ignore")

from .base_params import economic_params as parameters
from .src.models import EconModel
from .src.utils import (
    plotBankSummary,
    plotClimateModuleEffects,
    plotConsumersSummary,
    plotConsumptionInflationSummary,
    plotCovidStatistics,
    plotEnergyFirmsDemands,
    plotGoodsFirmSalesSummary,
    plotGoodsFirmsDemandsSummary,
    plotGoodsFirmsProfitSummary,
    plotGoodsFirmWorkersSummary,
)

# Global variables for variable extraction configuration
varListNpy = []  # Variables to export as NumPy arrays
varListCsv = []  # Variables to export as CSV files


class AgentPyCompatibleResults:
    """Wrapper to make ambr results compatible with AgentPy structure used in CliMaPan-Lab."""

    def __init__(self, ambr_results):
        # Create a structure that mimics result.variables.EconModel
        self.variables = type("Variables", (), {})()
        # ambr returns {'model': df, 'agents': df, ...}
        # We map 'model' df to EconModel and convert to pandas
        if isinstance(ambr_results, dict) and "model" in ambr_results:
            setattr(self.variables, "EconModel", ambr_results["model"].to_pandas())
            # Also attach agents if needed, though mostly EconModel is used
            if "agents" in ambr_results:
                setattr(self.variables, "agents", ambr_results["agents"].to_pandas())
        else:
            # Fallback if it's already in the right format or something else
            # If it's already an AgentPy-like object, just assign its variables
            self.variables = (
                ambr_results.variables if hasattr(ambr_results, "variables") else None
            )


def single_run(
    parameters, idx=0, parent_folder=None, make_stats=False, var_dict=None, args=None
):
    """
    Execute a single simulation experiment.

    Supports optional multi-parameter bookkeeping for parameter sweep experiments.

    Args:
        parameters: Dict of model parameters, or [params_dict, varying_dict] for sweeps
        idx: Index for this run in a parameter sweep
        parent_folder: Parent directory for organizing sweep results
        make_stats: Whether to collect results for later aggregation
        var_dict: Dictionary to store results across multiple runs
        args: Command-line arguments object

    Returns:
        AgentPyCompatibleResults object containing simulation outputs
    """
    # ===== Parameter Configuration =====
    # Detect multi-parameter mode (parameters is [params_dict, varying_dict])
    multi_params = False
    if len(parameters) == 2:
        multi_params = True
        varying_var = parameters[1]  # Dict of varying parameters
        parameters = parameters[0]  # Base parameters dict

    # Generate unique timestamp for this run
    timestamp = datetime.timestamp(datetime.now())

    # Encode varying parameters into folder name for traceability
    if multi_params:
        varying_params = "".join(
            [
                str(list(varying_var.keys())[i]) + str(list(varying_var.values())[i])
                for i in range(len(varying_var))
            ]
        )
    else:
        varying_params = None

    # ===== Output Directory Setup =====
    # Construct folder path based on scenario settings and options
    if (
        args
        and hasattr(args, "climateDamage")
        and args.climateDamage
        and parameters.get("climateShockMode") is not None
    ):
        # Include climate shock mode in folder name
        shockModeList = parameters["climateShockMode"]
        base_name = f"results_{parameters['settings']}_{parameters['covid_settings']}_{''.join(shockModeList)}"

        if parent_folder:
            save_folder = os.path.abspath(f"./{parent_folder}/{base_name}")
        else:
            save_folder = os.path.abspath(f"./results/{base_name}")

        if varying_params is not None:
            save_folder += f"_{varying_params}"
        save_folder += f"_{timestamp}"
    else:
        # Standard folder naming without climate damage
        parameters["climateShockMode"] = None
        base_name = f"results_{parameters['settings']}_{parameters['covid_settings']}"

        if parent_folder:
            save_folder = os.path.abspath(f"./{parent_folder}/{base_name}")
        else:
            save_folder = os.path.abspath(f"./results/{base_name}")

        if varying_params is not None:
            save_folder += f"_{varying_params}"
        save_folder += f"_{timestamp}"

    # ===== Model Execution =====
    model = EconModel(parameters)
    raw_results = model.run()

    # Wrap results for compatibility
    results = AgentPyCompatibleResults(raw_results)

    # Ensure output directory exists
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # ===== Visualization Generation =====
    if args and hasattr(args, "plot") and args.plot:
        print("Plotting the results...")

        # Core economic indicators
        plotConsumersSummary(results, save_folder)
        plotConsumptionInflationSummary(results, save_folder)
        plotBankSummary(results, save_folder)

        # Firm-level analysis
        plotGoodsFirmsProfitSummary(results, save_folder)
        plotGoodsFirmsDemandsSummary(results, save_folder)
        plotGoodsFirmWorkersSummary(results, save_folder)
        plotGoodsFirmSalesSummary(results, save_folder)

        # Sector-specific plots
        if parameters["energySectorFlag"]:
            plotEnergyFirmsDemands(results, save_folder)
        if parameters["climateModuleFlag"]:
            plotClimateModuleEffects(results, save_folder)
        if parameters["covid_settings"]:
            plotCovidStatistics(results, save_folder)

    # ===== NumPy Array Export =====
    # Export selected variables as .npy files for exact precision preservation
    if varListNpy is not None and len(varListNpy) > 0:
        for var in varListNpy:
            if var in results.variables.EconModel.columns:
                # Extract non-null values and preserve array structure
                saving_var = np.array(
                    [
                        i
                        for i in list(results.variables.EconModel[var.strip()].values)
                        if (i is not None)
                    ]
                )
                saving_var = np.array(
                    [[i] if "ndarray" in str(type(i)) else i for i in saving_var]
                )

                # Save with sanitized filename
                filename = f"{save_folder}/{''.join(var.strip().split(' '))}.npy"
                np.save(
                    filename,
                    np.array(
                        [
                            (
                                list(i)
                                if ("ndarray" in str(type(i)) and i.shape != ())
                                else i
                            )
                            for i in list(
                                results.variables.EconModel[var.strip()].values
                            )
                        ]
                    ),
                )

                # Remove from main DataFrame to reduce memory footprint
                results.variables.EconModel = results.variables.EconModel.drop(
                    columns=[var.strip()]
                )

    # ===== CSV Export for Selected Variables =====
    if varListCsv is not None and len(varListCsv) > 0:
        for var in varListCsv:
            if var in results.variables.EconModel.columns:
                # Handle array-like values appropriately
                varList = []
                for i in results.variables.EconModel[var].values:
                    if i is not None and "ndarray" in str(type(i)):
                        varList.append([i])
                    else:
                        varList.append(i)

                # Attempt CSV export (may fail for ragged arrays)
                try:
                    filename = f"{save_folder}/{''.join(var.strip().split(' '))}.csv"
                    pd.DataFrame(
                        [i for i in results.variables.EconModel[var].values]
                    ).to_csv(filename)
                except:
                    pass  # Silently skip problematic columns

    # ===== Main Results Export =====
    # Save remaining DataFrame columns as compressed CSV
    results.variables.EconModel.to_csv(
        f"{save_folder}/single_run.csv.gz", compression="gzip"
    )

    # Collect results for aggregation (parameter sweep mode)
    if make_stats and var_dict is not None:
        var_dict[idx] = results.variables.EconModel

    # ===== Metadata Persistence =====
    # Save full parameter dictionary for reproducibility
    with open(f"{save_folder}/params.txt", "w") as params_file:
        params_file.write(json.dumps(parameters))

    # Save varying parameters separately for sweep experiments
    if multi_params:
        with open(f"{save_folder}/varying_params.txt", "w") as params_file:
            params_file.write(json.dumps(varying_var))

    return results


def multi_run(overall_dict, i, save_folder):
    """
    Execute one simulation within a multi-run batch.

    Handles seed-based reproducibility and per-run output organization.

    Args:
        overall_dict: Shared dictionary to collect results across runs
        i: Run index (seeds start at 60 by convention)
        save_folder: Parent directory for all batch runs
    """
    print(f"Processing run number {i-60+1}")

    # ===== Seed Configuration =====
    # Set unique seed for this run (convention: start at 60)
    parameters["seed"] = i

    # ===== Per-Run Directory Setup =====
    process_save_path = os.path.join(os.path.abspath(f"{save_folder}"), f"run_{i-60}")
    if not os.path.exists(process_save_path):
        os.makedirs(process_save_path)

    # ===== Model Execution =====
    model = EconModel(parameters)
    results = model.run()

    # ===== Optional Visualization =====
    if args and hasattr(args, "plot") and args.plot:
        print("Plotting the results...")

        # Generate all standard plots
        plotConsumersSummary(results, process_save_path)
        plotConsumptionInflationSummary(results, process_save_path)
        plotBankSummary(results, process_save_path)
        plotGoodsFirmsProfitSummary(results, process_save_path)
        plotGoodsFirmsDemandsSummary(results, process_save_path)
        plotGoodsFirmWorkersSummary(results, process_save_path)
        plotGoodsFirmSalesSummary(results, process_save_path)

        # Conditional plots based on model configuration
        if parameters["energySectorFlag"]:
            plotEnergyFirmsDemands(results, process_save_path)
        if parameters["climateModuleFlag"]:
            plotClimateModuleEffects(results, process_save_path)

    # ===== NumPy Export =====
    if varListNpy is not None and len(varListNpy) > 0:
        for var in varListNpy:
            if var in results.variables.EconModel.columns:
                # Extract and structure data for NumPy storage
                saving_var = np.array(
                    [
                        i
                        for i in list(results.variables.EconModel[var.strip()].values)
                        if (i is not None)
                    ]
                )
                saving_var = np.array(
                    [[i] if "ndarray" in str(type(i)) else i for i in saving_var]
                )

                # Save and remove from DataFrame
                filename = f"{process_save_path}/{''.join(var.strip().split(' '))}.npy"
                np.save(filename, saving_var)
                results.variables.EconModel = results.variables.EconModel.drop(
                    columns=[var.strip()]
                )

    # ===== CSV Export =====
    if varListCsv is not None and len(varListCsv) > 0:
        for var in varListCsv:
            if var in results.variables.EconModel.columns:
                # Prepare data for CSV export
                varList = []
                for i in results.variables.EconModel[var].values:
                    if i is not None and "ndarray" in str(type(i)):
                        varList.append([i])
                    else:
                        varList.append(i)

                filename = f"{process_save_path}/{''.join(var.strip().split(' '))}.csv"
                pd.DataFrame(
                    [i for i in results.variables.EconModel[var].values]
                ).to_csv(filename)

    # ===== Model Persistence =====
    # Pickle the entire model object for detailed post-analysis
    with open(f"{process_save_path}/model_run_{i-60}.pickle", "wb") as handle:
        pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Store results for batch aggregation
    overall_dict[f"Run_0{i-60}"] = results.variables.EconModel


def main():
    """
    Main entry point for console script execution.

    Orchestrates the simulation workflow based on command-line arguments:
    - Parses CLI arguments for scenario configuration
    - Handles single vs. multi-run execution modes
    - Manages parameter sweep experiments
    - Coordinates parallel execution
    """
    # ========================================
    # Command-Line Argument Configuration
    # ========================================
    parser = argparse.ArgumentParser(
        description="CliMaPan-Lab Economic Model Simulation Runner"
    )

    # Simulation mode arguments
    parser.add_argument(
        "-n",
        "--noOfRuns",
        type=int,
        default=1,
        help="Number of simulation runs (1=single, >1=batch with different seeds)",
    )

    # Scenario configuration
    parser.add_argument(
        "-s",
        "--settings",
        type=str,
        default="BAU",
        help="Economic scenario: BAU, CT, CTRa, CTRb, CTRc, CTRd",
    )
    parser.add_argument(
        "-c",
        "--covidSettings",
        type=str,
        default=None,
        help="Pandemic scenario: BAU, DIST, LOCK, VAX",
    )
    parser.add_argument(
        "-d",
        "--climateDamage",
        type=str,
        default="AggPop",
        help="Climate damage type: AggPop, Idiosyncratic, or None",
    )

    # Output configuration
    parser.add_argument(
        "-l",
        "--extractedVarListPathNpy",
        default=None,
        help="Path to .txt file listing variables to export as NumPy arrays",
    )
    parser.add_argument(
        "-v",
        "--extractedVarListPathCsv",
        default=None,
        help="Path to .txt file listing variables to export as CSV files",
    )
    parser.add_argument(
        "-p", "--plot", action="store_true", help="Generate visualization plots"
    )

    # Make args globally accessible for nested functions
    global args
    args = parser.parse_args()

    # ========================================
    # Parameter Configuration
    # ========================================
    # Apply scenario settings to global parameters
    if args.settings:
        parameters["settings"] = args.settings.strip()

    if args.covidSettings:
        parameters["covid_settings"] = args.covidSettings.strip()

    # ========================================
    # Variable Export List Loading
    # ========================================
    # Load NumPy export variable list
    if (
        args.extractedVarListPathNpy is not None
        and os.path.exists(args.extractedVarListPathNpy.strip())
        and args.extractedVarListPathNpy.strip().endswith(".txt")
    ):
        file = args.extractedVarListPathNpy.strip()
        varListNpy = []
        with open(file) as f:
            varListNpy = [line.strip() for line in f.readlines() if line.strip()]
    else:
        varListNpy = []

    # Load CSV export variable list
    if (
        args.extractedVarListPathCsv is not None
        and os.path.exists(args.extractedVarListPathCsv.strip())
        and args.extractedVarListPathCsv.strip().endswith(".txt")
    ):
        file = args.extractedVarListPathCsv.strip()
        varListCsv = []
        with open(file) as f:
            varListCsv = [line.strip() for line in f.readlines() if line.strip()]
    else:
        varListCsv = []

    # Make export lists globally accessible
    globals()["varListNpy"] = varListNpy
    globals()["varListCsv"] = varListCsv

    # ========================================
    # Execution Mode Selection
    # ========================================
    if args.noOfRuns == 1:
        # ===== Single Run Mode =====
        print("Start simulating...")
        print(f"Climate damage mode: {args.climateDamage}")

        # Check for list-valued parameters (indicates sweep mode)
        count = sum(1 for v in parameters.values() if isinstance(v, list))

        if count == 0:
            # Standard single run
            single_run(parameters)
        else:
            # ===== Parameter Sweep Mode =====
            print("Entering multi-parameter sweep mode...")

            # Identify varying parameters
            parameters_combinations = []
            count = 0
            list_of_varying_parameters = {}
            values_of_varying_parameters = {}

            for name, value in parameters.items():
                if isinstance(value, list):
                    list_of_varying_parameters[count] = name
                    values_of_varying_parameters[name] = value
                    parameters_combinations.append(value)
                    count += 1

            # Generate Cartesian product of parameter combinations
            list_parameters_combinations = list(product(*parameters_combinations))
            print(
                f"Parameter sweep will generate {len(list_parameters_combinations)} experiments"
            )

            # Build parameter dictionaries for each combination
            parameters_combinations = []
            for parameter_vars in list_parameters_combinations:
                varying_dict = {}
                params_copy = copy.deepcopy(parameters)

                for i, value in enumerate(parameter_vars):
                    param_name = list_of_varying_parameters[i]
                    params_copy[param_name] = value
                    varying_dict[param_name] = value

                parameters_combinations.append([params_copy, varying_dict])

            # Create parent directory for sweep results
            timestamp = datetime.timestamp(datetime.now())
            parent_folder = f"./results/result_multi_{timestamp}"
            if not os.path.exists(parent_folder):
                os.makedirs(parent_folder)

            var_dict = {}

            # Execute all combinations in parallel
            Parallel(n_jobs=-1, prefer="threads")(
                delayed(single_run)(
                    params,
                    idx,
                    parent_folder=parent_folder,
                    make_stats=True,
                    var_dict=var_dict,
                    args=args,
                )
                for idx, params in enumerate(parameters_combinations)
            )

            # Save base parameter configuration
            with open(f"{parent_folder}/params.txt", "w") as params_file:
                params_file.write(json.dumps(parameters))

        print("Simulation completed.")

    elif args.noOfRuns > 1:
        # ===== Multi-Run Batch Mode =====
        print(f"Starting batch simulation with {args.noOfRuns} runs...")

        # Check for parameter sweeps (not supported in multi-run mode)
        count = sum(1 for v in parameters.values() if isinstance(v, list))

        if count == 0:
            # Standard multi-run over seeds
            overall_dict = {}
            timestamp = datetime.timestamp(datetime.now())

            # Configure output directory with appropriate naming
            if args.climateDamage:
                save_folder = (
                    f"./results/multi_run_results_"
                    f"{parameters['settings']}_{parameters['covid_settings']}_"
                    f"CLIMATE_{timestamp}"
                )
            else:
                parameters["climateShockMode"] = None
                save_folder = (
                    f"./results/multi_run_results_"
                    f"{parameters['settings']}_{parameters['covid_settings']}_"
                    f"{timestamp}"
                )

            if not os.path.exists(save_folder):
                os.makedirs(save_folder)

            # Execute runs in parallel (seeds 60 to 60+N-1)
            Parallel(n_jobs=-1, prefer="threads")(
                delayed(multi_run)(overall_dict, i, save_folder)
                for i in range(60, 60 + args.noOfRuns)
            )

            # Aggregate results into single DataFrame
            result = pd.concat(overall_dict)
            result = result.rename(columns={"Unnamed: 0": "RunNo"})
            result.to_csv(f"{save_folder}/multi_runs.csv.gz", compression="gzip")

            # Save parameter configuration
            with open(f"{save_folder}/params.txt", "w") as params_file:
                params_file.write(json.dumps(parameters))

        else:
            # Multi-parameter + multi-run combination not implemented
            print("ERROR: Parameter sweeps are not supported in multi-run mode.")
            print("Please use either parameter sweeps OR multiple runs, not both.")

        print("Batch simulation completed.")


# ========================================
# Script Entry Points
# ========================================
if __name__ == "__main__":
    main()
