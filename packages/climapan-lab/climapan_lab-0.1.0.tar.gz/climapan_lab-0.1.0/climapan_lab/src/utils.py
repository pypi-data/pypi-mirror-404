"""
CliMaPan-Lab: Climate-Pandemic Economic Modeling Laboratory
Utility Functions and Plotting

This module contains utility functions for data processing, statistical calculations,
and visualization of simulation results.
"""

import itertools
import json
import math
import os
import random
import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from scipy.interpolate import griddata
from statsmodels.tsa.filters.hp_filter import hpfilter

from .params import parameters


def listToArray(x):
    try:
        return np.array(x)
    except ValueError:
        return np.array(x, dtype=object)


def leap_year(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    return False


def days_in_month(month, year):
    if month in {1, 3, 5, 7, 8, 10, 12}:
        return 31
    if month == 2:
        if leap_year(year):
            return 29
        return 28
    return 30


def _merge_edgelist(p1, p2, mapping, offset=0):
    """Helper function to convert lists to arrays and optionally map arrays"""
    p1 = np.array(p1, dtype=np.int32)
    p2 = np.array(p2, dtype=np.int32)
    if mapping is not None:
        mapping = np.array(mapping, dtype=np.int32)
        p1 = mapping[p1] - offset
        p2 = mapping[p2] - offset
    output = dict(p1=p1, p2=p2)
    return output


def gini(x, eps=1e-8):
    """
    Calculate Gini coefficient efficiently (O(N log N)).

    Args:
        x (array-like): Array of values (income/consumption)
        eps (float): Small value to avoid division by zero

    Returns:
        float: Gini coefficient
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return 0.0

    # Filter NaNs if any, though model shouldn't produce them ideally
    x = x[~np.isnan(x)]
    if x.size == 0:
        return 0.0

    # Sort data for efficient calculation
    sorted_x = np.sort(x)
    n = x.size

    # Gini formula using sorted values:
    # G = (2 * sum(i * x_i) / (n * sum(x_i))) - (n + 1) / n
    # where i is 1-based index (1 to n)

    index = np.arange(1, n + 1)
    return (2 * np.sum(index * sorted_x)) / (n * np.sum(sorted_x) + eps) - (n + 1) / n


def plotConsumersSummary(results, saveFolder):
    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax1 = plt.subplot2grid((6, 2), (5, 0))
    ax1.margins(0.1)
    ax1.plot(
        [
            (
                results.variables.EconModel["Gini"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Gini"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
            and not np.isnan(
                results.variables.EconModel["Gini"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
        ]
    )
    ax1.set_ylabel("Gini")
    ax1.set_xlabel("Year")

    ax1 = plt.subplot2grid((6, 2), (5, 1))
    ax1.margins(0.1)
    ax1.hist(
        np.array([np.sum(i) for i in results.variables.EconModel["Wage"]])
        + results.variables.EconModel["Owners Income"],
        1000,
    )
    ax1.set_ylabel("Density")
    ax1.set_xlabel("Wage")

    ax1 = plt.subplot2grid((6, 2), (4, 0))
    ax1.margins(0.1)
    ax1.plot(
        [
            (
                results.variables.EconModel["UnemploymentRate"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            * 100
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["UnemploymentRate"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
            and not np.isnan(
                results.variables.EconModel["UnemploymentRate"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
        ]
    )
    ax1.set_ylabel("Unemployment Rate (%)")
    ax1.set_xlabel("Year")

    ax2 = plt.subplot2grid((6, 2), (1, 0))
    ax2.margins(0.1)
    # ax2.plot([(results.variables.EconModel['Available Income'][results.variables.EconModel['BankDataWriter'].keys()[i]].sum()) for i in range(50,len(results.variables.EconModel['BankDataWriter']))], label = "Available Income")
    ax2.plot(
        [
            np.sum(
                results.variables.EconModel["UnemplDole"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["UnemplDole"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Unempl Dole",
    )
    ax2.plot(
        [
            np.sum(
                results.variables.EconModel["Owners Income"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Owners Income"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Owners Income",
    )
    ax2.plot(
        [
            np.sum(
                results.variables.EconModel["Wage"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Wage"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Wage",
    )
    ax2.set_ylabel("Available Income")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax2 = plt.subplot2grid((6, 2), (1, 1))
    ax2.margins(0.1)
    data = []
    # data.append([(results.variables.EconModel['Available Income'][results.variables.EconModel['BankDataWriter'].keys()[i]].sum()) for i in range(50,len(results.variables.EconModel['BankDataWriter']))])
    data.append(
        [
            np.sum(
                np.array(
                    (
                        results.variables.EconModel["UnemplDole"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                    )
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["UnemplDole"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            np.sum(
                np.array(
                    (
                        results.variables.EconModel["Owners Income"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                    )
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Owners Income"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            np.sum(
                np.sum(
                    np.array(
                        (
                            results.variables.EconModel["Wage"][
                                results.variables.EconModel["BankDataWriter"].keys()[i]
                            ]
                        )
                    )
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Wage"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.boxplot(data)
    ax2.set_ylabel("Available Income")

    ax2 = plt.subplot2grid((6, 2), (2, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["Wage"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Wage"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Wage",
    )
    ax2.set_ylabel("Wage")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax2 = plt.subplot2grid((6, 2), (2, 1))
    ax2.margins(0.1)
    data = []
    data.append(
        [
            np.sum(
                np.sum(
                    np.array(
                        (
                            results.variables.EconModel["Wage"][
                                results.variables.EconModel["BankDataWriter"].keys()[i]
                            ]
                        )
                    )
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Wage"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.boxplot(data)
    ax2.set_ylabel("Wage")

    ax3 = plt.subplot2grid((6, 2), (3, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["New Credit Asked"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["New Credit Asked"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="New Credit Asked",
    )
    ax3.plot(
        [
            (
                results.variables.EconModel["Obtained Credit"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Obtained Credit"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Obtained Credit",
    )
    ax3.set_ylabel("New Credit Asked vs Obtained Credit")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot2grid((6, 2), (3, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["New Credit Asked"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["New Credit Asked"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["Obtained Credit"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Obtained Credit"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("New Credit Asked vs Obtained Credit")

    ax5 = plt.subplot2grid((6, 2), (0, 0))
    ax5.margins(0.1)
    ax5.plot(
        [
            (
                results.variables.EconModel["Wealth"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Wealth"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax5.set_ylabel("Wealth")
    ax5.set_xlabel("Year")

    ax3 = plt.subplot2grid((6, 2), (0, 1))
    ax5.margins(0.1)
    ax5.boxplot(
        [
            (
                results.variables.EconModel["Wealth"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Wealth"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax5.set_ylabel("Wealth")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/ConsumerSummaryPlot.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/ConsumerSummaryPlot.png")


def plotConsumptionInflationSummary(results, saveFolder):
    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax5 = plt.subplot2grid((5, 2), (0, 0))
    ax5.margins(0.1)
    ax5.plot(
        [
            (
                results.variables.EconModel["Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "capitalists"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Capitalists",
    )
    ax5.plot(
        [
            (
                results.variables.EconModel["Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "green_energy_owners"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Green Energy Owners",
    )
    ax5.plot(
        [
            (
                results.variables.EconModel["Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "brown_energy_owners"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Brown Energy Owners",
    )
    ax5.plot(
        [
            (
                results.variables.EconModel["Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "workers"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Workers",
    )
    ax5.set_ylabel("Consumption")
    ax5.set_xlabel("Year")
    ax5.legend()

    ax5 = plt.subplot2grid((5, 2), (0, 1))
    ax5.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "capitalists"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "green_energy_owners"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "brown_energy_owners"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "workers"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax5.boxplot(data)
    ax5.set_ylabel("Consumption")

    ax1 = plt.subplot2grid((5, 2), (1, 0))
    ax1.margins(0.1)
    ax1.plot(
        [
            (
                results.variables.EconModel["Gini Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Gini Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
            and not np.isnan(
                results.variables.EconModel["Gini Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
        ]
    )
    ax1.set_ylabel("Gini Consumption")
    ax1.set_xlabel("Year")

    ax5 = plt.subplot2grid((5, 2), (2, 0))
    ax5.margins(0.1)
    ax5.plot(
        [
            (
                results.variables.EconModel["Desired Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "capitalists"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Desired Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Capitalists",
    )
    ax5.plot(
        [
            (
                results.variables.EconModel["Desired Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "green_energy_owners"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Desired Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Green Energy Owners",
    )
    ax5.plot(
        [
            (
                results.variables.EconModel["Desired Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "brown_energy_owners"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Desired Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Brown Energy Owners",
    )
    ax5.plot(
        [
            (
                results.variables.EconModel["Desired Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "workers"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Desired Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Workers",
    )
    ax5.set_ylabel("Desired Consumption")
    ax5.set_xlabel("Year")
    ax5.legend()

    ax5 = plt.subplot2grid((5, 2), (2, 1))
    ax5.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Desired Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "capitalists"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Desired Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["Desired Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "green_energy_owners"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Desired Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["Desired Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "brown_energy_owners"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Desired Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["Desired Consumption"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][
                    np.argwhere(
                        results.variables.EconModel["Consumer Type"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                        == "workers"
                    )
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Desired Consumption"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax5.boxplot(data)
    ax5.set_ylabel("Desired Consumption")

    ax5 = plt.subplot2grid((5, 2), (3, 0))
    ax5.margins(0.1)
    ax5.plot(
        [
            (
                results.variables.EconModel["Expected Inflation Rate"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Expected Inflation Rate"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="expectedInflationRate",
    )
    ax5.set_ylabel("expectedInflationRate")
    ax5.set_xlabel("Year")
    ax5.legend()

    ax5 = plt.subplot2grid((5, 2), (3, 1))
    ax5.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Expected Inflation Rate"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Expected Inflation Rate"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax5.boxplot(data)
    ax5.set_ylabel("expectedInflationRate")

    ax5 = plt.subplot2grid((5, 2), (4, 0))
    ax5.margins(0.1)
    ax5.plot(
        [
            (
                results.variables.EconModel["Inflation Rate"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Inflation Rate"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="inflationRate",
    )
    ax5.set_ylabel("inflationRate")
    ax5.set_xlabel("Year")
    ax5.legend()

    ax5 = plt.subplot2grid((5, 2), (4, 1))
    ax5.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Inflation Rate"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Inflation Rate"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax5.boxplot(data)
    ax5.set_ylabel("inflationRate")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/ConsumptionInflationSummary.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/ConsumptionInflationSummary.png")


def plotBankSummary(results, saveFolder, eps=1e-8):
    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax1 = plt.subplot2grid((9, 2), (0, 0))
    ax1.margins(0.1)
    ax1.plot(
        [
            (
                results.variables.EconModel["Bank totalLoanSupply"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank totalLoanSupply"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Total Loan Supply",
    )
    ax1.plot(
        [
            (
                results.variables.EconModel["Bank Loan Demands"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank Loan Demands"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Loan Demand",
    )
    ax1.set_ylabel("Bank Total Loan Supply vs Loan Demand")
    ax1.set_xlabel("Year")
    ax1.legend()

    ax1 = plt.subplot2grid((9, 2), (1, 0))
    ax1.margins(0.1)
    ax1.plot(
        [
            (
                results.variables.EconModel["Bank iL"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
                * 100
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank iL"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Bank Debt to Equity",
    )
    ax1.plot(
        [
            1.5
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank iL"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Bank Debt to Equity")
    ax1.set_xlabel("Year")

    ax3 = plt.subplot2grid((9, 2), (7, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Bank iL"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
                * 100
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank iL"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Bank Debt to Equity")

    ax2 = plt.subplot2grid((9, 2), (2, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["Bank Equity"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank Equity"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Bank Equity")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax3 = plt.subplot2grid((9, 2), (2, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Bank Equity"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank Equity"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Bank Equity")

    ax2 = plt.subplot2grid((9, 2), (3, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["Bank Deposits"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank Deposits"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Bank Deposits")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax3 = plt.subplot2grid((9, 2), (3, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Bank Deposits"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank Deposits"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Bank Deposits")

    ax2 = plt.subplot2grid((9, 2), (4, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["Consumer iL"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumer iL"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Consumer iL",
    )
    for j in range(len(results.variables.EconModel["CS iL"][0])):
        ax2.plot(
            [
                (
                    results.variables.EconModel["CS iL"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS iL"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ],
            label=f"CS {j} iL",
        )
    for j in range(len(results.variables.EconModel["CP iL"][0])):
        ax2.plot(
            [
                (
                    results.variables.EconModel["CP iL"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP iL"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ],
            label=f"CP {j} iL",
        )
    ax2.set_ylabel("iL")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax3 = plt.subplot2grid((9, 2), (4, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Consumer iL"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumer iL"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    for j in range(len(results.variables.EconModel["CS iL"][0])):
        data.append(
            [
                (
                    results.variables.EconModel["CS iL"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS iL"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    for j in range(len(results.variables.EconModel["CP iL"][0])):
        data.append(
            [
                (
                    results.variables.EconModel["CP iL"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP iL"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    ax3.boxplot(data)
    ax3.set_ylabel("iL")

    ax2 = plt.subplot2grid((9, 2), (5, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["Consumer iH"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumer iH"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Consumer iH",
    )
    for j in range(len(results.variables.EconModel["CS iF"][0])):
        ax2.plot(
            [
                (
                    results.variables.EconModel["CS iF"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS iF"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ],
            label=f"CS {j} iF",
        )
    for j in range(len(results.variables.EconModel["CP iF"][0])):
        ax2.plot(
            [
                (
                    results.variables.EconModel["CP iF"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP iF"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ],
            label=f"CP {j} iF",
        )
    ax2.set_ylabel("iF/iH")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax3 = plt.subplot2grid((9, 2), (5, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Consumer iH"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Consumer iH"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    for j in range(len(results.variables.EconModel["CS iF"][0])):
        data.append(
            [
                (
                    results.variables.EconModel["CS iF"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS iF"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    for j in range(len(results.variables.EconModel["CP iF"][0])):
        data.append(
            [
                (
                    results.variables.EconModel["CP iF"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP iF"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    ax3.boxplot(data)
    ax3.set_ylabel("iF/iH")

    ax2 = plt.subplot2grid((9, 2), (6, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["CS Num Bankrupt"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Num Bankrupt"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="CS Num Bankrupt",
    )
    ax2.plot(
        [
            (
                results.variables.EconModel["CP Num Bankrupt"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Num Bankrupt"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="CP Num Bankrupt",
    )
    ax2.set_ylabel("Number of Bankrupt Goods Firms")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax3 = plt.subplot2grid((9, 2), (6, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["CS Num Bankrupt"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Num Bankrupt"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["CP Num Bankrupt"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Num Bankrupt"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Number of Bankrupt Goods Firms")

    ax2 = plt.subplot2grid((9, 2), (7, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["Bank Loan Over Equity"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank Loan Over Equity"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Bank Leverage",
    )
    ax2.plot(
        [
            0.5
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank Loan Over Equity"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Bank Leverage")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax3 = plt.subplot2grid((9, 2), (7, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Bank Loan Over Equity"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Bank Loan Over Equity"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Bank Leverage")

    ax2 = plt.subplot2grid((9, 2), (8, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["GDP"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
                - results.variables.EconModel["GDP"][
                    results.variables.EconModel["BankDataWriter"].keys()[i - 1]
                ].sum()
            )
            * 100
            / (
                results.variables.EconModel["GDP"][
                    results.variables.EconModel["BankDataWriter"].keys()[i - 1]
                ].sum()
                + eps
            )
            for i in range(51, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["GDP"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
            and results.variables.EconModel["GDP"][
                results.variables.EconModel["BankDataWriter"].keys()[i - 1]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("GDP Increase")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax3 = plt.subplot2grid((9, 2), (8, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["GDP"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
                - results.variables.EconModel["GDP"][
                    results.variables.EconModel["BankDataWriter"].keys()[i - 1]
                ].sum()
            )
            * 100
            / (
                results.variables.EconModel["GDP"][
                    results.variables.EconModel["BankDataWriter"].keys()[i - 1]
                ].sum()
                + eps
            )
            for i in range(51, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["GDP"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
            and results.variables.EconModel["GDP"][
                results.variables.EconModel["BankDataWriter"].keys()[i - 1]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("GDP Increase")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/BankSummary.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/BankSummary.png")


def plotGoodsFirmsProfitSummary(results, saveFolder):
    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax1 = plt.subplot2grid((5, 2), (0, 0))
    ax1.margins(0.1)
    ax1.plot(
        [
            (
                results.variables.EconModel["CS Net Profits"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Net Profits"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Consumer Goods Firms Net Profits")
    ax1.set_xlabel("Year")

    ax1 = plt.subplot2grid((5, 2), (1, 0))
    ax1.margins(0.1)
    ax1.plot(
        [
            (
                results.variables.EconModel["CP Net Profits"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Net Profits"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Capital Goods Firms Net Profits")
    ax1.set_xlabel("Year")

    ax2 = plt.subplot2grid((5, 2), (2, 0))
    ax2.margins(0.1)
    ax2.plot(
        [
            (
                results.variables.EconModel["CS Loan Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Loan Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="ConsumptionGoods Loan Demand",
    )
    ax2.plot(
        [
            (
                results.variables.EconModel["CS Loan Obtained"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Loan Obtained"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="ConsumptionGoods Loan Obtained",
    )
    ax2.plot(
        [
            (
                results.variables.EconModel["CP Loan Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Loan Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="CapitalGoods Loan Demand",
    )
    ax2.plot(
        [
            (
                results.variables.EconModel["CP Loan Obtained"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Loan Obtained"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="CapitalGoods Loan Obtained",
    )
    ax2.set_ylabel("Loans")
    ax2.set_xlabel("Year")
    ax2.legend()

    ax3 = plt.subplot2grid((5, 2), (3, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["CS Firm Loans"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Firm Loans"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Consumer Goods Firms Loans")
    ax3.set_xlabel("Year")

    ax3 = plt.subplot2grid((5, 2), (4, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["CP Firm Loans"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].sum()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Firm Loans"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Capital Goods Firms Loans")
    ax3.set_xlabel("Year")

    ax1 = plt.subplot2grid((5, 2), (0, 1))
    ax1.margins(0.1)
    data = []
    [
        data.append(
            [
                (
                    results.variables.EconModel["CS Net Profits"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS Net Profits"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
        for j in range(len(results.variables.EconModel["CS Net Profits"][0]))
    ]
    ax1.boxplot(data)
    ax1.set_ylabel("Consumer Goods Firms Net Profits")

    ax1 = plt.subplot2grid((5, 2), (1, 1))
    ax1.margins(0.1)
    data = []
    [
        data.append(
            [
                (
                    results.variables.EconModel["CP Net Profits"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP Net Profits"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
        for j in range(len(results.variables.EconModel["CP Net Profits"][0]))
    ]
    ax1.boxplot(data)
    ax1.set_ylabel("Capital Goods Firms Net Profits")

    ax3 = plt.subplot2grid((5, 2), (3, 1))
    ax3.margins(0.1)
    data = []
    [
        data.append(
            [
                (
                    results.variables.EconModel["CS Firm Loans"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS Firm Loans"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
        for j in range(len(results.variables.EconModel["CS Firm Loans"][0]))
    ]
    ax3.boxplot(data)
    ax3.set_ylabel("Consumer Goods Firms Loans")

    ax3 = plt.subplot2grid((5, 2), (4, 1))
    ax3.margins(0.1)
    data = []
    [
        data.append(
            [
                (
                    results.variables.EconModel["CP Firm Loans"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][j]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP Firm Loans"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
        for j in range(len(results.variables.EconModel["CP Firm Loans"][0]))
    ]
    ax3.boxplot(data)
    ax3.set_ylabel("Capital Goods Firms Loans")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/GoodsFirmsProfitSummary.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/GoodsFirmsProfitSummary.png")


def plotGoodsFirmsDemandsSummary(results, saveFolder):
    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax1 = plt.subplot2grid((8, 2), (0, 0))
    ax1.margins(0.1)
    lines = ax1.plot(
        [
            (
                results.variables.EconModel["CS Labour Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Labour Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Consumer Goods Firms Labour Demand")
    ax1.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Labour Demand"][0]))
        ],
    )

    ax3 = plt.subplot2grid((8, 2), (1, 0))
    ax3.margins(0.1)
    lines = ax3.plot(
        [
            (
                results.variables.EconModel["CS Capital Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Capital Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Consumer Goods Capital Demand")
    ax3.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Capital Demand"][0]))
        ],
    )

    ax3 = plt.subplot2grid((8, 2), (2, 0))
    ax3.margins(0.1)
    lines = ax3.plot(
        [
            (
                results.variables.EconModel["CS Capital"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Capital"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Consumer Goods Capital")
    ax3.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Capital"][0]))
        ],
    )

    ax3 = plt.subplot2grid((8, 2), (3, 0))
    ax3.margins(0.1)
    lines = ax3.plot(
        [
            (
                results.variables.EconModel["CS Demand Forecast"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].squeeze()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Demand Forecast"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Consumer Goods Forecast Demand")
    ax3.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Demand Forecast"][0]))
        ],
    )

    ax1 = plt.subplot2grid((8, 2), (4, 0))
    ax1.margins(0.1)
    lines = ax1.plot(
        [
            (
                results.variables.EconModel["CP Labour Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Labour Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Capital Goods Firms Labour Demand")
    ax1.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Labour Demand"][0]))
        ],
    )

    ax3 = plt.subplot2grid((8, 2), (5, 0))
    ax3.margins(0.1)
    lines = ax3.plot(
        [
            (
                results.variables.EconModel["CP Capital Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Capital Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Capital Goods Capital Demand")
    ax3.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Capital Demand"][0]))
        ],
    )

    ax3 = plt.subplot2grid((8, 2), (6, 0))
    ax3.margins(0.1)
    lines = ax3.plot(
        [
            (
                results.variables.EconModel["CP Capital"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Capital"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Capital Goods Capital")
    ax3.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Capital"][0]))
        ],
    )

    ax3 = plt.subplot2grid((8, 2), (7, 0))
    ax3.margins(0.1)
    lines = ax3.plot(
        [
            (
                results.variables.EconModel["CP Demand Forecast"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ].squeeze()
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Demand Forecast"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Capital Goods Forecast Demand")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Demand Forecast"][0]))
        ],
    )

    ax1 = plt.subplot2grid((8, 2), (0, 1))
    ax1.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CS Labour Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Labour Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.boxplot(data)
    ax1.set_ylabel("Consumer Goods Firms Labour Demand")

    ax3 = plt.subplot2grid((8, 2), (1, 1))
    ax3.margins(0.1)
    ax3.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CS Capital Demand"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS Capital Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.set_ylabel("Consumer Goods Capital Demand")

    ax3 = plt.subplot2grid((8, 2), (2, 1))
    ax3.margins(0.1)
    ax3.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CS Capital"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS Capital"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.set_ylabel("Consumer Goods Capital")

    ax3 = plt.subplot2grid((8, 2), (3, 1))
    ax3.margins(0.1)
    ax3.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CS Demand Forecast"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ].squeeze()
                )
                for i in range(
                    50, len(results.variables.EconModel["BankDataWriter"]) - 50
                )
                if results.variables.EconModel["CS Demand Forecast"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.set_ylabel("Consumer Goods Forecast Demand")

    ax1 = plt.subplot2grid((8, 2), (4, 1))
    ax1.margins(0.1)
    ax1.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CP Labour Demand"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP Labour Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax1.set_ylabel("Capital Goods Firms Labour Demand")

    ax3 = plt.subplot2grid((8, 2), (5, 1))
    ax3.margins(0.1)
    ax3.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CP Capital Demand"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP Capital Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.set_ylabel("Capital Goods Capital Demand")

    ax3 = plt.subplot2grid((8, 2), (6, 1))
    ax3.margins(0.1)
    ax3.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CP Capital"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP Capital"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.set_ylabel("Capital Goods Capital")

    ax3 = plt.subplot2grid((8, 2), (7, 1))
    ax3.margins(0.1)
    ax3.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CP Demand Forecast"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ].squeeze()
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP Demand Forecast"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.set_ylabel("Capital Goods Forecast Demand")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/GoodsFirmsDemandsSummary.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/GoodsFirmsDemandsSummary.png")


def plotEnergyFirmsDemands(results, saveFolder):
    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax3 = plt.subplot(521)
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["GE Labour Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["GE Labour Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Green Energy",
    )
    ax3.plot(
        [
            (
                results.variables.EconModel["BE Labour Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["BE Labour Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Brown Energy",
    )
    ax3.set_ylabel("Electricity Labour Demand")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot(523)
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["GE Demand Forecast"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][0]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["GE Demand Forecast"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Green Energy",
    )
    ax3.plot(
        [
            (
                results.variables.EconModel["BE Demand Forecast"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][0]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["BE Demand Forecast"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Brown Energy",
    )
    ax3.set_ylabel("Electricity Demand Forecast")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot(525)
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["GE Price"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["GE Price"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Green Energy",
    )
    ax3.plot(
        [
            (
                results.variables.EconModel["BE Price"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["BE Price"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Brown Energy",
    )
    ax3.set_ylabel("Electricity Price")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot(527)
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["GE Capital"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["GE Capital"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Green Capital",
    )
    ax3.plot(
        [
            (
                results.variables.EconModel["BE Capital"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["BE Capital"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Brown Capital",
    )
    ax3.plot(
        [
            (
                results.variables.EconModel["GE Capital Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["GE Capital Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Green Capital Demand",
    )
    ax3.plot(
        [
            (
                results.variables.EconModel["BE Capital Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["BE Capital Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Brown Capital Demand",
    )
    ax3.set_ylabel("Electricity Capital")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot(522)
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["GE Labour Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][0]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["GE Labour Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            (
                results.variables.EconModel["BE Labour Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][0]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["BE Labour Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Electricity Labour Demand")

    ax3 = plt.subplot(524)
    ax3.margins(0.1)
    data = []
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["GE Demand Forecast"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["GE Demand Forecast"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["BE Demand Forecast"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["BE Demand Forecast"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Electricity Demand Forecast")

    ax3 = plt.subplot(526)
    ax3.margins(0.1)
    data = []
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["GE Price"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["GE Price"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["BE Price"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["BE Price"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Electricity Price")

    ax3 = plt.subplot(528)
    ax3.margins(0.1)
    data = []
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["GE Capital"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["GE Capital"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["BE Capital"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["BE Capital"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["GE Capital Demand"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["GE Capital Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["BE Capital Demand"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["BE Capital Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Electricity Capital")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/EnergyFirmsDemands.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/EnergyFirmsDemands.png")


def plotGoodsFirmWorkersSummary(results, saveFolder):
    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax1 = plt.subplot(421)
    ax1.margins(0.1)
    lines = ax1.plot(
        [
            (
                results.variables.EconModel["CS Number of Workers"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Number of Workers"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Consumer Goods Firms Number of Workers")
    ax1.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Labour Demand"][0]))
        ],
    )

    ax1 = plt.subplot(425)
    ax1.margins(0.1)
    lines = ax1.plot(
        [
            (
                results.variables.EconModel["CP Number of Workers"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Number of Workers"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Capital Goods Firms Number of Workers")
    ax1.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Capital"][0]))
        ],
    )

    ax2 = plt.subplot(423)
    ax2.margins(0.1)
    lines = ax2.plot(
        [
            (
                results.variables.EconModel["CS Number of Consumers"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Number of Consumers"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Consumer Goods Firms Number of Consumers")
    ax2.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Labour Demand"][0]))
        ],
    )

    ax3 = plt.subplot(427)
    ax3.margins(0.1)
    lines = ax3.plot(
        [
            (
                results.variables.EconModel["CP Number of Consumers"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Number of Consumers"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Capital Goods Firms Number of Consumers")
    ax3.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Capital"][0]))
        ],
    )

    ax1 = plt.subplot(422)
    ax1.margins(0.1)
    ax1.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CS Number of Workers"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS Number of Workers"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax1.set_ylabel("Consumer Goods Firms Number of Workers")

    ax1 = plt.subplot(426)
    ax1.margins(0.1)
    ax1.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CP Number of Workers"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP Number of Workers"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax1.set_ylabel("Capital Goods Firms Number of Workers")

    ax2 = plt.subplot(424)
    ax2.margins(0.1)
    ax2.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CS Number of Consumers"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS Number of Consumers"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax2.set_ylabel("Consumer Goods Firms Number of Consumers")

    ax3 = plt.subplot(428)
    ax3.margins(0.1)
    ax3.boxplot(
        np.array(
            [
                (
                    results.variables.EconModel["CP Number of Consumers"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP Number of Consumers"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.set_ylabel("Capital Goods Firms Number of Consumers")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/GoodsFirmWorkersSummary.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/GoodsFirmWorkersSummary.png")


def plotGoodsFirmSalesSummary(results, saveFolder):
    plt.figure(figsize=(56, 27))
    plt.subplots_adjust(hspace=0.5)

    ax1 = plt.subplot2grid((10, 2), (0, 0))
    ax1.margins(0.1)
    lines = ax1.plot(
        [
            (
                results.variables.EconModel["CS Price"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Price"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Consumer Goods Firms Price")
    ax1.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Labour Demand"][0]))
        ],
    )

    ax1 = plt.subplot2grid((10, 2), (1, 0))
    ax1.margins(0.1)
    lines = ax1.plot(
        [
            (
                results.variables.EconModel["CP Price"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Price"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax1.set_ylabel("Capital Goods Firms Price")
    ax1.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Capital"][0]))
        ],
    )

    ax2 = plt.subplot2grid((10, 2), (2, 0))
    ax2.margins(0.1)
    lines = ax2.plot(
        [
            (
                results.variables.EconModel["CS Sold Products"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Sold Products"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Consumer Goods Firms Sold Products")
    ax2.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Labour Demand"][0]))
        ],
    )

    ax3 = plt.subplot2grid((10, 2), (3, 0))
    ax3.margins(0.1)
    lines = ax3.plot(
        [
            (
                results.variables.EconModel["CP Sold Products"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Sold Products"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.set_ylabel("Capital Goods Firms Sold Products")
    ax3.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Capital"][0]))
        ],
    )

    ax2 = plt.subplot2grid((10, 2), (4, 0))
    ax2.margins(0.1)
    lines = ax2.plot(
        [
            (
                results.variables.EconModel["CS Inventory"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Inventory"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Consumer Goods Firms Inventory")
    ax2.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Labour Demand"][0]))
        ],
    )

    ax2 = plt.subplot2grid((10, 2), (5, 0))
    ax2.margins(0.1)
    lines = ax2.plot(
        [
            (
                results.variables.EconModel["CP Inventory"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Inventory"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Capital Goods Firms Inventory")
    ax2.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Labour Demand"][0]))
        ],
    )

    ax2 = plt.subplot2grid((10, 2), (6, 0))
    ax2.margins(0.1)
    lines = ax2.plot(
        [
            (
                results.variables.EconModel["CS Energy Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Energy Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Consumer Goods Firms Energy Demand")
    ax2.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Consumer Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CS Energy Demand"][0]))
        ],
    )

    ax2 = plt.subplot2grid((10, 2), (7, 0))
    ax2.margins(0.1)
    lines = ax2.plot(
        [
            (
                results.variables.EconModel["CP Energy Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Energy Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.set_ylabel("Capital Goods Firms Energy Demand")
    ax2.set_xlabel("Year")
    plt.legend(
        lines,
        [
            f"Capital Goods Firm no.{i+1}"
            for i in range(len(results.variables.EconModel["CP Energy Demand"][0]))
        ],
    )

    ax2 = plt.subplot2grid((10, 2), (8, 0))
    ax2.margins(0.1)
    lines = ax2.plot(
        [
            (
                np.sum(
                    results.variables.EconModel["CS V Cost"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS V Cost"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="VC",
    )
    lines = ax2.plot(
        [
            (
                np.sum(
                    results.variables.EconModel["CS U Cost"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS U Cost"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="UC",
    )
    lines = ax2.plot(
        [
            (
                np.sum(
                    results.variables.EconModel["CS Q Cost"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Q Cost"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="QC",
    )
    ax2.set_ylabel("Consumer Goods Firms Costs")
    ax2.set_xlabel("Year")
    plt.legend()

    ax2 = plt.subplot2grid((10, 2), (8, 0))
    ax2.margins(0.1)
    lines = ax2.plot(
        [
            (
                np.sum(
                    results.variables.EconModel["CP V Cost"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP V Cost"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="VC",
    )
    lines = ax2.plot(
        [
            (
                np.sum(
                    results.variables.EconModel["CP U Cost"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                )
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP U Cost"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="UC",
    )
    # lines=ax2.plot([(np.sum(results.variables.EconModel['CP Q Cost'][results.variables.EconModel['BankDataWriter'].keys()[i]])) for i in range(50,len(results.variables.EconModel['BankDataWriter'])) if results.variables.EconModel['Expected Inflation Rate'][results.variables.EconModel['BankDataWriter'].keys()[i]] is not None], label='QC')
    ax2.set_ylabel("Capital Goods Firms Costs")
    ax2.set_xlabel("Year")
    plt.legend()

    ax1 = plt.subplot2grid((10, 2), (0, 1))
    ax1.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CS Price"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Price"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    for d in data:
        ax1.boxplot(data)
    ax1.set_ylabel("Consumer Goods Firms Price")

    ax1 = plt.subplot2grid((10, 2), (1, 1))
    ax1.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CP Price"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Price"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    for d in data:
        ax1.boxplot(data)
    ax1.set_ylabel("Capital Goods Firms Price")

    ax2 = plt.subplot2grid((10, 2), (2, 1))
    ax2.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CS Sold Products"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Sold Products"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    for d in data:
        ax2.boxplot(data)
    ax2.set_ylabel("Consumer Goods Firms Sold Products")

    ax3 = plt.subplot2grid((10, 2), (3, 1))
    ax3.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CP Sold Products"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Sold Products"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Capital Goods Firms Sold Products")

    ax2 = plt.subplot2grid((10, 2), (4, 1))
    ax2.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CS Inventory"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Inventory"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.boxplot(data)
    ax2.set_ylabel("Consumer Goods Firms Inventory")

    ax2 = plt.subplot2grid((10, 2), (5, 1))
    ax2.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CP Inventory"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Inventory"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.boxplot(data)
    ax2.set_ylabel("Capital Goods Firms Inventory")

    ax2 = plt.subplot2grid((10, 2), (6, 1))
    ax2.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CS Energy Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CS Energy Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.boxplot(data)
    ax2.set_ylabel("Consumer Goods Firms Energy Demand")

    ax2 = plt.subplot2grid((10, 2), (7, 1))
    ax2.margins(0.1)
    data = np.array(
        [
            (
                results.variables.EconModel["CP Energy Demand"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["CP Energy Demand"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax2.boxplot(data)
    ax2.set_ylabel("Capital Goods Firms Energy Demand")

    ax2 = plt.subplot2grid((10, 2), (8, 1))
    ax2.margins(0.1)
    data = []
    data.append(
        np.array(
            [
                (
                    np.sum(
                        results.variables.EconModel["CS V Cost"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                    )
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS V Cost"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    data.append(
        np.array(
            [
                (
                    np.sum(
                        results.variables.EconModel["CS U Cost"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                    )
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS U Cost"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    data.append(
        np.array(
            [
                (
                    np.sum(
                        results.variables.EconModel["CS Q Cost"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                    )
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS Q Cost"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax2.boxplot(data)
    ax2.set_ylabel("Consumer Goods Firms Costs")

    ax2 = plt.subplot2grid((10, 2), (9, 1))
    ax2.margins(0.1)
    data = []
    data.append(
        np.array(
            [
                (
                    np.sum(
                        results.variables.EconModel["CP V Cost"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                    )
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CP V Cost"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    data.append(
        np.array(
            [
                (
                    np.sum(
                        results.variables.EconModel["CP U Cost"][
                            results.variables.EconModel["BankDataWriter"].keys()[i]
                        ]
                    )
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["CS U Cost"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    # data.append(np.array([(np.sum(results.variables.EconModel['CP Q Cost'][results.variables.EconModel['BankDataWriter'].keys()[i]])) for i in range(50,len(results.variables.EconModel['BankDataWriter'])) if results.variables.EconModel['Expected Inflation Rate'][results.variables.EconModel['BankDataWriter'].keys()[i]] is not None]))
    ax2.boxplot(data)
    ax2.set_ylabel("Capital Goods Firms Costs")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/GoodsFirmSalesSummary.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/GoodsFirmSalesSummary.png")


def plotClimateModuleEffects(results, saveFolder):
    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax3 = plt.subplot2grid((10, 2), (0, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["Climate C02 Taxes"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Climate C02 Taxes"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Climate C02 Taxes",
    )
    ax3.set_ylabel("Climate C02 Taxes")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot2grid((10, 2), (1, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["Climate C02"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            / 1e9
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Climate C02"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Climate C02 (GtCO2)",
    )
    ax3.set_ylabel("Climate C02")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot2grid((10, 2), (2, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["Climate Radiative Forcing"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][0]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Climate Radiative Forcing"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Climate Radiative Forcing",
    )
    ax3.set_ylabel("Climate Radiative Forcing")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot2grid((10, 2), (3, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["Climate Temperature"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Climate Temperature"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Climate Temperature",
    )
    ax3.set_ylabel("Climate Temperature")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot2grid((10, 2), (4, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            (
                results.variables.EconModel["Climate ETD"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Climate ETD"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Climate ETD",
    )
    ax3.plot(
        [
            (
                results.variables.EconModel["Climate ETM"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Climate ETM"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Climate ETM",
    )
    ax3.set_ylabel("Climate Aggregate Damage")
    ax3.set_xlabel("Year")
    ax3.legend()

    ax3 = plt.subplot2grid((10, 2), (0, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Climate C02 Taxes"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Climate C02 Taxes"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Climate C02 Taxes")

    ax3 = plt.subplot2grid((10, 2), (1, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            (
                results.variables.EconModel["Climate C02 Concentration"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ][0]
                / 1e9
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Climate C02 Concentration"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Climate C02 Concentration")

    ax3 = plt.subplot2grid((10, 2), (2, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["Climate Radiative Forcing"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["Climate Radiative Forcing"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Climate Radiative Forcing")

    ax3 = plt.subplot2grid((10, 2), (3, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["Climate Temperature"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["Climate Temperature"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Climate Temperature")

    ax3 = plt.subplot2grid((10, 2), (4, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        np.array(
            [
                (
                    results.variables.EconModel["Climate ETD"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ][0]
                )
                for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
                if results.variables.EconModel["Climate ETD"][
                    results.variables.EconModel["BankDataWriter"].keys()[i]
                ]
                is not None
            ]
        )
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Climate Aggregate Damage")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/ClimateModule.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/ClimateModule.png")


def plotCovidStatistics(results, saveFolder):

    plt.figure(figsize=(36, 27))
    plt.subplots_adjust(hspace=0.5)

    ax3 = plt.subplot2grid((2, 2), (0, 0))
    ax3.margins(0.1)
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == None
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Normal",
    )
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "susceptible"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Susceptible",
    )
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "mild"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Mild",
    )
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "infected non-sympotomatic"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Infected non-sympotomatic",
    )
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "severe"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Severe",
    )
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "critical"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Critical",
    )
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "dead"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Dead",
    )
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "recovered"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Recovered",
    )
    ax3.plot(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "immunized"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ],
        label="Immunized",
    )
    ax3.set_ylabel("Covid State Over Time (Days)")
    ax3.set_xlabel("Day")
    ax3.legend()

    ax3 = plt.subplot2grid((2, 2), (0, 1))
    ax3.margins(0.1)
    data = []
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == None
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "susceptible"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "mild"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "infected non-sympotomatic"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "severe"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "critical"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "dead"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "recovered"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    data.append(
        [
            len(
                [
                    state
                    for state in results.variables.EconModel["Covid State"][
                        results.variables.EconModel["BankDataWriter"].keys()[i]
                    ]
                    if state == "immunized"
                ]
            )
            for i in range(50, len(results.variables.EconModel["BankDataWriter"]))
            if results.variables.EconModel["Covid State"][
                results.variables.EconModel["BankDataWriter"].keys()[i]
            ]
            is not None
        ]
    )
    ax3.boxplot(data)
    ax3.set_ylabel("Covid State Over Time")

    if os.path.isdir(saveFolder):
        plt.savefig(f"{saveFolder}/CovidStat.png")
    else:
        os.mkdir(saveFolder)
        plt.savefig(f"{saveFolder}/CovidStat.png")


# =============================================================================
# Additional Graph and Analysis Functions (from examples/graph.py)
# =============================================================================

# Global tick definition for plotting
tick = pd.date_range("2018-1-1", "2021-12-31", freq="MS").strftime("%b%Y").tolist()


def ensure_folder_exists(folder_path):
    """Ensure that the specified folder exists, create if it doesn't."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    return folder_path


def debase(list):
    """
    De-bases the given time series list by subtracting the first value from all elements.
    """
    first_value = list[0]
    debased_list = [value - first_value for value in list]
    return debased_list


def cumulative_sum(time_series):
    """
    Calculates the cumulative sum of a time series.

    Parameters:
    - time_series: list or numpy array, the time series data

    Returns:
    - numpy array of cumulative sums
    """
    time_series = np.array(time_series)
    cumulative_values = np.cumsum(time_series)
    return cumulative_values


def normalize_value(data):
    """Returns a zero-filled list of the same length as data."""
    base_list = [0] * len(data)
    return base_list


def percentage_change(base, compare):
    """Calculate percentage change between two series."""
    percentage_diff = [
        (b - a) / a * 100 if a != 0 else 0 for a, b in zip(base, compare)
    ]
    return percentage_diff


def group_average(df, column_name, group_column):
    """
    Calculate the average of the specified column for each group defined by the group_column in the DataFrame.
    """
    unique_groups = df[group_column].unique()
    group_averages = {}

    for group in unique_groups:
        group_data = df[df[group_column] == group]
        avg_values = calculate_average(group_data, column_name)
        group_averages[group] = avg_values

    return group_averages


def clean_data(df, column_name):
    """
    Clean the specified column in the DataFrame by removing None values from the lists.
    """
    df[f"{column_name}_cleaned"] = df[column_name].apply(
        lambda value_list: [x for x in value_list if x is not None]
    )


def calculate_average(df, column_name):
    """
    Calculate the average of the specified column in the DataFrame across all lists at each time step.
    """
    max_length = max(
        len(value_list) for value_list in df[f"{column_name}_cleaned"]
    )  # Find the maximum length of the lists
    avg_values = [
        np.mean(
            [
                value_list[i]
                for value_list in df[f"{column_name}_cleaned"]
                if len(value_list) > i
            ]
        )
        for i in range(max_length)
    ]
    return avg_values


def calculate_confidence_interval(df, column_name, confidence=0.95):
    """
    Calculate the confidence interval for the specified column in the DataFrame across all lists at each time step.
    """
    max_length = max(len(value_list) for value_list in df[f"{column_name}_cleaned"])
    ci_lower = []
    ci_upper = []

    for i in range(max_length):
        values_at_t = [
            value_list[i]
            for value_list in df[f"{column_name}_cleaned"]
            if len(value_list) > i
        ]
        mean_at_t = np.mean(values_at_t)
        std_at_t = np.std(values_at_t)
        margin_of_error = 1.96 * std_at_t / np.sqrt(len(values_at_t))

        ci_lower.append(mean_at_t - margin_of_error)
        ci_upper.append(mean_at_t + margin_of_error)

    return ci_lower, ci_upper


def sensitivity_3d(
    name,
    data,
    length,
    covid_time,
    dataset_name,
    savecode,
    length_cut=10,
    area=False,
    export=False,
    save_folder="figures",
):
    """
    Create a 3D sensitivity plot.
    Note: data has to be a triplet of 3 series
    """
    folder_path = save_folder

    # prepare data input
    x = []
    y = []
    z = data[2]

    for i in range(len(data[0])):
        x.append(data[0][i][-length:])
        x[i] = x[i][:length_cut]
        x[i] = np.array(x[i]).mean()

    for i in range(len(data[1])):
        y.append(data[1][i][-length:])
        y[i] = y[i][:length_cut]
        y[i] = np.array(y[i]).mean()

    x_min = np.min(x)
    x_max = np.max(x)
    y_min = np.min(y)
    y_max = np.max(y)

    xi = np.linspace(x_min, x_max, 900)
    yi = np.linspace(y_min, y_max, 900)

    X, Y = np.meshgrid(xi, yi)
    Z = griddata((x, y), z, (X, Y), method="cubic")

    fig = go.Figure()
    fig.add_trace(go.Surface(x=xi, y=yi, z=Z, colorscale="Cividis"))
    fig.update_layout(
        scene=dict(
            zaxis=dict(range=[0, 1]),
            xaxis_title=dataset_name[0],
            yaxis_title=dataset_name[1],
            zaxis_title=dataset_name[2],
        ),
        width=700,
        margin=dict(r=20, b=10, l=10, t=10),
    )

    fig.show()

    if export:
        # Export the plot as a PDF file in the specified folder
        ensure_folder_exists(folder_path)
        pio.write_image(
            fig,
            os.path.join(folder_path, savecode + "_" + str(name) + "_plot.pdf"),
            format="pdf",
        )


def scatter_3d(
    name,
    data,
    length,
    dataset_name,
    savecode,
    length_cut=10,
    area=False,
    export=False,
    save_folder="figures",
):
    """
    Create a 3D scatter plot.
    Note: data has to be a triplet of 3 series
    """
    folder_path = save_folder

    # prepare data input
    x = []
    y = []

    for i in range(len(data[0])):
        x.append(data[0][i])
        x[i] = x[i][-length:]
        if length_cut != None:
            x[i] = x[i][:length_cut]

    for i in range(len(data[0])):
        y.append(data[1][i])
        y[i] = y[i][-length:]
        if length_cut != None:
            y[i] = y[i][:length_cut]

    # Create a date range with the same length as each item in the variable list
    if length_cut != None:
        end_date = pd.to_datetime("2023-01-01")  # The given end date
        start_date = end_date - pd.DateOffset(
            months=length
        )  # Calculate the start date 48 months before
        date_range = pd.date_range(
            start=start_date, periods=length_cut, freq="MS"
        )  # Generate the date range
        ntick = length_cut
    else:
        date_range = pd.date_range(end="2023-01-01", periods=length, freq="MS")
        ntick = length
    print(date_range[0])

    fig = go.Figure()
    for i, item in enumerate(x):
        fig.add_trace(go.Scatter3d(x=date_range, y=y[i], z=x[i], name=dataset_name[i]))

    fig.show()

    if export:
        # Export the plot as a PDF file in the specified folder
        ensure_folder_exists(folder_path)
        pio.write_image(
            fig,
            os.path.join(folder_path, savecode + "_" + str(name) + "_plot.pdf"),
            format="pdf",
        )


def pline_plot(
    name,
    data,
    color_set,
    length,
    covid_time,
    dataset_name,
    savecode,
    graph_title,
    length_cut=None,
    tick=3,
    area=False,
    export=False,
    is_percentage=False,
    apply_hp_filter=False,
    hp_lambda=14400,
    save_folder="figures",
):
    """
    Create a line plot with optional HP filter and confidence intervals.
    """
    folder_path = save_folder
    x = []

    # Prepare data input
    for i in range(len(data)):
        x.append(data[i])
        x[i] = x[i][-length:]

        if length_cut is not None:
            x[i] = x[i][:length_cut]

    # Apply Hodrick-Prescott filter if selected
    if apply_hp_filter:
        for i in range(len(x)):
            cycle, trend = hpfilter(x[i], lamb=hp_lambda)
            x[i] = trend  # Replace the original data with the trend component

    # Create a date range with the same length as each item in the variable list
    if length_cut is not None:
        end_date = pd.to_datetime("2025-01-01")  # The given end date
        start_date = end_date - pd.DateOffset(
            months=length
        )  # Calculate the start date 48 months before
        date_range = pd.date_range(
            start=start_date, periods=length_cut, freq="MS"
        )  # Generate the date range
    else:
        date_range = pd.date_range(end="2025-01-01", periods=length, freq="MS")

    # Create tick values for every three months
    tickvals = date_range[::tick]
    ticktext = [date.strftime("%m/%y") for date in tickvals]

    fig = go.Figure()
    for i, item in enumerate(x):
        fig.add_trace(
            go.Scatter(
                x=date_range,
                y=item,
                name=dataset_name[i],
                mode="lines",
                marker=dict(color=color_set[i]),
            )
        )

    # Set the y-axis label depending on whether it's percentage or absolute numbers
    y_axis_title = f"{name} (%)" if is_percentage else name

    # Set the x-axis title, y-axis title, and chart title
    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=-90,
            tickwidth=2,
            ticklen=10,
            gridcolor="darkgray",
            zerolinecolor="darkgray",
            gridwidth=0.1,
            ticks="outside",
            tickfont=dict(size=15),
            showline=True,
            linewidth=2,
            linecolor="black",
            mirror=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(
                text=y_axis_title,
                font=dict(family="Times New Roman, serif", size=20, color="black"),
            ),
            tickwidth=2,
            ticklen=10,
            gridcolor="lightgray",
            zerolinecolor="lightgray",
            gridwidth=0.1,
            ticks="outside",
            tickfont=dict(size=15),
            showline=True,
            linewidth=2,
            linecolor="black",
            mirror=True,
            fixedrange=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="left",
            x=0,
            font=dict(size=16),
        ),
        # Show a gray grid on the plot
        yaxis_gridcolor="darkgray",
        xaxis_gridcolor="darkgray",
        plot_bgcolor="white",
        margin=dict(l=50, r=20, t=50, b=50, pad=4),
        height=700,
        width=700,
        title=dict(
            text=graph_title,
            x=0.5,
            y=0.99,
            xanchor="center",
            yanchor="top",
            font=dict(family="Times New Roman, serif", size=36, color="black"),
        ),
    )
    # Add pre-covid area
    if area:
        fig.add_vline(x=covid_time, line_width=4, line_dash="dash", line_color="red")
    # Option to export the graph
    if export:
        # Export the plot as a PDF file in the specified folder
        ensure_folder_exists(folder_path)
        pio.write_image(
            fig,
            os.path.join(folder_path, savecode + "_" + str(name) + "_plot.pdf"),
            format="pdf",
        )

    fig.show()


