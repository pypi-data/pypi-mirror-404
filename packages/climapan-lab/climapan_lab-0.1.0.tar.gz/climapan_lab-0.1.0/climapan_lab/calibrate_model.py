#!/usr/bin/env python3
"""
Model Calibration Script for CliMaPan-Lab using Bayesian Optimization

Calibrates model parameters against Germany9122.csv using AUTOCORRELATION-BASED matching.
This matches the dynamics/patterns of time series rather than absolute values.
"""

import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from climapan_lab.base_params import economic_params as parameters
from climapan_lab.src.models import EconModel

# =============================================================================
# Load Target Data
# =============================================================================


def load_target_data(filepath: str = None) -> pd.DataFrame:
    """Load Germany9122.csv target data."""
    if filepath is None:
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data", "Germany9122.csv"
        )

    df = pd.read_csv(filepath)
    df = df.ffill().bfill()
    print(f"Loaded target data: {len(df)} years")
    print(f"Columns: {list(df.columns)}")
    return df


# =============================================================================
# Autocorrelation Functions
# =============================================================================


def compute_autocorrelation(series: np.ndarray, max_lag: int = 5) -> np.ndarray:
    """
    Compute autocorrelation for a time series up to max_lag.

    Args:
        series: 1D array of time series values
        max_lag: Maximum lag to compute

    Returns:
        Array of autocorrelation values for lags 1 to max_lag
    """
    series = np.asarray(series, dtype=float)
    n = len(series)

    if n < max_lag + 2:
        return np.zeros(max_lag)

    # Normalize
    mean = np.mean(series)
    var = np.var(series)

    if var < 1e-10:
        return np.zeros(max_lag)

    normalized = (series - mean) / np.sqrt(var)

    acf = []
    for lag in range(1, max_lag + 1):
        if lag < n:
            acf.append(np.mean(normalized[:-lag] * normalized[lag:]))
        else:
            acf.append(0)

    return np.array(acf)


def compute_statistics(series: np.ndarray) -> Dict[str, float]:
    """
    Compute key statistics of a time series.

    Args:
        series: 1D array of time series values

    Returns:
        Dictionary with mean, std, cv, trend, and autocorrelations
    """
    series = np.asarray(series, dtype=float)
    n = len(series)

    if n < 3:
        return {"mean": 0, "std": 0, "cv": 0, "trend": 0, "acf": np.zeros(5)}

    mean = np.mean(series)
    std = np.std(series)
    cv = std / (abs(mean) + 1e-10)  # Coefficient of variation

    # Trend (normalized slope)
    x = np.arange(n)
    if std > 1e-10:
        slope = np.polyfit(x, series, 1)[0]
        trend = slope / (abs(mean) + 1e-10)  # Normalized trend
    else:
        trend = 0

    acf = compute_autocorrelation(series, max_lag=5)

    return {"mean": mean, "std": std, "cv": cv, "trend": trend, "acf": acf}


# =============================================================================
# Parameter Space - ALL calibratable parameters from params.py
# =============================================================================

PARAM_SPACE = {
    # Consumer parameters
    "unemploymentDole": (50, 500),
    "owner_endownment": (3000, 12000),
    "wageAdjustmentRate": (0.0001, 0.01),
    "subsistenceLevelOfConsumption": (20, 80),
    "worker_additional_consumption": (1, 30),
    "owner_additional_consumption": (50, 150),
    "consumption_growth": (0.0005, 0.005),
    "consumption_var": (0.02, 0.15),
    "ownerProportionFromProfits": (0.4, 0.9),
    "energyOwnerProportionFromProfits": (0.5, 0.95),
    # Bank parameters
    "bankResInit": (1e9, 1e10),
    "bankIL": (0.05, 0.2),
    # Firm parameters
    "depreciationRate": (0.1, 0.4),
    "forecast_discount_factor": (0.7, 0.99),
    "mark_up_factor": (0.3, 0.8),
    "mark_up_alpha": (0.3, 0.8),
    "capital_growth_rate": (0.01, 0.1),
    "reserve_ratio": (0.1, 0.5),
    # Production parameters
    "rho_labour": (40, 120),
    "rho_energy": (60, 200),
    "rho_labour_K": (30, 100),
    "rho_energy_K": (80, 300),
    # Energy sector
    "energy_price_growth": (0.002, 0.02),
    "base_green_energy_price": (30, 100),
    "fossil_fuel_price": (0.5, 5),
    "fossil_fuel_price_growth_rate": (0.002, 0.02),
    # Climate parameters
    "climateSensitivity": (3, 10),
    "climateZetaBrown": (0.2, 0.8),
}


# =============================================================================
# Simulation Runner
# =============================================================================


