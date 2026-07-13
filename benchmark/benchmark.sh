#!/bin/bash
# Quick setup and run script for benchmark suite

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check Python
print_header "Checking Python Installation"
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found"
    echo "Install Python 3.8+ from https://www.python.org"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
print_success "$PYTHON_VERSION found"

# Check required files
print_header "Checking Files"
for file in benchmark/benchmark_runner.py benchmark/report_generator.py benchmark/model-configs.ini benchmark/prompts; do
    if [ -e "$file" ]; then
        print_success "$file found"
    else
        print_error "$file not found"
        exit 1
    fi
done

# Install Python dependencies
print_header "Installing Dependencies"
python3 -m pip install -q requests --upgrade 2>/dev/null || python3 -m pip install requests --upgrade
print_success "Dependencies installed"

# Check server
print_header "Checking llama-server"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    print_success "llama-server is running on localhost:8080"
else
    print_warning "llama-server not found on localhost:8080"
    echo ""
    echo "To start llama-server, run one of the following:"
    echo ""
    echo "Option 1 - Using llama-cpp-python (recommended):"
    echo "  python -m llama_cpp.server --model-path /path/to/model.gguf"
    echo ""
    echo "Option 2 - Using llama-server directly:"
    echo "  llama-server -m /path/to/model.gguf -c 65536 -ngl 999 -p 8080"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# List available options
print_header "Available Models"
echo "Model configurations found in benchmark/model-configs.ini:"
grep '^\[' benchmark/model-configs.ini | grep -v '^\[\*\]' | head -5
echo "... (and more)"
echo ""

# Ask what to run
echo "What would you like to do?"
echo ""
echo "1) Run quick benchmark (reasoning prompt, first model)"
echo "2) Run full benchmark"
echo "3) List available profiles and prompts"
echo "4) View documentation"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        print_header "Running Quick Benchmark"
        PROFILES=$(grep '^\[' benchmark/model-configs.ini | grep -v '^\[\*\]' | head -1 | tr -d '[]')
        echo "Using profile: $PROFILES"
        python3 benchmark/benchmark_runner.py --profile "$PROFILES" --prompt reasoning
        
        # Generate report
        print_header "Generating Report"
        LATEST=$(ls -t benchmark_results/results_*.json 2>/dev/null | head -1)
        if [ -n "$LATEST" ]; then
            python3 benchmark/report_generator.py "$LATEST"
            print_success "Report generated: reports/benchmark_report.html"
            echo "Open it in your browser to view results"
        fi
        ;;
    2)
        print_header "Running Full Benchmark"
        python3 benchmark/benchmark_runner.py
        
        # Generate report
        print_header "Generating Report"
        LATEST=$(ls -t benchmark_results/results_*.json 2>/dev/null | head -1)
        if [ -n "$LATEST" ]; then
            python3 benchmark/report_generator.py "$LATEST"
            print_success "Report generated: reports/benchmark_report.html"
        fi
        ;;
    3)
        print_header "Available Profiles"
        grep '^\[' benchmark/model-configs.ini | grep -v '^\[\*\]' | tr -d '[]'
        
        print_header "Available Prompts"
        ls -1 benchmark/prompts/ | sed 's/\.txt$//'
        ;;
    4)
        less docs/README_BENCHMARKS.md
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

print_header "Done!"
