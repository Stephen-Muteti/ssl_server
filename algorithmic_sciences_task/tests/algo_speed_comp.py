"""
Search algorithm benchmarking.

Measures the speed and memory efficiency of various search algorithms
on files of different sizes.
"""

import time
import csv
import os
from typing import List, Tuple, Callable

import psutil

# First-party imports (your internal modules)
from config.settings import CONFIG_FILE_PATH
from core.config_loader import get_config_value
from core.logger import logger

# Import searcher classes (grouped together)
from core.search_algorithms.line_by_line import LineByLineSearcher
from core.search_algorithms.mmap_search import MmapSearcher
from core.search_algorithms.buffered_chunk_search import BufferedChunkSearcher
from core.search_algorithms.regex_line_search import RegexLineSearcher
from core.search_algorithms.trie_search import TrieBasedSearcher
from core.search_algorithms.cached_line_search import CachedLineSearcher
from core.search_algorithms.set_based_searcher import SetBasedSearcher
from core.search_algorithms.protocols import SearchProtocol


class SearchBenchmarkRunner:
    """
    Benchmark search algorithms on files of different sizes.

    Attributes:
        search_term (str): The term to be searched in files.
        sizes (List[int]): List of file sizes (number of lines).
        reread_on_query (bool): Whether to reread the file on each search.
        temp_dir (str): Directory to generate test files.
        results (List[Tuple[int, str, float]]): Collected benchmarking results.
    """

    def __init__(self, temp_dir: str = "tests/temp_files") -> None:
        """Initialize benchmark settings and create test directory."""
        self.search_term = get_config_value(
            CONFIG_FILE_PATH,
            "search_term",
            default="Stephen is overly talented",
        )
        self.sizes = [10_000, 100_000, 500_000, 1_000_000]
        self.reread_on_query = get_config_value(
            CONFIG_FILE_PATH, "reread", default=False
        )
        self.temp_dir = temp_dir
        self.results: List[Tuple[int, str, float, float]] = []
        os.makedirs(self.temp_dir, exist_ok=True)

        self.algorithms: List[Tuple[str, SearchProtocol]] = [
            ("LineByLineSearcher", LineByLineSearcher()),
            ("MMapSearcher", MmapSearcher()),
            ("BufferedChunkSearcher", BufferedChunkSearcher()),
            ("RegexLineSearcher", RegexLineSearcher()),
            ("TrieSearcher", TrieBasedSearcher()),
            ("CachedLineSearcher", CachedLineSearcher()),
            ("SetBasedSearcher", SetBasedSearcher()),
        ]

    def generate_test_file(self, line_count: int, filename: str) -> str:
        """
        Generate a test file containing dummy lines.

        The search term is appended at the end of the file.

        Args:
            line_count (int): Number of dummy lines to write.
            filename (str): Name of the file to create.

        Returns:
            str: Full path to the created file.
        """
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            for i in range(line_count):
                f.write(f"This is line number {i}\n")
            f.write(self.search_term + "\n")
        return filepath

    def benchmark_algorithm(
        self,
        algorithm_func: Callable[[str, str, bool], str],
        file_path: str,
        num_runs: int = 3,
    ) -> Tuple[float, float]:
        """
        Measure execution time and memory usage for a search algorithm.

        Runs the search function multiple times and computes the average
        execution time (in milliseconds) and memory usage (in megabytes).

        Args:
            algorithm_func (Callable): The search function to benchmark.
                Should accept (file_path, search_term, reread_on_query).
            file_path (str): Path to the file for search execution.
            num_runs (int): Number of benchmark runs (default is 3).

        Returns:
            Tuple[float, float]: A tuple containing:
                - Average execution time in milliseconds.
                - Average memory usage in megabytes (MB).
        """
        algorithm_func(file_path, self.search_term, self.reread_on_query)

        process = psutil.Process(os.getpid())
        total_time = 0.0
        total_memory = 0.0
        for _ in range(num_runs):
            start_time = time.time()
            start_mem = process.memory_info().rss

            algorithm_func(file_path, self.search_term, self.reread_on_query)

            end_mem = process.memory_info().rss
            end_time = time.time()
            total_time += end_time - start_time
            total_memory += end_mem - start_mem

        avg_time = (total_time / num_runs) * 1000
        avg_memory = total_memory / num_runs / (1024 * 1024)
        return avg_time, avg_memory

    def write_to_csv(self, filename: str) -> None:
        """
        Save benchmark results to a CSV file.

        Args:
            filename (str): Path to the CSV file.
        """
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["File Size", "Algorithm", "Avg Time (ms)", "Avg Memory (MB)"]
            )
            writer.writerows(self.results)

    def run(self) -> None:
        """
        Execute benchmark tests on multiple search algorithms.

        Runs performance benchmarks for different search algorithms on various
        file sizes, then saves the results to a CSV file.
        """
        for size in self.sizes:
            file_path = self.generate_test_file(size, f"test_file_{size}.txt")
            for name, searcher in self.algorithms:
                logger.debug("Testing %s on %d lines", name, size)
                avg_time, avg_mem = self.benchmark_algorithm(
                    searcher.search, file_path
                )
                self.results.append((size, name, avg_time, avg_mem))

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
        utils_dir = os.path.join(project_root, "utils")
        os.makedirs(utils_dir, exist_ok=True)

        csv_path = get_config_value(
            CONFIG_FILE_PATH,
            "benchmark_output_csv",
            os.path.join(utils_dir, "search_benchmark_results.csv"),
        )

        self.write_to_csv(csv_path)
        print(f"Benchmark results written to {csv_path}")


if __name__ == "__main__":
    runner = SearchBenchmarkRunner()
    runner.run()