def pline_plot_with_ci(
    name,
    data,
    color_set,
    length,
    covid_time,
    dataset_name,
    savecode,
    graph_title,
    ci_data,
    length_cut=None,
    tick=3,
    area=False,
    export=False,
    save_folder="figures",
):
    """
    A function to plot time series data with optional confidence intervals and pre-COVID vertical line.
    """
    folder_path = save_folder
    x = []
    ci_lower = []
    ci_upper = []

    # Prepare data and confidence interval input
    for i in range(len(data)):
        x.append(data[i][-length:])
        if length_cut is not None:
            x[i] = x[i][:length_cut]

        lower_bound, upper_bound = ci_data[i]
        ci_lower.append(lower_bound[-length:])
        ci_upper.append(upper_bound[-length:])

        if length_cut is not None:
            ci_lower[i] = ci_lower[i][:length_cut]
            ci_upper[i] = ci_upper[i][:length_cut]

    # Create a date range with the same length as each item in the variable list
    if length_cut is not None:
        end_date = pd.to_datetime("2023-01-01")  # The given end date
        start_date = end_date - pd.DateOffset(months=length)
        date_range = pd.date_range(start=start_date, periods=length_cut, freq="MS")
        ntick = length_cut
    else:
        date_range = pd.date_range(end="2023-01-01", periods=length, freq="MS")
        ntick = length

    # Create tick values for every three months
    tickvals = date_range[::tick]
    ticktext = [date.strftime("%m/%y") for date in tickvals]

    fig = go.Figure()

    # Add confidence intervals first (so they appear behind the lines)
    for i, item in enumerate(x):
        fig.add_trace(
            go.Scatter(
                x=date_range,
                y=ci_upper[i],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=date_range,
                y=ci_lower[i],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor=f"rgba{tuple(list(plt.colors.to_rgba(color_set[i])[:3]) + [0.2])}",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Add the main data lines
    for i, item in enumerate(x):
        fig.add_trace(
            go.Scatter(
                x=date_range,
                y=item,
                name=dataset_name[i],
                mode="lines",
                line=dict(color=color_set[i], width=2),
            )
        )

    # Update layout
    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=-90,
            tickwidth=2,
            ticklen=10,
            gridcolor="darkgray",
            zerolinecolor="darkgray",
            gridwidth=0.1,
            ticks="outside",
            tickfont=dict(size=15),
            showline=True,
            linewidth=2,
            linecolor="black",
            mirror=True,
            fixedrange=True,
        ),
        yaxis=dict(
            title=dict(
                text=name,
                font=dict(family="Times New Roman, serif", size=20, color="black"),
            ),
            tickwidth=2,
            ticklen=10,
            gridcolor="lightgray",
            zerolinecolor="lightgray",
            gridwidth=0.1,
            ticks="outside",
            tickfont=dict(size=15),
            showline=True,
            linewidth=2,
            linecolor="black",
            mirror=True,
            fixedrange=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="left",
            x=0,
            font=dict(size=16),
        ),
        yaxis_gridcolor="darkgray",
        xaxis_gridcolor="darkgray",
        plot_bgcolor="white",
        margin=dict(l=50, r=20, t=50, b=50, pad=4),
        height=700,
        width=700,
        title=dict(
            text=graph_title,
            x=0.5,
            y=0.99,
            xanchor="center",
            yanchor="top",
            font=dict(family="Times New Roman, serif", size=36, color="black"),
        ),
    )

    # Add pre-covid area
    if area:
        fig.add_vline(x=covid_time, line_width=4, line_dash="dash", line_color="red")

    # Option to export the graph
    if export:
        ensure_folder_exists(folder_path)
        pio.write_image(
            fig,
            os.path.join(folder_path, savecode + "_" + str(name) + "_plot.pdf"),
            format="pdf",
        )

    fig.show()


