# REPRODUCE.md

This guide details how to reproduce the benchmark results, plots, and server tests for the task.

---

The steps below can be carried out from the extracted zip file. There is no particular path requirements for the project for reproducing the results.


## Prerequisites

### 1. Python Virtual Environment

Ensure you have Python 3.9+ installed.

Create and activate a Python virtual environment inside the project root directory. Install
the required python libraries as below:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### SSL SETUP
Follow [SSL SETUP GUIDE](./SSL_SETUP.md) to geberate the ssl files for the server.

---


## 2. Benchmark Search Algorithm Performance

Benchmark the implemented search algorithms:

```bash
source .venv/bin/activate
python -m tests.algo_speed_comp
```

This will:
- Benchmark all search algorithms (line-by-line, cached, mmap, regex, trie, etc.)
- Save performance results to `utils/search_benchmark_results.csv`

The generated CSV (utils/search_benchmark_results.csv) looks like:
    File Size,Algorithm,Avg Time (ms),Avg Memory (MB)
    10000,LineByLineSearcher,2.000888188680013,0.0013020833333333333
    10000,MMapSearcher,2.666632334391276,0.5690104166666666
    10000,BufferedChunkSearcher,1.998265584309896,0.032552083333333336
    ...

---

## 3. Plot Algorithm Performance

Generate visual comparisons between search methods:

```bash
source .venv/bin/activate
python -m utils.plot_benchmark
```

Outputs:
- `utils/algorithm_performance_comp.png` (speed comparison)
- `utils/algorithm_memory_usage_comp.png` (memory usage comparison)

---

## 4. Run Server and Perform Client Search

**Start the server:**

```bash
source .venv/bin/activate
python run_server.py
```

**In a second terminal, run the client:**

```bash
source .venv/bin/activate
python -m client.client
```

The client connects securely via SSL, sends search queries, and receives responses from the server.

The line `Algorithmic Sciences loves speed` exists in the search file. Try it!

---

## 5. Server Load Testing (QPS Simulation)

To simulate increasing client load:

```bash
source .venv/bin/activate
python -m client.load_test_client
```

This will:
- Generate `utils/load_test_results.csv`
- Collect latency and error rates across increasing QPS (queries per second)

---

## 6. Plot Server Load Analysis

Visualize server performance under load:

```bash
source .venv/bin/activate
python -m utils.plot_benchmark_analysis
```

Outputs:
- `utils/latency_vs_qps.png` (latency vs QPS)
- `utils/errors_vs_qps.png` (errors vs QPS)
- `utils/qps_thresholds.png` (acceptable performance thresholds)

---

## 7. Run Unit Tests and Code Quality Checks

Ensure all unit tests pass and the codebase adheres to quality standards:

```bash
source .venv/bin/activate
pytest
flake8 .
mypy .
```

Unit tests are located under the `tests/` directory and validate both functionality and edge cases.

---

## Notes

- All commands assume you are inside the project root unless otherwise specified.
- If you encounter permission errors during SSL generation, consider prefixing commands with `sudo`.
- The system is designed to be fully offline-capable after dependencies are installed.