def run_simulation(params: dict, n_years: int = 10) -> dict:
    """Run simulation and return yearly aggregated metrics."""
    steps = n_years * 365

    sim_params = parameters.copy()
    sim_params.update(params)
    sim_params["steps"] = steps
    sim_params["show_progress"] = False
    sim_params["climateModuleFlag"] = True

    model = EconModel(sim_params)
    model.setup()

    monthly_gdp = []
    monthly_unemployment = []
    monthly_investment = []
    monthly_co2 = []

    for step in range(steps):
        model.step()
        model.update()

        if hasattr(model, "GDP") and model.GDP > 0:
            monthly_gdp.append(model.GDP)
        if hasattr(model, "unemploymentRate"):
            monthly_unemployment.append(model.unemploymentRate * 100)
        if hasattr(model, "ksale"):
            monthly_investment.append(model.ksale)
        if hasattr(model, "climateModule") and hasattr(model.climateModule, "EM"):
            monthly_co2.append(
                model.climateModule.EM[-1] if len(model.climateModule.EM) > 0 else 0
            )

    def yearly_aggregate(monthly_data: list, n_years: int) -> np.ndarray:
        if not monthly_data:
            return np.zeros(n_years)
        arr = np.array(monthly_data)
        n_months = len(arr)
        years = []
        for y in range(n_years):
            start = y * 12
            end = min((y + 1) * 12, n_months)
            if start < n_months:
                years.append(np.mean(arr[start:end]))
            else:
                years.append(0)
        return np.array(years)

    return {
        "GDP": yearly_aggregate(monthly_gdp, n_years),
        "UnemploymentRate": yearly_aggregate(monthly_unemployment, n_years),
        "Investment": yearly_aggregate(monthly_investment, n_years),
        "Climate C02": yearly_aggregate(monthly_co2, n_years),
    }


# =============================================================================
# Autocorrelation-Based Objective Function
# =============================================================================


def objective_function(
    params: dict, target_data: pd.DataFrame, n_years: int = 10
) -> float:
    """
    Compute autocorrelation-based distance between simulation and target.

    Matches:
    1. Autocorrelation structure (ACF lags 1-5)
    2. Coefficient of variation (relative variability)
    3. Trend direction and magnitude

    Args:
        params: Model parameters to evaluate
        target_data: Target DataFrame
        n_years: Number of years to simulate

    Returns:
        Combined distance score (lower is better)
    """
    try:
        sim_results = run_simulation(params, n_years)
        total_distance = 0.0
        n_metrics = 0

        for metric in ["GDP", "UnemploymentRate", "Investment", "Climate C02"]:
            if metric not in target_data.columns:
                continue

            target = target_data[metric].values[:n_years]
            sim = sim_results.get(metric, np.zeros(n_years))[:n_years]

            # Handle NaN
            valid_mask = ~np.isnan(target)
            if not np.any(valid_mask):
                continue

            target_valid = target[valid_mask]
            sim_valid = (
                sim[valid_mask] if len(sim) >= len(target) else sim[: len(target_valid)]
            )

            if len(sim_valid) < 3 or len(target_valid) < 3:
                continue

            # Compute statistics for both
            target_stats = compute_statistics(target_valid)
            sim_stats = compute_statistics(sim_valid)

            # 1. ACF distance (most important - matches dynamics)
            acf_distance = np.mean((target_stats["acf"] - sim_stats["acf"]) ** 2)

            # 2. CV distance (matches relative variability)
            cv_distance = (target_stats["cv"] - sim_stats["cv"]) ** 2

            # 3. Trend distance (matches direction of change)
            trend_distance = (target_stats["trend"] - sim_stats["trend"]) ** 2

            # Combined distance (weighted)
            metric_distance = (
                0.6 * acf_distance + 0.25 * cv_distance + 0.15 * trend_distance
            )

            total_distance += metric_distance
            n_metrics += 1

        return total_distance / max(n_metrics, 1)

    except Exception as e:
        print(f"Error in objective: {e}")
        return float("inf")


# =============================================================================
# Bayesian Optimization
# =============================================================================


