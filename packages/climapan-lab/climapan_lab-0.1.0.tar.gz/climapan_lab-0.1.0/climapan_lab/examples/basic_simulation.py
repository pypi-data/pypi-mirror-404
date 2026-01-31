#!/usr/bin/env python3
"""
Basic simulation example for CliMaPan-Lab.

This example demonstrates how to:
1. Set up and run a basic economic simulation
2. Configure different scenarios (BAU, Climate Tax, COVID policies)
3. Save and analyze results
4. Create basic visualizations

Usage:
    python basic_simulation.py [--scenario BAU|CT|CTR] [--covid BAU|DIST|LOCK|VAX]
"""

import argparse
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from ..base_params import economic_params

# Import the economic model and parameters
from ..model import EconModel
from ..run_sim import single_run


def setup_basic_scenario(
    scenario="BAU", covid_policy="BAU", steps=120, agents_scale=1.0
):
    """
    Set up a basic scenario with configurable parameters.

    Args:
        scenario: Economic scenario ("BAU", "CT", "CTR")
        covid_policy: COVID policy ("BAU", "DIST", "LOCK", "VAX")
        steps: Number of simulation steps (months)
        agents_scale: Scale factor for agent numbers (for testing vs full runs)

    Returns:
        dict: Parameters for the simulation
    """
    params = economic_params.copy()

    # Scale agent numbers for testing vs production
    params.update(
        {
            "c_agents": int(params["c_agents"] * agents_scale),
            "capitalists": int(params["capitalists"] * agents_scale),
            "csf_agents": max(1, int(params["csf_agents"] * agents_scale)),
            "cpf_agents": max(1, int(params["cpf_agents"] * agents_scale)),
            "green_energy_owners": max(
                1, int(params["green_energy_owners"] * agents_scale)
            ),
            "brown_energy_owners": max(
                1, int(params["brown_energy_owners"] * agents_scale)
            ),
            "steps": steps,
            "settings": scenario,
            "covid_settings": covid_policy,
            "verboseFlag": False,
        }
    )

    # Scenario-specific adjustments
    if scenario == "CT":  # Carbon Tax
        params["co2_tax"] = 0.05
        params["co2_price"] = 50
    elif scenario.startswith("CTR"):  # Carbon Tax with Redistribution
        params["co2_tax"] = 0.05
        params["co2_price"] = 50
        params["lumpSum"] = 500000  # Redistribution amount

    # COVID policy adjustments
    if covid_policy == "DIST":  # Social Distancing
        params["num_contacts_community"] = 10  # Reduced contacts
        params["num_contacts_firms"] = 10
    elif covid_policy == "LOCK":  # Lockdown
        params["num_contacts_community"] = 5
        params["num_contacts_firms"] = 5
        params["sick_reduction"] = 20  # Higher consumption reduction when sick
    elif covid_policy == "VAX":  # Vaccination
        params["p_vax"] = 0.8  # Vaccination rate

    return params


def run_basic_simulation(params, output_dir="results"):
    """
    Run a basic simulation with the given parameters.

    Args:
        params: Simulation parameters
        output_dir: Directory to save results

    Returns:
        tuple: (model_results, save_folder)
    """
    print(
        f"Running simulation: {params['settings']} scenario with {params['covid_settings']} COVID policy"
    )
    print(
        f"Agents: {params['c_agents']} consumers, {params['csf_agents']} consumer firms, {params['cpf_agents']} capital firms"
    )
    print(f"Steps: {params['steps']} months")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Run the simulation
    results = single_run(params, parent_folder=output_dir, make_stats=True)

    return results


