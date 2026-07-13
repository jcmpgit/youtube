# Benchmark Suite - Quick Command Reference

## Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# OR
venv\Scripts\activate       # Windows

# Install Python dependencies
pip install -r requirements.txt

# Make scripts executable (one-time)
chmod +x benchmark.sh
```

### Next Time
```bash
# Just activate the venv:
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
```

## Starting Model Server

### LM Studio (Recommended - GUI)
```bash
# 1. Open LM Studio app
# 2. Click "Local Server" tab
# 3. Select model from dropdown
# 4. Click "Start Server"
# Default port: 1234
```

### llama.cpp (Command Line)
```bash
# Using llama-cpp-python (recommended)
python -m llama_cpp.server --model-path /path/to/model.gguf
# Default port: 8080

# Using llama-server directly
llama-server \
  -m /path/to/gemma-4-12b-it-Q4_K_M.gguf \
  -mmproj /path/to/mmproj-BF16.gguf \
  -c 65536 -ngl 999 -p 8080
```

### Remote Server (Ollama, RunPod, etc.)
```bash
# Connect to server on different host/port
python3 benchmark/benchmark_runner.py --host 192.168.1.100 --port 8000
```

## Running Benchmarks

```bash
# With LM Studio (port 1234) - runs first model only (default)
python3 benchmark/benchmark_runner.py --port 1234

# With llama.cpp (port 8080) - runs first model only (default)
python3 benchmark/benchmark_runner.py

# Specific model profile (recommended for LM Studio)
python3 benchmark/benchmark_runner.py --profile gemma4-12b-q4_k_m --port 1234

# Specific prompt only
python3 benchmark/benchmark_runner.py --prompt reasoning --port 1234

# Combine profile + prompt
python3 benchmark/benchmark_runner.py --profile gemma4-12b-q4_k_m --prompt agent-maze --port 1234

# Run against ALL 96 configs (only useful with multiple GPU/remote)
python3 benchmark/benchmark_runner.py --all-profiles

# Remote server (not localhost)
python3 benchmark/benchmark_runner.py --host 192.168.1.100 --port 8000
```

## Generating Reports

```bash
# Generate HTML report (supports glob patterns)
python3 benchmark/report_generator.py benchmark_results/results_*.json

# Specify output filename (saved to reports/ folder by default)
python3 benchmark/report_generator.py benchmark_results/results_*.json --output reports/my_report.html

# Load multiple specific files
python3 benchmark/report_generator.py benchmark_results/results_*.json

# Then open in browser:
open reports/benchmark_report.html   # macOS
xdg-open reports/benchmark_report.html  # Linux
start reports/benchmark_report.html  # Windows
```

## Available Models (from benchmark/model-configs.ini)

```
gemma4-12b                (Base model)
gemma4-12b-q8            (8-bit quantization)
gemma4-12b-q4_k_m        (4-bit K-means quantization)
gemma4-12b-qat           (Quantization-Aware Training)
gemma4-12b-qat-q4_0      (QAT + 4-bit)
gemma4-12b-bf16          (Brain Float 16-bit)
```

List all: `grep '^\[' benchmark/model-configs.ini | grep -v '^\[\*\]'`

## Available Prompts (11 total)

```
reasoning               Logic puzzles
agent-maze             Slime mold pathfinding simulation
sand-physics           Physics-based sand simulation
dungeon-game           Text-based dungeon game
breakout               Breakout/brick breaker game
driving-2d             2D driving simulation
kanban                 Kanban board application
expense-tracker        Expense tracking application
fake-desktop           Desktop environment simulator
memory-match           Pattern matching memory game
adherence              Instruction adherence testing
```

List all: `ls benchmark/prompts/ | sed 's/\.txt$//'`

## Common Workflows

### Quick Test (5 minutes)
```bash
python3 benchmark/benchmark_runner.py --prompt reasoning
python3 benchmark/report_generator.py benchmark_results/results_*.json
open reports/benchmark_report.html
```

### Full Benchmark (varies by model size)
```bash
python3 benchmark/benchmark_runner.py
python3 benchmark/report_generator.py benchmark_results/results_*.json
open reports/benchmark_report.html
```

### Compare Two Models
```bash
# Test model 1
python3 benchmark/benchmark_runner.py --profile gemma4-12b-q4_k_m
cp benchmark_results/results_*.json results_q4.json

# Test model 2  
python3 benchmark/benchmark_runner.py --profile gemma4-12b-q8
cp benchmark_results/results_*.json results_q8.json

# Generate reports
python3 benchmark/report_generator.py results_q4.json --output reports/report_q4.html
python3 benchmark/report_generator.py results_q8.json --output reports/report_q8.html

