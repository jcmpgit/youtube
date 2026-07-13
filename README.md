# YouTube

AI model evaluation and benchmarking tools.

## Overview

This repository contains benchmark systems for evaluating language model performance across multiple dimensions.

### Benchmark Runner

A complete benchmark system in `benchmark/` that runs AI model inference tests and generates HTML performance reports.

**Features:**
- Execute prompts against multiple model configurations
- Collect performance metrics (latency, throughput, token generation)
- **Auto-extract generated code as runnable files** (HTML, JS, CSS)
- Generate interactive HTML reports
- Compare models across test scenarios

```bash
# Quick start with LM Studio
python3 benchmark/benchmark_runner.py --port 1234

# Generate report from results
python3 benchmark/report_generator.py benchmark_results/results_*.json
```

Extracted artifacts are saved to `benchmark_results/artifacts/{model_config}/{prompt_name}/` for easy viewing and comparison.

See [benchmark docs](docs/README_BENCHMARKS.md) for full details.

### Benchmark Overviews

- **Agency Benchmark** — [`agency-benchmark-overview.html`](agency-benchmark-overview.html) — Evaluates tool-calling capability (22 scenarios, 8 simulated tools)
- **Performance Benchmark** — [`performance-benchmark-overview.html`](performance-benchmark-overview.html) — Performance comparison across models

## Project Structure

```
benchmark/              # Benchmark runner scripts & config
  ├── benchmark_runner.py
  ├── report_generator.py
  ├── quickstart.py
  ├── benchmark.sh
  ├── model-configs.ini
  └── prompts/
benchmark_results/      # Raw JSON results (gitignored)
  └── artifacts/        # Extracted code files by model (gitignored)
      └── {model_config}/
          └── {prompt_name}/
              ├── index.html
              └── ...
reports/                # Generated HTML reports (gitignored)
docs/                   # Documentation
```

## Requirements

- Python 3.8+
- A running LLM inference server (LM Studio, llama.cpp, Ollama, etc.)