def create_basic_plots(results, save_folder):
    """
    Create basic plots from simulation results.

    Args:
        results: Simulation results
        save_folder: Directory to save plots
    """
    if not hasattr(results, "variables") or not hasattr(results.variables, "EconModel"):
        print("Warning: Results don't contain expected variables for plotting")
        return

    data = results.variables.EconModel

    # Create figures directory
    plots_dir = os.path.join(save_folder, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    # Plot 1: GDP over time
    plt.figure(figsize=(10, 6))
    if "GDP" in data:
        gdp_data = data["GDP"].values
        if len(gdp_data) > 0 and hasattr(gdp_data[0], "__len__"):
            gdp_series = [x for x in gdp_data if x is not None]
            if gdp_series:
                plt.plot(gdp_series)
                plt.title("GDP Over Time")
                plt.xlabel("Time (months)")
                plt.ylabel("GDP")
                plt.grid(True)
                plt.savefig(os.path.join(plots_dir, "gdp_over_time.png"))
                plt.close()

    # Plot 2: Unemployment rate
    plt.figure(figsize=(10, 6))
    if "UnemploymentRate" in data:
        unemployment_data = data["UnemploymentRate"].values
        unemployment_series = [
            x for x in unemployment_data if x is not None and str(x) != "nan"
        ]
        if unemployment_series:
            plt.plot(unemployment_series)
            plt.title("Unemployment Rate Over Time")
            plt.xlabel("Time (months)")
            plt.ylabel("Unemployment Rate")
            plt.grid(True)
            plt.savefig(os.path.join(plots_dir, "unemployment_over_time.png"))
            plt.close()

    # Plot 3: Climate variables (if available)
    if "ClimateTemperature" in data:
        plt.figure(figsize=(10, 6))
        temp_data = data["ClimateTemperature"].values
        temp_series = [x for x in temp_data if x is not None]
        if temp_series:
            plt.plot(temp_series)
            plt.title("Temperature Anomaly Over Time")
            plt.xlabel("Time (months)")
            plt.ylabel("Temperature Anomaly (°C)")
            plt.grid(True)
            plt.savefig(os.path.join(plots_dir, "temperature_over_time.png"))
            plt.close()

    print(f"Basic plots saved to {plots_dir}")


def analyze_results(results, save_folder):
    """
    Perform basic analysis of simulation results.

    Args:
        results: Simulation results
        save_folder: Directory to save analysis
    """
    if not hasattr(results, "variables") or not hasattr(results.variables, "EconModel"):
        print("Warning: Results don't contain expected variables for analysis")
        return

    data = results.variables.EconModel
    analysis_file = os.path.join(save_folder, "basic_analysis.txt")

    with open(analysis_file, "w") as f:
        f.write("Basic Simulation Analysis\n")
        f.write("=" * 30 + "\n\n")

        # Analyze key economic indicators
        for var_name in ["GDP", "UnemploymentRate", "InflationRate", "Consumption"]:
            if var_name in data:
                var_data = data[var_name].values
                clean_data = [x for x in var_data if x is not None and str(x) != "nan"]

                if clean_data:
                    f.write(f"{var_name}:\n")
                    f.write(f"  Mean: {np.mean(clean_data):.4f}\n")
                    f.write(f"  Std:  {np.std(clean_data):.4f}\n")
                    f.write(f"  Min:  {np.min(clean_data):.4f}\n")
                    f.write(f"  Max:  {np.max(clean_data):.4f}\n\n")

        # Analyze climate variables if available
        for var_name in ["ClimateTemperature", "ClimateC02Concentration"]:
            if var_name in data:
                var_data = data[var_name].values
                clean_data = [x for x in var_data if x is not None]

                if clean_data:
                    f.write(f"{var_name}:\n")
                    f.write(f"  Final value: {clean_data[-1]:.4f}\n")
                    f.write(f"  Change: {clean_data[-1] - clean_data[0]:.4f}\n\n")

    print(f"Basic analysis saved to {analysis_file}")


def main():
    """Main function to run the basic simulation example."""
    parser = argparse.ArgumentParser(description="Run a basic CliMaPan-Lab simulation")
    parser.add_argument(
        "--scenario",
        choices=["BAU", "CT", "CTR"],
        default="BAU",
        help="Economic scenario to run",
    )
    parser.add_argument(
        "--covid",
        choices=["BAU", "DIST", "LOCK", "VAX"],
        default="BAU",
        help="COVID policy to apply",
    )
    parser.add_argument(
        "--steps", type=int, default=120, help="Number of simulation steps (months)"
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=0.1,
        help="Agent scale factor (0.1 for quick testing, 1.0 for full simulation)",
    )
    parser.add_argument(
        "--output", default="results", help="Output directory for results"
    )
    parser.add_argument("--plots", action="store_true", help="Generate basic plots")
    parser.add_argument(
        "--analysis", action="store_true", help="Perform basic analysis"
    )

    args = parser.parse_args()

    # Set up the scenario
    params = setup_basic_scenario(
        scenario=args.scenario,
        covid_policy=args.covid,
        steps=args.steps,
        agents_scale=args.scale,
    )

    # Run the simulation
    try:
        results = run_basic_simulation(params, args.output)
        print("Simulation completed successfully!")

        # Find the save folder (created by single_run)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_folder = None

        # Look for the results folder
        for item in os.listdir(args.output):
            if item.startswith(f"results_{args.scenario}_{args.covid}"):
                save_folder = os.path.join(args.output, item)
                break

        if save_folder and os.path.exists(save_folder):
            print(f"Results saved to: {save_folder}")

            # Generate plots if requested
            if args.plots:
                create_basic_plots(results, save_folder)

            # Perform analysis if requested
            if args.analysis:
                analyze_results(results, save_folder)
        else:
            print("Warning: Could not locate results folder for post-processing")

    except Exception as e:
        print(f"Simulation failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
