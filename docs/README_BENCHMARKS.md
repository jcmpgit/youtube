# Benchmark Runner & Report Generator

A complete system for running AI model benchmarks against your prompts and generating comprehensive performance reports.

## Overview

This system lets you:
- ✅ Execute benchmark prompts against different model configurations
- 📊 Collect performance metrics (latency, throughput, token generation)
- 📈 Generate interactive HTML reports
- 🎯 Compare models across multiple test scenarios

## Setup

### Prerequisites

1. **Python 3.8+**
2. **Running llama-server** instance with your model loaded
3. **Required Python packages**:

```bash
pip install requests
```

### Install

The benchmark tools are in the `benchmark/` directory:
- `benchmark/benchmark_runner.py` - Main test executor
- `benchmark/report_generator.py` - HTML report creator

## Quick Start

### 0. Setup Virtual Environment (One-Time)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

### 1. Activate venv (Every Session)

```bash
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
```

### 2. Start Your Model Server

#### Option A: LM Studio (Recommended - GUI)

1. Open **LM Studio** desktop application
2. Click **"Local Server"** tab on the left
3. Select your model from the library dropdown
4. Click **"Start Server"** button
5. Wait for green status indicator (shows port and model loaded)

Port: **1234** (default)

#### Option B: llama.cpp (Command Line)

```bash
# Using llama-cpp-python
python -m llama_cpp.server --model-path /path/to/model.gguf

# Or using llama-server directly  
llama-server \
  -m /path/to/gemma-4-12b-it-Q4_K_M.gguf \
  -mmproj /path/to/mmproj-BF16.gguf \
  -c 65536 -ngl 999 --flash-attn -p 8080
```

Port: **8080** (default)

### 3. Run Benchmarks

In a new terminal:

```bash
# With LM Studio (port 1234) - 1 profile × all prompts (11 tests)
python3 benchmark/benchmark_runner.py --port 1234

# With llama.cpp (port 8080) - 1 profile × all prompts (11 tests)
python3 benchmark/benchmark_runner.py

# Run specific profile only
python3 benchmark/benchmark_runner.py --profile gemma4-12b-q4_k_m --port 1234

# Run specific prompt only
python3 benchmark/benchmark_runner.py --prompt reasoning --port 1234

# Combine filters
python3 benchmark/benchmark_runner.py --profile gemma4-12b-q4_k_m --prompt agent-maze --port 1234

# Run against ALL 96 profiles (batch/remote only - not for LM Studio)
python3 benchmark/benchmark_runner.py --all-profiles

# Custom server location (not localhost)
python3 benchmark/benchmark_runner.py --host 192.168.1.100 --port 8080
```

**Note:** By default, only the first model profile runs — perfect for LM Studio where you load one model at a time. Use `--profile NAME` to pick a different one, or `--all-profiles` for the full suite.

### 4. Generate Report

```bash
# Generate HTML report from results
python3 benchmark/report_generator.py benchmark_results/results_20240115_143022.json

# Save to custom location
python3 benchmark/report_generator.py benchmark_results/results_20240115_143022.json --output reports/my_report.html
```

Then open the HTML file in your browser.

## Command Line Options

### benchmark_runner.py

```
--profile PROFILE         Test specific model profile (default: first profile only)
--all-profiles            Run against every profile in model-configs.ini
--prompt PROMPT           Test specific prompt (default: all)
--config FILE             Path to model config file (default: benchmark/model-configs.ini)
--prompts-dir DIR        Path to prompts directory (default: benchmark/prompts)
--prompts-dir DIR         Path to prompts directory (default: prompts)
--output-dir DIR          Output directory for results (default: benchmark_results)
--host HOST              llama-server host (default: localhost)
--port PORT              llama-server port (default: 8080)
```

### report_generator.py

```
RESULTS_FILE            Path to benchmark results JSON file
--output FILE           Output HTML file (default: benchmark_report.html)
```

## Switching Between Servers

The benchmark runner supports any OpenAI-compatible API. Here's how to use different servers:

### LM Studio (Easiest)
1. Open LM Studio app
2. Click "Local Server" → Select model → "Start Server"
4. Run: `python3 benchmark/benchmark_runner.py --port 1234`

### llama.cpp  
1. Start: `python -m llama_cpp.server --model-path /path/to/model.gguf`
2. Run: `python3 benchmark/benchmark_runner.py` (or `--port 8080` explicitly)

### Ollama
1. Start: `ollama run gemma`
2. Run: `python3 benchmark/benchmark_runner.py --port 11434`

### Remote Server
```bash
python3 benchmark/benchmark_runner.py --host 192.168.1.100 --port 8000
```

## Output

### Results JSON

Each benchmark run saves a JSON file with detailed results:

```json
[
  {
    "prompt_name": "reasoning",
    "model_config": "gemma4-12b-q4_k_m",
    "start_time": "2024-01-15T14:30:22.123456",
    "end_time": "2024-01-15T14:30:47.654321",
    "duration_seconds": 25.531,
    "status": "success",
    "tokens_generated": 312,
    "first_token_latency_ms": 145.2,
    "response_text": "..."
  }
]
```

### HTML Report

The generated report includes:
- **Overview**: Total tests, pass rate, success/failure counts
- **Performance Metrics**: Duration, tokens, latency statistics
- **By Model**: Success rate and performance for each model profile
- **By Prompt**: Success rate and performance for each prompt type

## Model Configurations

All model profiles are defined in `benchmark/model-configs.ini`. Each profile includes:

