"""
Plot benchmark analysis.

Visualizes benchmark results with latency, error trends, and QPS thresholds.
"""

import os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config.settings import CONFIG_FILE_PATH

from core.config_loader import get_config_value


def load_data(csv_path: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    return pd.read_csv(csv_path)


def plot_latency_vs_qps(df: pd.DataFrame) -> None:
    """
    Plot the relationship between average latency and queries per second (QPS).

    Args:
        df (pd.DataFrame): The DataFrame containing benchmark data.

    Returns:
        None: This function does not return any value.
    """
    plt.figure(figsize=(12, 6))
    sns.lineplot(
        data=df,
        x="qps",
        y="avg_latency_ms",
        hue="file_size",
        marker="o",
        palette="tab10",
    )
    plt.title("Average Latency vs QPS for Different File Sizes")
    plt.xlabel("Queries Per Second (QPS)")
    plt.ylabel("Average Latency (ms)")
    plt.legend(title="File Size")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("utils/latency_vs_qps.png")
    plt.show()


def plot_errors_vs_qps(df: pd.DataFrame) -> None:
    """
    Plot the relationship between error count and queries per second (QPS).

    Args:
        df (pd.DataFrame): The DataFrame containing benchmark data.

    Returns:
        None: This function does not return any value.
    """
    plt.figure(figsize=(12, 6))
    sns.lineplot(
        data=df,
        x="qps",
        y="error_count",
        hue="file_size",
        marker="x",
        palette="Set2",
    )
    plt.title("Error Count vs QPS for Different File Sizes")
    plt.xlabel("Queries Per Second (QPS)")
    plt.ylabel("Error Count")
    plt.legend(title="File Size")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("utils/errors_vs_qps.png")
    plt.show()


def plot_thresholds(df: pd.DataFrame) -> None:
    """
    Plot the maximum sustainable QPS without errors for different file sizes.

    Args:
        df (pd.DataFrame): The DataFrame containing benchmark data.

    Returns:
        None: This function does not return any value.
    """
    threshold_data = (
        df[df["error_count"] == 0]
        .groupby("file_size")["qps"]
        .max()
        .reset_index()
        .rename(columns={"qps": "max_qps_without_error"})
    )

    plt.figure(figsize=(10, 5))
    sns.barplot(
        data=threshold_data,
        x="file_size",
        y="max_qps_without_error",
        palette="coolwarm",
    )
    plt.title("Max Sustainable QPS Without Errors per File Size")
    plt.xlabel("File Size")
    plt.ylabel("Max QPS (0 Errors)")
    plt.tight_layout()
    plt.savefig("utils/qps_thresholds.png")
    plt.show()


if __name__ == "__main__":
    # Path to the CSV file containing benchmark data
    csv_path = get_config_value(
        CONFIG_FILE_PATH, "load_test_csv", "utils/load_test_results.csv"
    )
    csv_path = os.path.join("utils", "load_test_results.csv")

    # Load the data from the CSV file
    df = load_data(csv_path)

    # Clean up column names by removing spaces and converting to lowercase
    df.rename(
        columns=lambda x: x.strip()
        .lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", ""),
        inplace=True,
    )

    # Remove rows with latency of 0 and errors > 0
    df = df[df["avg_latency_ms"] > 0]
    df = df[(df["qps"] >= 1) & (df["qps"] <= 50)]

    # Generate plots
    plot_latency_vs_qps(df)
    plot_errors_vs_qps(df)
    plot_thresholds(df)
