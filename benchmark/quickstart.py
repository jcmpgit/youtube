#!/usr/bin/env python3
"""
Quick Start Helper for Benchmark Suite
Helps set up and run benchmarks interactively
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import requests
        return True
    except ImportError:
        print("❌ Missing dependency: requests")
        print("   Install with: pip install requests")
        return False

def check_server(host: str = "localhost", port: int = 8080) -> bool:
    """Check if llama-server is running"""
    try:
        import requests
        response = requests.get(f"http://{host}:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def list_profiles():
    """List available model profiles"""
    from benchmark_runner import ConfigParser
    parser = ConfigParser("benchmark/model-configs.ini")
    profiles = parser.get_profiles()
    
    print("Available Model Profiles:")
    print("-" * 40)
    for i, profile in enumerate(profiles, 1):
        print(f"{i:2d}. {profile}")
    print()
    return profiles

def list_prompts():
    """List available prompts"""
    prompts_dir = Path("benchmark/prompts")
    prompts = sorted([f.stem for f in prompts_dir.glob("*.txt")])
    
    print("Available Prompts:")
    print("-" * 40)
    for i, prompt in enumerate(prompts, 1):
        print(f"{i:2d}. {prompt}")
    print()
    return prompts

def run_benchmark_interactive():
    """Interactive benchmark runner"""
    
    print_header("🎯 Benchmark Runner - Interactive Mode")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check server
    print("Checking for llama-server...", end=" ", flush=True)
    if not check_server():
        print("❌\n")
        print("llama-server is not running!")
        print("\nTo start llama-server:")
        print("  llama-server -m <model-path> -c 65536 -ngl 999 -p 8080")
        print("\nOr use Python:")
        print("  python -m llama_cpp.server --model-path <model-path>")
        return False
    print("✓\n")
    
    # Get options
    profiles = list_profiles()
    prompts = list_prompts()
    
    print("Select what to benchmark:")
    print("1. All profiles × All prompts (full suite)")
    print("2. Single profile × All prompts")
    print("3. All profiles × Single prompt")
    print("4. Single profile × Single prompt")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    profile_arg = ""
    prompt_arg = ""
    
    if choice == "1":
        run_all = True
    elif choice == "2":
        idx = input(f"Select profile (1-{len(profiles)}): ").strip()
        try:
            profile_arg = f"--profile {profiles[int(idx) - 1]}"
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return False
    elif choice == "3":
        idx = input(f"Select prompt (1-{len(prompts)}): ").strip()
        try:
            prompt_arg = f"--prompt {prompts[int(idx) - 1]}"
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return False
    elif choice == "4":
        pidx = input(f"Select profile (1-{len(profiles)}): ").strip()
        qidx = input(f"Select prompt (1-{len(prompts)}): ").strip()
        try:
            profile_arg = f"--profile {profiles[int(pidx) - 1]}"
            prompt_arg = f"--prompt {prompts[int(qidx) - 1]}"
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return False
    else:
        print("❌ Invalid choice")
        return False
    
    # Run benchmark
    print_header("Running Benchmark")
    
    cmd = f"python benchmark_runner.py {profile_arg} {prompt_arg}".strip()
    print(f"Command: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("\n❌ Benchmark failed")
        return False
    
    # Find latest results file
    results_dir = Path("benchmark_results")
    if not results_dir.exists():
        print("❌ Results directory not found")
        return False
    
    results_files = sorted(results_dir.glob("results_*.json"))
    if not results_files:
        print("❌ No results files found")
        return False
    
    latest_results = results_files[-1]
    
    # Generate report
    print_header("Generating Report")
    
    report_name = f"report_{latest_results.stem}.html"
    cmd = f"python report_generator.py {latest_results} --output {report_name}"
    print(f"Command: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("\n❌ Report generation failed")
        return False
    
    print_header("✓ Complete!")
    print(f"Results: {latest_results}")
    print(f"Report:  {report_name}")
    print(f"\nOpen {report_name} in your browser to view results")
    return True

def validate_setup():
    """Validate benchmark setup"""
    print_header("🔍 Validating Setup")
    
    issues = []
    
    # Check files
    print("Checking files...")
    required_files = [
        ("benchmark/benchmark_runner.py", "Main runner"),
        ("benchmark/report_generator.py", "Report generator"),
        ("benchmark/model-configs.ini", "Model configurations"),
    ]
    
    for filename, description in required_files:
        if Path(filename).exists():
            print(f"  ✓ {description} ({filename})")
        else:
            print(f"  ✗ {description} ({filename})")
            issues.append(f"Missing {filename}")
    
    # Check prompts
    print("\nChecking prompts...")
    prompts_dir = Path("benchmark/prompts")
    if prompts_dir.exists():
        prompt_files = list(prompts_dir.glob("*.txt"))
        print(f"  ✓ Found {len(prompt_files)} prompts")
        for pf in sorted(prompt_files):
            print(f"    - {pf.stem}")
    else:
        print(f"  ✗ prompts directory not found")
        issues.append("Missing prompts directory")
    
    # Check dependencies
    print("\nChecking dependencies...")
    try:
        import requests
        print("  ✓ requests module")
    except ImportError:
        print("  ✗ requests module")
        issues.append("Run: pip install requests")
    
    # Check server
    print("\nChecking llama-server...")
    if check_server():
        print("  ✓ llama-server is running on localhost:8080")
    else:
        print("  ⚠ llama-server not found")
        print("    (This is OK if you haven't started it yet)")
    
    print()
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ Setup looks good!")
        return True

def main():
    """Main menu"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "validate":
            validate_setup()
        elif sys.argv[1] == "run":
            run_benchmark_interactive()
        elif sys.argv[1] == "help":
            print("""
Benchmark Suite Quick Start Helper

Usage:
  python quickstart.py              - Interactive menu
  python quickstart.py run          - Run benchmark (interactive)
  python quickstart.py validate     - Check setup
  python quickstart.py help         - Show this help

Examples:
  python quickstart.py validate
  python quickstart.py run

See README_BENCHMARKS.md for full documentation.
""")
    else:
        print_header("Benchmark Suite")
        print("1. Run benchmark (interactive)")
        print("2. Validate setup")
        print("3. View documentation")
        print("4. Exit")
        print()
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            run_benchmark_interactive()
        elif choice == "2":
            validate_setup()
        elif choice == "3":
            print("\nOpening README_BENCHMARKS.md...")
            os.system("cat README_BENCHMARKS.md | less")
        elif choice == "4":
            print("Goodbye!")
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