def pbar_plot(
    name,
    data,
    length,
    covid_time,
    dataset_name,
    savecode,
    area=False,
    export=False,
    save_folder="figures",
):
    """Create bar plots for data visualization."""
    folder_path = save_folder
    x = []

    for i in range(len(data)):
        x.append(data[i][-length:])

    fig = go.Figure()
    for i, item in enumerate(x):
        fig.add_trace(go.Bar(x=list(range(len(item))), y=item, name=dataset_name[i]))

    fig.update_layout(
        title=name, xaxis_title="Time", yaxis_title="Value", barmode="group"
    )

    if export:
        ensure_folder_exists(folder_path)
        pio.write_image(
            fig,
            os.path.join(folder_path, f"{savecode}_{name}_plot.pdf"),
            format="pdf",
        )

    fig.show()


def box_plot(
    name,
    data,
    color_set,
    length,
    dataset_name,
    savecode,
    graph_title,
    length_cut=None,
    export=False,
    save_folder="figures",
):
    """Create box plots for data distribution analysis."""
    folder_path = save_folder
    x = []

    for i in range(len(data)):
        x.append(data[i][-length:])
        if length_cut is not None:
            x[i] = x[i][:length_cut]

    fig = go.Figure()
    for i, item in enumerate(x):
        fig.add_trace(
            go.Box(
                y=item,
                name=dataset_name[i],
                marker_color=color_set[i] if i < len(color_set) else None,
            )
        )

    fig.update_layout(
        title=graph_title, xaxis_title="Dataset", yaxis_title=name, showlegend=True
    )

    if export:
        ensure_folder_exists(folder_path)
        pio.write_image(
            fig,
            os.path.join(folder_path, f"{savecode}_{name}_plot.pdf"),
            format="pdf",
        )

    fig.show()


