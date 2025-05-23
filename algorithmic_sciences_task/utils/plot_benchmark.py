"""
Benchmark analysis plotting.

Generates performance visualizations for different search algorithms.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config.settings import CONFIG_FILE_PATH
from core.config_loader import get_config_value

# Load file path from config
CSV_PATH = get_config_value(
    CONFIG_FILE_PATH,
    "search_benchmark_csv",
    "utils/search_benchmark_results.csv",
)

# Load the CSV data
df = pd.read_csv(CSV_PATH)

# Set Seaborn theme for better visuals
sns.set(style="whitegrid")


def plot_execution_time(df: pd.DataFrame) -> None:
    """Plot algorithm execution time across different file sizes."""
    pivot_df = df.pivot(
        index="File Size", columns="Algorithm", values="Avg Time (ms)"
    )

    plt.figure(figsize=(12, 6))
    for column in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df[column], marker="o", label=column)

    plt.xlabel("File Size")
    plt.ylabel("Average Time (ms)")
    plt.title("Algorithm Performance by File Size")
    plt.legend(title="Algorithm")
    plt.xscale("log")
    plt.tight_layout()
    plt.savefig("utils/algorithm_performance_comp.png")
    plt.show()


def plot_memory_usage(df: pd.DataFrame) -> None:
    """Plot algorithm memory usage across different file sizes."""
    pivot_mem_df = df.pivot(
        index="File Size", columns="Algorithm", values="Avg Memory (MB)"
    )

    plt.figure(figsize=(12, 6))
    for column in pivot_mem_df.columns:
        plt.plot(
            pivot_mem_df.index, pivot_mem_df[column], marker="s", label=column
        )

    plt.xlabel("File Size")
    plt.ylabel("Average Memory (MB)")
    plt.title("Algorithm Memory Usage by File Size")
    plt.legend(title="Algorithm")
    plt.xscale("log")
    plt.tight_layout()
    plt.savefig("utils/algorithm_memory_usage_comp.png")
    plt.show()


def compute_average_memory(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the average memory usage for each algorithm."""
    avg_memory_df = (
        df.groupby("Algorithm")["Avg Memory (MB)"].mean().reset_index()
    )
    avg_memory_df.rename(
        columns={"Avg Memory (MB)": "Average Memory Usage (MB)"}, inplace=True
    )
    return avg_memory_df


def compute_average_runtime(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the average execution time for each algorithm."""
    avg_runtime_df = (
        df.groupby("Algorithm")["Avg Time (ms)"].mean().reset_index()
    )
    avg_runtime_df.rename(
        columns={"Avg Time (ms)": "Average Runtime (ms)"}, inplace=True
    )
    return avg_runtime_df


def plot_average_runtime(avg_runtime_df: pd.DataFrame) -> None:
    """Plot average runtime for each algorithm."""
    plt.figure(figsize=(10, 6))
    sns.barplot(
        x="Algorithm",
        y="Average Runtime (ms)",
        data=avg_runtime_df,
        palette="muted",
    )

    plt.xlabel("Algorithm")
    plt.ylabel("Average Runtime (ms)")
    plt.title("Overall Average Runtime per Algorithm")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("utils/algorithm_average_runtime.png")
    plt.show()


def display_average_runtime_table(avg_runtime_df: pd.DataFrame) -> None:
    """Display the table of average runtimes."""
    print("\n=== Average Runtime per Algorithm ===")
    print(avg_runtime_df.to_string(index=False))


def display_average_memory_table(avg_memory_df: pd.DataFrame) -> None:
    """Display the table of average memory usage."""
    print("\n=== Average Memory Usage per Algorithm ===")
    print(avg_memory_df.to_string(index=False))


if __name__ == "__main__":
    plot_execution_time(df)
    plot_memory_usage(df)

    # Compute and visualize average runtime per algorithm
    avg_runtime_df = compute_average_runtime(df)
    plot_average_runtime(avg_runtime_df)
    display_average_runtime_table(avg_runtime_df)

    # Compute and visualize average memory usage per algorithm
    avg_memory_df = compute_average_memory(df)
    display_average_memory_table(avg_memory_df)
