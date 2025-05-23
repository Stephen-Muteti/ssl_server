# File Search Benchmarking Tool

This project benchmarks the performance of different file search algorithms across varying file sizes. It evaluates speed and efficiency using methods like line-by-line search, cached reads, memory-mapped files (`mmap`), and set-based lookup.


## Project Structure

algorithmic_sciences_task
├── certs
│   ├── server_openssl.cnf
│   ├── client_openssl.cnf
│   ├── server.key
│   ├── server.crt
│   ├── client.key
│   ├── client.crt
│   └── ca.pem
├── client
│ 	├── __init__.py
│   ├── client.py
│ 	└── load_test_client.py
├── config
│  	├── __init__.py
│ 	├── server_config.yaml
│ 	└── settings.py
├── core
│ 	├── __init__.py
│   ├── config_loader.py
│   ├── connection_handler.py
│   ├── logger.py
│   ├── ssl_wrapper.py
│   └── search_algorithms
│       ├── __init__.py
│       ├── buffered_chunk_search.py
│       ├── cached_line_search.py
│       ├── line_by_line.py
│       ├── mmap_search.py
│       ├── protocols.py
│       ├── regex_line_search.py
│       ├── set_based_searcher.py
│       └── trie_search.py
├── data
│ 	├── __init__.py
│ 	└── file_to_search.txt
├── server/
│ 	├── __init__.py
│ 	└── tcp_server.py
├── tests
│ 	├── __init__.py
│ 	├── algo_speed_comp.py
│ 	├── test_client.py
│   ├── test_connection_handler.py
│   ├── test_search_algorithms.py
│ 	└── temp_files
│       ├── empty.txt
│ 		├── test_file_10000.txt
│ 		├── test_file_100000.txt
│ 		├── test_file_500000.txt
│ 		└── test_file_1000000.txt
├── utils
│ 	├── 
│   ├── algorithm_memory_usage_comp.png
│   ├── algorithm_performance_comp.png
│   ├── errors_vs_qps.png
│   ├── latency_vs_qps.png
│   ├── latency_vs_qps.png
│   ├── load_test_results.csv
│   ├── plot_benchmark.py
│   ├── plot_benchmark_analysis.py
│   ├── qps_thresholds.png
│ 	└── search_benchmark_results.csv
├── .flake8
├── mypy.ini
├── pyproject.toml
├── pytest.ini
├── README.md
├── REPRODUCE.md
├── requirements.txt
└── run_server.py



## Setup

### 1. Install Dependencies
This project uses only the standard Python libraries (`os`, `csv`, `time`, `matplotlib`, etc.):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Benchmarks

From the root directory:
```bash
python -m tests.algo_speed_comp
```
This will:

    Generate test files of various sizes (10k to 1M lines)

    Run each search algorithm multiple times

    Save benchmark results to utils/search_benchmark_results.csv

## Visualizing Results

To generate and view a comparison chart:

```bash
python -m utils.plot_benchmark
```

This will display and save a plot comparing average search times across all methods and file sizes.

## Output

The generated CSV (utils/search_benchmark_results.csv) looks like:
	File Size,Algorithm,Avg Time (ms),Avg Memory (MB)
    10000,LineByLineSearcher,2.000888188680013,0.0013020833333333333
    10000,MMapSearcher,2.666632334391276,0.5690104166666666
    10000,BufferedChunkSearcher,1.998265584309896,0.032552083333333336
	...

## Notes

    Designed for Linux-based environments (e.g., Ubuntu)

    Results may vary depending on system memory and disk I/O

    You can modify the SEARCH_TERM and file sizes in algo_speed_comp.py

For instructions on how to run the server as a background Linux daemon using systemd, see [Running the Server as a Linux Daemon](./INSTALL.md)

Alternatively, you can run it manually for testing [](./REPRODUCE.md)

## Author

Stephen Muteti