def heatmap_plot(
    name,
    data,
    color_set,
    length,
    dataset_names,
    savecode,
    graph_title,
    length_cut=None,
    tick=3,
    export=False,
    save_folder="figures",
):
    """Create heatmap visualization for correlation analysis."""
    folder_path = save_folder

    # Prepare data matrix
    matrix_data = []
    for i in range(len(data)):
        series = data[i][-length:]
        if length_cut is not None:
            series = series[:length_cut]
        matrix_data.append(series)

    # Convert to correlation matrix if multiple series
    if len(matrix_data) > 1:
        df = pd.DataFrame(matrix_data).T
        correlation_matrix = df.corr()

        fig = go.Figure(
            data=go.Heatmap(
                z=correlation_matrix.values,
                x=dataset_names,
                y=dataset_names,
                colorscale="Viridis",
            )
        )
    else:
        # Single series heatmap
        reshaped_data = np.array(matrix_data[0]).reshape(1, -1)
        fig = go.Figure(data=go.Heatmap(z=reshaped_data, colorscale="Viridis"))

    fig.update_layout(
        title=graph_title, xaxis_title="Variables", yaxis_title="Variables"
    )

    if export:
        ensure_folder_exists(folder_path)
        pio.write_image(
            fig,
            os.path.join(folder_path, f"{savecode}_heatmap.pdf"),
            format="pdf",
        )

    fig.show()


