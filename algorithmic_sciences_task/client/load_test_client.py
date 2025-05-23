"""Load test client module for benchmarking server performance."""

import socket
import ssl
import time
import threading
import csv
from pathlib import Path
from typing import List, Tuple, Optional
from core.logger import logger
from core.config_loader import get_config_value
from config.settings import CONFIG_FILE_PATH


class BenchmarkClient:
    """
    Handle sending search queries to the server and measuring latency.

    This client establishes connections and records response times.
    """

    def __init__(self) -> None:
        """Initialize BenchmarkClient with server settings."""
        self.ssl_config = {
            "enabled": get_config_value(
                CONFIG_FILE_PATH, "ssl_enabled", default=False
            ),
            "client_cert": get_config_value(
                CONFIG_FILE_PATH, "client_certfile"
            ),
            "client_key": get_config_value(CONFIG_FILE_PATH, "client_keyfile"),
            "server_cert": get_config_value(
                CONFIG_FILE_PATH, "server_certfile"
            ),
        }

        self.server_info = {
            "host": get_config_value(
                CONFIG_FILE_PATH, "server_host", default="127.0.0.1"
            ),
            "port": int(
                get_config_value(CONFIG_FILE_PATH, "server_port", default=5000)
            ),
        }

        self.search_term = get_config_value(
            CONFIG_FILE_PATH,
            "search_term",
            default="Stephen is overly talented",
        )

    def supports_ssl(self) -> bool:
        """
        Check if SSL/TLS is enabled for the client.

        Returns:
            bool: True if SSL/TLS is enabled, False otherwise.
        """
        return self.ssl_config["enabled"]

    def run_query(self, filename: str) -> Tuple[Optional[float], str]:
        """
        Send a search query to the server using mTLS.

        Args:
            filename (str): File to search on the server.

        Returns:
            Tuple[Optional[float], str]:
                Response time in seconds and the server response or error.
        """
        message = f"{filename}|{self.search_term}"
        try:
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if self.ssl_config["ssl_enabled"]:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

                # Load client-side certificate and private key
                context.load_cert_chain(
                    certfile=self.ssl_config["client_cert"],
                    keyfile=self.ssl_config["client_key"],
                )

                # Enforce mutual TLS authentication
                context.verify_mode = ssl.CERT_REQUIRED
                context.load_verify_locations(
                    self.ssl_config["server_cert"]
                )  # Validate server certificate

                with context.wrap_socket(
                    raw_socket, server_hostname=self.server_info["host"]
                ) as sock:
                    sock.settimeout(2)
                    sock.connect(
                        (self.server_info["host"], self.server_info["host"])
                    )
                    sock.sendall(message.encode())
                    start = time.time()
                    response = sock.recv(4096)
                    end = time.time()
            else:
                with raw_socket as sock:
                    sock.settimeout(2)
                    sock.connect(
                        (self.server_info["host"], self.server_info["port"])
                    )
                    sock.sendall(message.encode())
                    start = time.time()
                    response = sock.recv(4096)
                    end = time.time()

            return end - start, response.decode().strip()

        except (OSError, ssl.SSLError, ValueError) as e:
            logger.error("SSL connection setup failed: %s", e)
            return None, f"ERROR: {e}"


class BenchmarkServer:
    """
    Benchmarks server performance.

    Simulates load over various file sizes and QPS.
    """

    def __init__(
        self,
        file_sizes: List[int],
        qps_range: Tuple[int, int] = (1, 100),
        duration_per_level: int = 3,
    ) -> None:
        """Initialize BenchmarkClient with server configurations."""
        self.client = BenchmarkClient()
        self.test_config = {
            "file_sizes": file_sizes,
            "qps_range": qps_range,
            "duration_per_level": duration_per_level,
            "results_dir": get_config_value(
                CONFIG_FILE_PATH, "results_dir", default="utils"
            ),
            "temp_file_dir": get_config_value(
                CONFIG_FILE_PATH, "temp_file_dir", default="tests/temp_files"
            ),
            "result_file_name": "load_test_results.csv",
        }

        self.ssl_config = {
            "enabled": get_config_value(
                CONFIG_FILE_PATH, "ssl_enabled", default=False
            ),
        }

        self.server_info = {
            "host": get_config_value(
                CONFIG_FILE_PATH, "server_host", default="127.0.0.1"
            ),
            "port": int(
                get_config_value(CONFIG_FILE_PATH, "server_port", default=5000)
            ),
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the BenchmarkClient instance.

        Returns:
            str: Summary of server configuration.
        """
        return (
            f"BenchmarkClient(server_host={self.server_info['host']}, "
            f"ssl_enabled={self.ssl_config['enabled']})"
        )

    def run(self) -> None:
        """Benchmark server performance by simulating load."""
        results = []

        for size in self.test_config["file_sizes"]:
            size_filename = str(
                Path(self.test_config["temp_file_dir"])
                / f"test_file_{size}.txt"
            )
            print(f"\nTesting file size: {size} bytes")

            for qps in range(
                self.test_config["qps_range"][0],
                self.test_config["qps_range"][1] + 1,
            ):
                print(f"  QPS {qps} -> ", end="")

                latencies: list[float] = []
                errors = 0
                start_time = time.time()
                end_time = start_time + self.test_config["duration_per_level"]
                interval = 1.0 / qps

                def query_thread(
                    filename: str, latencies_list: List[float]
                ) -> None:
                    """Perform a query in a separate thread."""
                    nonlocal errors
                    latency, response = self.client.run_query(filename)
                    if latency is not None:
                        latencies_list.append(latency * 1000)
                    else:
                        errors += 1
                        logger.error("Query error: %s", response)

                threads = []

                while time.time() < end_time:
                    t = threading.Thread(
                        target=query_thread, args=(size_filename, latencies)
                    )
                    t.start()
                    threads.append(t)
                    time.sleep(interval)

                for t in threads:
                    t.join()

                avg_latency = (
                    sum(latencies) / len(latencies) if latencies else 0
                )
                print(f"Latency: {avg_latency:.2f} ms, Errors: {errors}")
                results.append([size, qps, avg_latency, errors])
        self.save_results(results)

    def save_results(self, results: List[List]) -> None:
        """Save benchmark results to a CSV file."""
        results_file = (
            Path(__file__).parent.parent
            / self.test_config["results_dir"]
            / self.test_config["result_file_name"]
        )
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with results_file.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["File Size", "QPS", "Avg Latency (ms)", "Error Count"]
            )
            writer.writerows(results)

        print(f"\nLoad test results written to: {results_file.resolve()}")


if __name__ == "__main__":
    # Define test file sizes
    test_file_sizes = [10_000, 100_000, 500_000, 1_000_000]

    # Run benchmark
    benchmark = BenchmarkServer(
        test_file_sizes, qps_range=(1, 100), duration_per_level=2
    )
    benchmark.run()
