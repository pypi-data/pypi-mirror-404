#!/usr/bin/env python3
"""
CliMaPan-Lab Simple Example
A basic example showing how to run a simulation with CliMaPan-Lab.
"""

import os
import sys

# Import CliMaPan-Lab components
try:
    from ..base_params import economic_params
    from ..model import EconModel
except ImportError:
    # Fallback for when running as standalone script
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from climapan_lab.base_params import economic_params
    from climapan_lab.model import EconModel


def run_simple_simulation():
    """Run a simple economic simulation."""

    print("CliMaPan-Lab Simple Example")
    print("=" * 50)

    # Create a copy of default parameters
    sim_params = economic_params.copy()

    # Modify some parameters for a simple run
    sim_params["settings"] = "BAU"  # Business as usual scenario
    sim_params["covid_settings"] = None  # No COVID
    sim_params["climateModuleFlag"] = False  # Disable climate for simplicity
    sim_params["steps"] = 120  # Run for 10 years (120 months)

    print(f"Running simulation with settings: {sim_params['settings']}")
    print(
        f"Climate module: {'Enabled' if sim_params['climateModuleFlag'] else 'Disabled'}"
    )
    print(f"COVID settings: {sim_params['covid_settings'] or 'None'}")
    print(f"Simulation steps: {sim_params['steps']}")
    print()

    # Create and run the model
    print("Creating economic model...")
    model = EconModel(sim_params)

    print("Running simulation...")
    results = model.run()

    print("Simulation completed!")
    print()

    # Display some basic results
    print("Basic Results Summary:")
    print("-" * 30)

    # Access results
    if hasattr(results, "variables") and hasattr(results.variables, "EconModel"):
        df = results.variables.EconModel

        # Show some key metrics from the last few steps
        last_steps = 5
        print(f"Final {last_steps} steps of simulation:")

        key_vars = ["GDP", "UnemploymentRate", "InflationRate", "TotalTaxes"]
        for var in key_vars:
            if var in df.columns:
                values = df[var].tail(last_steps)
                avg_value = values.mean() if len(values) > 0 else "N/A"
                print(f"  Average {var}: {avg_value}")

        print(f"\nTotal simulation steps completed: {len(df)}")
        print(f"Available variables: {len(df.columns)}")

    else:
        print("Results format not recognized")

    print("\nSimulation completed successfully!")
    return results


def main():
    """Main function for console script entry point."""
    return run_simple_simulation()


if __name__ == "__main__":
    run_simple_simulation()
