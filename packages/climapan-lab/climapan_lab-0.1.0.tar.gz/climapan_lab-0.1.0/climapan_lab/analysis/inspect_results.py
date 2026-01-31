#!/usr/bin/env python3
"""
Inspect the structure of simulation results.
"""

import argparse
import pickle
import sys


def inspect_results(results_path):
    """Inspect the structure of saved results."""
    print(f"Loading results from {results_path}")

    with open(results_path, "rb") as f:
        results = pickle.load(f)

    print("Results type:", type(results))
    print(
        "Results attributes:",
        [attr for attr in dir(results) if not attr.startswith("_")],
    )

    if hasattr(results, "variables"):
        print("\nVariables type:", type(results.variables))
        print(
            "Variables attributes:",
            [attr for attr in dir(results.variables) if not attr.startswith("_")],
        )

        if hasattr(results.variables, "data"):
            print("\nData type:", type(results.variables.data))
            if isinstance(results.variables.data, dict):
                print("Data keys:", list(results.variables.data.keys()))
                # Show a sample of the data
                for key, value in list(results.variables.data.items())[:3]:
                    print(
                        f'  {key}: {type(value)} - length: {len(value) if hasattr(value, "__len__") else "N/A"}'
                    )
                    if hasattr(value, "__len__") and len(value) > 0:
                        print(
                            f"    Sample values: {value[:3] if len(value) >= 3 else value}"
                        )
            else:
                print("Data content type:", type(results.variables.data))
                print("Data content:", results.variables.data)

    if hasattr(results, "parameters"):
        print("\nParameters available:", hasattr(results, "parameters"))
        if hasattr(results, "parameters"):
            print("Parameters type:", type(results.parameters))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect simulation results structure")
    parser.add_argument("results_path", help="Path to the results pickle file")
    args = parser.parse_args()

    inspect_results(args.results_path)