def bayesian_optimization(
    target_data: pd.DataFrame,
    n_calls: int = 30,
    n_years: int = 5,
    n_initial: int = 10,
    seed: int = 42,
) -> list:
    """Perform Bayesian optimization for model calibration."""
    np.random.seed(seed)

    print(f"\n{'='*60}")
    print(f"Autocorrelation-Based Bayesian Calibration")
    print(f"  Total calls: {n_calls}")
    print(f"  Initial random samples: {n_initial}")
    print(f"  Years per trial: {n_years}")
    print(f"  Parameters: {len(PARAM_SPACE)}")
    print(f"  Objective: ACF + CV + Trend matching")
    print(f"{'='*60}\n")

    param_names = list(PARAM_SPACE.keys())

    X_observed = []
    y_observed = []
    results = []

    start_time = time.time()

    def sample_random() -> dict:
        params = {}
        for name, (low, high) in PARAM_SPACE.items():
            if low > 0 and high / low > 100:
                params[name] = np.exp(np.random.uniform(np.log(low), np.log(high)))
            else:
                params[name] = np.random.uniform(low, high)
        return params

    def params_to_vector(params: dict) -> np.ndarray:
        vec = []
        for name, (low, high) in PARAM_SPACE.items():
            val = params.get(name, (low + high) / 2)
            normalized = (val - low) / (high - low + 1e-8)
            vec.append(normalized)
        return np.array(vec)

    def vector_to_params(vec: np.ndarray) -> dict:
        params = {}
        for i, (name, (low, high)) in enumerate(PARAM_SPACE.items()):
            params[name] = low + vec[i] * (high - low)
        return params

    def acquisition_function(x: np.ndarray) -> float:
        if len(X_observed) < 2:
            return np.random.random()

        X = np.array(X_observed)
        y = np.array(y_observed)

        distances = np.linalg.norm(X - x, axis=1)
        weights = 1 / (distances + 0.01)
        weights /= weights.sum()

        mu = np.dot(weights, y)
        min_dist = np.min(distances)
        sigma = min_dist * np.std(y) if np.std(y) > 0 else 0.1

        return mu - 1.5 * sigma

    def suggest_next() -> dict:
        best_acq = float("inf")
        best_x = None

        for _ in range(100):
            x = np.random.random(len(param_names))
            acq = acquisition_function(x)
            if acq < best_acq:
                best_acq = acq
                best_x = x

        return vector_to_params(best_x)

    for i in range(n_calls):
        if i < n_initial:
            params = sample_random()
            phase = "random"
        else:
            params = suggest_next()
            phase = "bayesian"

        trial_start = time.time()
        objective = objective_function(params, target_data, n_years)
        trial_time = time.time() - trial_start

        X_observed.append(params_to_vector(params))
        y_observed.append(objective if objective != float("inf") else 1e6)

        results.append(
            {
                "params": params,
                "objective": objective,
                "time": trial_time,
                "phase": phase,
            }
        )

        best_obj = min(r["objective"] for r in results)
        print(
            f"[{i+1}/{n_calls}] ({phase}) Score: {objective:.6f} | Best: {best_obj:.6f} | {trial_time:.1f}s"
        )

    total_time = time.time() - start_time

    results.sort(key=lambda x: x["objective"])

    print(f"\n{'='*60}")
    print(f"Optimization Complete!")
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Best Score: {results[0]['objective']:.6f}")
    print(f"{'='*60}\n")

    return results


def save_results(results: list, output_path: str):
    """Save calibration results to JSON."""
    serializable_results = []
    for r in results[:10]:
        serializable_results.append(
            {
                "params": {k: float(v) for k, v in r["params"].items()},
                "objective": (
                    float(r["objective"]) if r["objective"] != float("inf") else 1e10
                ),
                "time": float(r["time"]),
                "phase": r.get("phase", "unknown"),
            }
        )

    with open(output_path, "w") as f:
        json.dump(serializable_results, f, indent=2)

    print(f"Results saved to: {output_path}")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    target_data = load_target_data()

    # Compute target statistics for reference
    print("\nTarget Data Statistics:")
    print("-" * 40)
    for col in ["GDP", "UnemploymentRate", "Investment", "Climate C02"]:
        if col in target_data.columns:
            stats = compute_statistics(target_data[col].values)
            print(f"{col}:")
            print(f"  CV: {stats['cv']:.4f}")
            print(f"  Trend: {stats['trend']:.4f}")
            print(f"  ACF[1-3]: {stats['acf'][:3]}")

    results = bayesian_optimization(
        target_data=target_data,
        n_calls=20,  # 20 trials * 4 mins = ~80 mins
        n_years=30,  # Match full dataset length
        n_initial=5,  # Fewer random samples to save time
        seed=42,
    )

    print("\n" + "=" * 60)
    print("Best Parameters Found:")
    print("=" * 60)
    for k, v in sorted(results[0]["params"].items()):
        print(f"  {k}: {v:.6f}")

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "calibration_results.json"
    )
    save_results(results, output_path)

    best_params_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "optimized_params.py"
    )
    with open(best_params_path, "w") as f:
        f.write(
            "# Optimized parameters from Autocorrelation-Based Bayesian calibration\n"
        )
        f.write("# Matches: ACF structure, CV (variability), and Trend\n\n")
        f.write("optimized_params = {\n")
        for k, v in sorted(results[0]["params"].items()):
            f.write(f"    '{k}': {v},\n")
        f.write("}\n")
    print(f"Best params saved to: {best_params_path}")