- Model file path and quantization type
- Context window size
- GPU layer offloading settings
- Cache quantization options
- Other llama-server parameters

Available profiles: (see benchmark/model-configs.ini)
- `gemma4-12b` - Base model
- `gemma4-12b-q8` - 8-bit quantization
- `gemma4-12b-q4_k_m` - 4-bit quantization (K-means)
- `gemma4-12b-bf16` - Brain Float 16-bit
- And more...

## Prompts

11 benchmark prompt categories:

| Prompt | Type | Description |
|--------|------|-------------|
| `agent-maze` | Simulation | Build a slime-mold pathfinding simulation |
| `sand-physics` | Simulation | Physics-based sand simulation |
| `breakout` | Game | Build a breakout/brick breaker game |
| `driving-2d` | Game | 2D driving game simulation |
| `dungeon-game` | Game | Text-based dungeon exploration game |
| `kanban` | Application | Build a Kanban board application |
| `expense-tracker` | Application | Build an expense tracking app |
| `fake-desktop` | Application | Simulate a desktop environment |
| `reasoning` | Logic | Logic puzzles and reasoning challenges |
| `adherence` | QA | Test instruction adherence |
| `memory-match` | Game | Pattern matching memory game |

## Metrics Explained

### Duration
Total time from request start to completion (seconds)

### Tokens Generated
Total number of tokens produced by the model

### First Token Latency
Time from request to when the first token appears (milliseconds)
- Indicates responsiveness/prefill speed
- Lower is better

### Success Rate
Percentage of tests that completed without error
- "Error" includes timeouts and connection failures
- Doesn't measure correctness of responses

## Example Workflow

### Using LM Studio

```bash
# 1. Open LM Studio → Local Server tab → Select model → Start Server

# 2. Quick test on one prompt (in terminal)
python benchmark_runner.py --port 1234 --prompt reasoning

# 3. Run full benchmark on the loaded model
python benchmark_runner.py --port 1234

# 4. Generate a report
python report_generator.py benchmark_results/results_*.json --output report.html

# 5. Open report.html in your browser
```

### Using llama.cpp

```bash
# 1. Start the server with a specific model
llama-server -m gemma-4-12b-q4_k_m.gguf -c 65536 -ngl 999 -p 8080

# 2. Quick test on one prompt
python benchmark_runner.py --prompt reasoning

# 3. Run full benchmark on this model
python benchmark_runner.py

# 4. Generate a report
python report_generator.py benchmark_results/results_*.json --output report.html

# 5. Open report.html in your browser
```

Both run the **first model profile × all 11 prompts** by default. Use `--profile NAME` to target a specific profile.

## Troubleshooting

### llama-server not running error

```
❌ llama-server not running at http://localhost:8080
```

**Fix**: 
1. Ensure llama-server is started
2. Check correct host/port with `--host` and `--port` flags
3. Verify server is listening: `curl http://localhost:8080/health`

### Timeout errors

Increase timeout for slow models:
- Edit `benchmark_runner.py`, line ~130: `LlamaServerClient(host, port, timeout=600)`
- Or wait longer between requests

### Out of Memory (OOM)

- Reduce context window in model-configs.ini
- Use a smaller quantization (q4_0, q4_k_m instead of q8, bf16)
- Run tests individually with `--prompt` flag

### JSON decode errors

These usually indicate malformed llama-server responses. Try:
1. Restarting llama-server
2. Checking server logs for errors
3. Verifying model is compatible with your llama.cpp version

## Advanced Usage

### Custom Prompts

Add new prompts to the `benchmark/prompts/` directory. Any `.txt` file will be included in benchmarks:

```bash
echo "Your custom prompt here" > prompts/my-test.txt
python benchmark_runner.py --prompt my-test
```

### Batch Runs

Test multiple models sequentially:

```bash
for model in gemma4-12b-q8 gemma4-12b-q4_k_m; do
  echo "Testing $model..."
  python benchmark_runner.py --profile $model
done
```

### Compare Reports

Generate reports for each model and compare side-by-side:

```bash
python report_generator.py results_q8.json --output report_q8.html
python report_generator.py results_q4.json --output report_q4.html
# Open both in browser
```

## Performance Tips

1. **Reduce max_tokens** in `benchmark_runner.py` (line ~140) for faster tests
2. **Use GPU acceleration** - set `ngl 999` in model config
3. **Increase batch size** - modify llama-server settings
4. **Profile gradually** - test one model first, then scale

## File Structure

```
.
├── benchmark/                   # Benchmark scripts & config
│   ├── benchmark_runner.py      # Main test executor
│   ├── report_generator.py      # HTML report generator
│   ├── quickstart.py            # Interactive menu helper
│   ├── benchmark.sh             # Bash launcher
│   ├── requirements.txt         # Python dependencies
│   ├── model-configs.ini        # Model configurations
│   └── prompts/                 # Test prompts
│       ├── reasoning.txt
│       ├── agent-maze.txt
│       └── ...
├── benchmark_results/           # Raw JSON results (auto-created)
│   ├── results_20240115_143022.json
├── reports/                     # Generated HTML reports
│   └── benchmark_report.html
├── docs/                        # Documentation
│   ├── README_BENCHMARKS.md
│   ├── QUICKSTART.md
│   ├── COMMAND_REFERENCE.md
│   └── SETUP_COMPLETE.md
└── venv/                        # Python virtual environment
```

## License

Part of Luke's Dev Lab benchmark suite.