# Note: Additional plotting functions from examples/graph.py have been integrated.
# The following functions are available:
# - debase(): De-base time series data
# - cumulative_sum(): Calculate cumulative sums
# - percentage_change(): Calculate percentage changes
# - group_average(): Calculate group averages
# - clean_data(): Clean DataFrame columns
# - calculate_average(): Calculate averages across DataFrames
# - calculate_confidence_interval(): Calculate confidence intervals
# - sensitivity_3d(): Create 3D sensitivity plots
# - scatter_3d(): Create 3D scatter plots
# - pline_plot(): Create line plots with advanced formatting
# - pline_plot_with_ci(): Create line plots with confidence intervals
# - pbar_plot(): Create bar plots
# - box_plot(): Create box plots
# - heatmap_plot(): Create heatmap visualizations


def lognormal(mu, sigma):
    mean = math.log(mu**2 / math.sqrt(sigma + mu**2))
    std = math.sqrt(math.log(sigma / mu**2 + 1))
    y = np.random.lognormal(mean, std)
    return y


def normal(mu, sigma):
    mean = mu
    std = math.sqrt(sigma)
    y = np.random.normal(mean, std)
    return y


### Unused functions:


def setSignalToFirmForHiring(self):
    self.signalToFirmForHiring = (
        self.p.signalParameterOfProductivity * self.productivity
        + self.p.signalParameterOfRandomComponent
        * (random.random() - 0.5)
        * self.p.productivityParetoPositionParameter
        + self.desiredEConsumption * self.p.EnergyToProductivity
    )


def getSignalToFirmForHiring(self):
    return self.signalToFirmForHiring