# Compare in browser
open reports/report_q4.html reports/report_q8.html
```

### Batch Testing All Models
```bash
for profile in $(grep '^\[' benchmark/model-configs.ini | grep -v '\[\*\]' | tr -d '[]'); do
  echo "Testing $profile..."
  python3 benchmark/benchmark_runner.py --profile "$profile"
done

# Generate combined report from all results
python3 benchmark/report_generator.py benchmark_results/results_*.json
```

### Add Custom Prompt
```bash
# Create new test prompt
echo "Your custom prompt..." > benchmark/prompts/custom.txt

# Test it
python3 benchmark/benchmark_runner.py --prompt custom
```

## Help Commands

```bash
# Full help for all options
python3 benchmark/benchmark_runner.py --help
python3 benchmark/report_generator.py --help
python3 benchmark/quickstart.py help

# Validate setup
python3 benchmark/quickstart.py validate
```

## Output Files

```
benchmark_results/          # Raw JSON results (auto-timestamped)
├── results_20240115_143022.json
reports/                    # Generated HTML reports
├── benchmark_report.html
docs/                       # Documentation
├── COMMAND_REFERENCE.md
├── QUICKSTART.md
├── README_BENCHMARKS.md
└── SETUP_COMPLETE.md
benchmark/                  # Benchmark scripts & config
├── benchmark_runner.py
├── report_generator.py
├── quickstart.py
├── benchmark.sh
├── requirements.txt
├── model-configs.ini
└── prompts/
    ├── reasoning.txt
    ├── agent-maze.txt
    └── ...
```
├── results_20240115_143523.json    # Multiple runs saved separately
└── benchmark_report.html           # Final HTML report
```

## Interpreting Results

| Metric | Good | Bad | Notes |
|--------|------|-----|-------|
| Success Rate | 100% | < 50% | Timeouts/errors |
| Duration | < 30s | > 60s | Time per prompt |
| Tokens | 500+ | < 100 | Output completeness |
| Latency | < 500ms | > 1000ms | First token responsiveness |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "llama-server not running" | Start model server first |
| "Connection refused" | Check host/port with `--host` `--port` |
| "Module not found: requests" | `pip3 install requests` |
| "Timeout errors" | Increase timeout with `--timeout 900` or use a faster model |
| "Out of memory" | Reduce context length or use smaller quantization |
| "0 tokens reported" | Streaming format mismatch — fixed in latest benchmark_runner.py |
| "Report generator: unrecognized arguments" | Use glob pattern: `report_generator.py benchmark_results/results_*.json` |

## Environment Info

Show Python/environment details:
```bash
python3 --version
which python3
python3 -c "import sys; print(sys.executable)"
```

## File Structure

```
youtube/
├── benchmark_runner.py       ← Run benchmarks
├── report_generator.py       ← Generate reports
├── quickstart.py             ← Interactive helper
├── benchmark.sh              ← Bash launcher
├── model-configs.ini         ← Model configs
├── prompts/                  ← Test prompts (11 files)
├── requirements.txt          ← Dependencies
├── benchmark_results/        ← Output (auto-created)
├── QUICKSTART.md             ← Quick reference
├── README_BENCHMARKS.md      ← Full docs
└── COMMAND_REFERENCE.md      ← This file
```

## Performance Tips

- Use `--prompt reasoning` for 5-min validation
- GPU acceleration: ensure `ngl 999` in config
- Batch tests sequentially: one model at a time
- Check server logs if tests timeout

## Next Steps

1. Read `QUICKSTART.md` (5 min)
2. Run `bash benchmark.sh`
3. Generate and view report
4. Compare models with multiple runs

## Server Comparison

| Feature | LM Studio | llama.cpp |
|---------|-----------|-----------|
| **Launch** | GUI app | Command line |
| **Port** | 1234 | 8080 |
| **Model Loading** | Dropdown selector | CLI arguments |
| **Ease of Use** | Very easy | Moderate |
| **Control** | Limited | Full |

### Create Aliases for Quick Access

```bash
# Add to ~/.zshrc or ~/.bashrc
alias bench-studio="python3 benchmark_runner.py --port 1234"
alias bench-llama="python3 benchmark_runner.py --port 8080"
alias bench-quick="python3 benchmark_runner.py --prompt reasoning --port 1234"
```

Then just run:
```bash
bench-studio   # Use LM Studio
bench-llama    # Use llama.cpp
bench-quick    # Quick test (5 min)
```

---

**Pro Tip:** Bookmark this file for quick reference! 🚀
