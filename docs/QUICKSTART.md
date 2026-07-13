# Getting Started with Benchmark Suite

## 30-Second Setup

### Option A: Using LM Studio (Easiest)

```bash
# 1. Setup virtual environment (one-time)
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
pip install -r benchmark/requirements.txt

# 2. Activate venv (every session)
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows

# 3. Start LM Studio
#    - Open LM Studio app
#    - Click "Local Server" tab
#    - Select a model
#    - Click "Start Server" (wait for green status)

# 4. Run benchmarks (in terminal)
python3 benchmark/benchmark_runner.py --port 1234

# 5. Generate report
python3 benchmark/report_generator.py benchmark_results/results_*.json
open reports/benchmark_report.html
```

### Option B: Using llama.cpp

```bash
# 1. Setup virtual environment (one-time)
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
pip install -r benchmark/requirements.txt

# 2. Activate venv (every session)
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows

# 3. Start model server (in one terminal)
python -m llama_cpp.server --model-path /path/to/gemma-4-12b-it.gguf

# 4. Run benchmarks (in another terminal)
python3 benchmark/benchmark_runner.py

# 5. Generate report
python3 benchmark/report_generator.py benchmark_results/results_*.json
open reports/benchmark_report.html
```

## What You Just Did

1. **benchmark/benchmark_runner.py** - Ran 1 model profile × all 11 prompts (11 tests total) against your model
2. **benchmark/report_generator.py** - Analyzed results and created an interactive HTML dashboard
3. **Results** - Stored in `benchmark_results/` directory

> **Note:** By default, only the **first** model profile runs. With LM Studio (one model at a time), that's exactly right. Use `--all-profiles` to test all 96 configs (for batch/remote setups).

## File Descriptions

### Main Files
- **benchmark/benchmark_runner.py** - Core benchmark executor (420 lines)
  - Connects to llama-server
  - Loads prompts and model configs
  - Records timing and token metrics
  - Handles errors and timeouts

- **benchmark/report_generator.py** - Report generator (390 lines)
  - Analyzes raw JSON results
  - Computes statistics (mean, median, stdev, etc.)
  - Generates beautiful interactive HTML reports

- **benchmark/quickstart.py** - Interactive helper (280 lines)
  - Menu-driven benchmark runner
  - Setup validation
  - Easy model/prompt selection

- **benchmark/benchmark.sh** - Bash quick-start (180 lines)
  - One-command setup and run
  - Checks dependencies
  - Validates llama-server

### Configuration
- **benchmark/model-configs.ini** - Model profiles and settings
  - Multiple Gemma-4-12B variants
  - Quantization options (Q4, Q8, BF16)
  - GPU acceleration settings

- **benchmark/prompts/** - 11 benchmark test categories
  - Simulation tasks (maze, physics, games)
  - Application building (kanban, expense tracker)
  - Reasoning and logic puzzles

## Common Workflows

### Quick Test (5 min)
```bash
python benchmark_runner.py --prompt reasoning --port 1234
python report_generator.py benchmark_results/results_*.json
open benchmark_report.html
```

### Full Benchmark (varies by model)
```bash
python benchmark_runner.py --port 1234
python report_generator.py benchmark_results/results_*.json
open benchmark_report.html
```

### Compare Two Models
```bash
# Test model 1 on LM Studio (load Model A, then run)
python benchmark_runner.py --port 1234
mv benchmark_results/results_*.json results_model_a.json
python report_generator.py results_model_a.json --output report_model_a.html

# Test model 2 on LM Studio (load Model B, then run)
python benchmark_runner.py --port 1234
mv benchmark_results/results_*.json results_model_b.json
python report_generator.py results_model_b.json --output report_model_b.html

# Compare reports side-by-side in browser
open report_model_a.html report_model_b.html
```

### Test Single Prompt
```bash
python benchmark_runner.py --prompt agent-maze --port 1234
```

## Interpreting Results

### Success Rate
- **100%** - Model handled all test cases
- **0%** - Connection/timeout errors
- **50-99%** - Partial failures (check error messages)

### Duration (seconds)
- Average time to complete each prompt
- Depends on: model size, GPU, context length
- Target: < 30s for generation

### Tokens Generated
- How much output the model produced
- Higher = more complete responses
- Typical: 200-4000 tokens per prompt

### First Token Latency (milliseconds)
- Time to first output token
- Indicates prefill performance
- Lower = more responsive
- Target: < 500ms

## Troubleshooting

### "llama-server not running"
```bash
# Make sure server is started
python -m llama_cpp.server --model-path /path/to/model.gguf

# Or using llama-server directly
llama-server -m /path/to/model.gguf -c 65536 -ngl 999 -p 8080
```

### "Connection refused"
- Check server is on correct port (default 8080)
- Use `--host` and `--port` flags if different
- Verify firewall isn't blocking localhost

### "Timeout errors"
- Model is too slow for default timeout (300s)
- Edit `benchmark_runner.py` line ~130: increase `timeout` parameter
- Or increase max_tokens (line ~140) to generate less

### "Out of memory (OOM)"
- Reduce context length in model config
- Use smaller quantization variant
- Run tests individually instead of batch

## What's Next?

### Generate More Metrics
Edit `benchmark_runner.py` to collect additional data:
- Memory usage
- GPU utilization
- Quality scoring (task-specific)
- Custom metrics

### Running Both Servers for Comparison
```bash
# Terminal 1: Start LM Studio
# (Open app → Local Server tab → Select model → Start Server)

# Terminal 2: Start llama.cpp (different model)
python -m llama_cpp.server --model-path /path/to/other-model.gguf

# Terminal 3: Run first benchmark (LM Studio)
python3 benchmark_runner.py --port 1234
mv benchmark_results/results_*.json results_lm_studio.json

# Terminal 4: Run second benchmark (llama.cpp)
python3 benchmark_runner.py --port 8080
mv benchmark_results/results_*.json results_llama_cpp.json

# Generate reports
python3 report_generator.py results_lm_studio.json --output report_lm_studio.html
python3 report_generator.py results_llama_cpp.json --output report_llama_cpp.html

# Compare in browser
open report_lm_studio.html report_llama_cpp.html
```

### Expand Prompts
Add new test cases to `prompts/` directory:
```bash
echo "Your benchmark prompt..." > prompts/custom-test.txt
python benchmark_runner.py --prompt custom-test
```

### Integrate with CI/CD
Run benchmarks in your test pipeline:
```yaml
# Example GitHub Actions
- name: Run Benchmarks
  run: |
    python benchmark_runner.py
    python report_generator.py benchmark_results/results_*.json
```

### Track Performance Over Time
Keep historical results:
```bash
# Each run automatically timestamps results
python benchmark_runner.py
# Creates: benchmark_results/results_20240115_143022.json

# Generate multiple reports for comparison
python report_generator.py results_20240115_143022.json --output report_jan15.html
python report_generator.py results_20240116_091523.json --output report_jan16.html
```

## Key Features

✅ **Easy Setup** - One command to start  
✅ **Comprehensive Metrics** - Timing, throughput, latency  
✅ **Beautiful Reports** - Interactive HTML dashboards  
✅ **Flexible Configuration** - Test any model/prompt combo  
✅ **Error Handling** - Timeouts, connection issues  
✅ **Performance Focus** - Measures what matters  
✅ **Scalable** - Works with 7B to 70B+ models  

## Reference

| Command | Purpose |
|---------|---------|
| `python quickstart.py` | Interactive menu |
| `python quickstart.py validate` | Check setup |
| `python benchmark_runner.py` | Run all benchmarks |
| `python benchmark_runner.py --prompt reasoning` | Test one prompt |
| `python report_generator.py results.json` | Generate HTML report |
| `bash benchmark.sh` | Bash quick-start |
| `pip install -r requirements.txt` | Install dependencies |

## Questions?

See **README_BENCHMARKS.md** for detailed documentation, including:
- Advanced command-line options
- Model configuration details
- Custom metrics and scoring
- Batch automation examples
