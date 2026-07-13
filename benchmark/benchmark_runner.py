#!/usr/bin/env python3
"""
Benchmark Runner for AI Agent Evaluation Suite
Executes prompts against llama-server (or LM Studio) and generates reports

Supported Servers:
  - llama-server (llama.cpp) - port 8080 (default)
  - LM Studio - port 1234
  - Any OpenAI-compatible API endpoint

Usage:
  python3 benchmark_runner.py              # Uses localhost:8080 (llama.cpp)
  python3 benchmark_runner.py --port 1234  # Uses LM Studio
  python3 benchmark_runner.py --host 192.168.1.100 --port 8080  # Remote server
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import requests
from dataclasses import dataclass, asdict
import statistics

@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    prompt_name: str
    model_config: str
    start_time: str
    end_time: str
    duration_seconds: float
    status: str  # "success", "error", "timeout"
    tokens_generated: int
    tokens_per_second: float = 0.0
    first_token_latency_ms: Optional[float] = None
    response_text: str = ""
    error_message: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

class ConfigParser:
    """Parse model-configs.ini"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.configs = {}
        self._parse()
    
    def _parse(self):
        """Parse INI-style config file"""
        current_section = None
        with open(self.config_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    self.configs[current_section] = {}
                elif '=' in line and current_section:
                    key, value = line.split('=', 1)
                    self.configs[current_section][key.strip()] = value.strip()
        
        # Merge defaults into each profile
        defaults = self.configs.get('*', {})
        for section in self.configs:
            if section != '*':
                merged = {**defaults, **self.configs[section]}
                self.configs[section] = merged
    
    def get_profiles(self) -> List[str]:
        """Return all model profile names (exclude [*])"""
        return [k for k in self.configs.keys() if k != '*']
    
    def get_config(self, profile: str) -> Dict[str, str]:
        """Get config for a specific profile"""
        return self.configs.get(profile, {})

class LlamaServerClient:
    """Connect to llama-server and execute prompts"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, timeout: int = 600):
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
    
    def health_check(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _extract_text(self, data: Dict[str, Any]) -> str:
        """Extract text from response JSON, handling both OpenAI and llama.cpp formats."""
        # OpenAI format: {"choices": [{"text": "..."}]}
        if 'choices' in data and data['choices']:
            choice = data['choices'][0]
            if 'text' in choice:
                return choice['text']
            if 'delta' in choice and 'content' in choice['delta']:
                return choice['delta']['content']
        # llama.cpp / LM Studio format: {"content": "..."}
        if 'content' in data:
            return data['content']
        return ""
    
    def generate(self, prompt: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Generate text using llama-server / LM Studio.
        Handles both OpenAI and llama.cpp response formats,
        both streaming (SSE) and non-streaming responses.
        Returns response with timing metrics.
        """
        start_time = time.time()
        first_token_time = None
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/completions",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "stream": True,
                },
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()
            
            full_text = ""
            token_count = 0
            content_type = response.headers.get("content-type", "")
            is_streaming = "text/event-stream" in content_type
            
            if is_streaming:
                # Streaming (SSE) response - iterate over events
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    if not first_token_time:
                        first_token_time = time.time() - start_time
                    
                    line_text = line.decode("utf-8", errors="replace").strip()
                    
                    if not line_text or line_text == "data: [DONE]":
                        continue
                    
                    if line_text.startswith("data: "):
                        line_text = line_text[6:]
                    
                    try:
                        data = json.loads(line_text)
                        delta = self._extract_text(data)
                        if delta:
                            full_text += delta
                            token_count += 1
                    except json.JSONDecodeError:
                        pass
            else:
                # Non-streaming response - get full JSON at once
                if not first_token_time:
                    first_token_time = time.time() - start_time
                
                try:
                    data = response.json()
                    full_text = self._extract_text(data)
                except (json.JSONDecodeError, KeyError):
                    full_text = response.text
            
            total_time = time.time() - start_time
            
            # Fallback: count words as token estimate if streaming didn't work
            if token_count == 0 and full_text.strip():
                token_count = len(full_text.split())
            
            # Estimate first token latency from total time if not available
            if not first_token_time and token_count > 0 and total_time > 0:
                first_token_time = total_time / token_count
            
            return {
                "success": True,
                "text": full_text[:500] + "..." if len(full_text) > 500 else full_text,
                "tokens": token_count,
                "duration": total_time,
                "first_token_latency_ms": first_token_time * 1000 if first_token_time else None,
            }
        except requests.Timeout:
            return {"success": False, "error": "Timeout", "duration": time.time() - start_time}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": time.time() - start_time}

class BenchmarkRunner:
    """Main benchmark execution engine"""
    
    def __init__(self, 
                 config_path: str,
                 prompts_dir: str,
                 output_dir: str = "benchmark_results",
                 host: str = "localhost",
                 port: int = 8080,
                 timeout: int = 600):
        self.config_parser = ConfigParser(config_path)
        self.prompts_dir = Path(prompts_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.client = LlamaServerClient(host, port, timeout)
        self.results: List[BenchmarkResult] = []
    
    def load_prompts(self) -> Dict[str, str]:
        """Load all prompts from prompts directory"""
        prompts = {}
        for prompt_file in self.prompts_dir.glob("*.txt"):
            with open(prompt_file) as f:
                prompts[prompt_file.stem] = f.read()
        return prompts
    
    def run_benchmark(self, 
                      profile: Optional[str] = None,
                      prompt_name: Optional[str] = None,
                      all_profiles: bool = False) -> List[BenchmarkResult]:
        """
        Run benchmarks for specified profile/prompt combination.
        - If profile is set, run that specific profile.
        - If all_profiles is True, run every profile in model-configs.ini.
        - Otherwise, run only the first profile (for LM Studio / one-model-at-a-time).
        - If prompt_name is None, run all prompts.
        """
        
        # Verify server is running
        print("Checking llama-server health...")
        if not self.client.health_check():
            print(f"❌ llama-server not running at {self.client.base_url}")
            if self.client.base_url == "http://localhost:1234":
                print("   Make sure LM Studio is running with 'Local Server' started.")
            else:
                print("   Start it with: llama-server -c 8000 -m <model_path> (see model-configs.ini)")
            sys.exit(1)
        print("✓ llama-server is running")
        
        prompts = self.load_prompts()
        
        if profile:
            profiles = [profile]
        elif all_profiles:
            profiles = self.config_parser.get_profiles()
        else:
            # Default: just the first profile (one model loaded at a time)
            profiles = [self.config_parser.get_profiles()[0]]
        
        if prompt_name:
            prompts = {prompt_name: prompts[prompt_name]}
        
        total_tests = len(profiles) * len(prompts)
        current = 0
        
        print(f"\n📊 Running {total_tests} tests...\n")
        
        for cfg_profile in profiles:
            for pname, ptext in prompts.items():
                current += 1
                print(f"[{current}/{total_tests}] {cfg_profile} → {pname}...", end=" ", flush=True)
                
                start_time = datetime.now().isoformat()
                gen_start = time.time()
                
                response = self.client.generate(ptext)
                
                end_time = datetime.now().isoformat()
                duration = time.time() - gen_start
                
                if response["success"]:
                    tokens = response["tokens"]
                    tps = tokens / duration if duration > 0 else 0.0
                    result = BenchmarkResult(
                        prompt_name=pname,
                        model_config=cfg_profile,
                        start_time=start_time,
                        end_time=end_time,
                        duration_seconds=duration,
                        status="success",
                        tokens_generated=tokens,
                        tokens_per_second=round(tps, 2),
                        first_token_latency_ms=response["first_token_latency_ms"],
                        response_text=response["text"][:500] + "..." if len(response["text"]) > 500 else response["text"],
                    )
                    print(f"✓ ({tokens} tokens, {duration:.2f}s, {tps:.1f} tok/s)")
                else:
                    result = BenchmarkResult(
                        prompt_name=pname,
                        model_config=cfg_profile,
                        start_time=start_time,
                        end_time=end_time,
                        duration_seconds=duration,
                        status="error",
                        tokens_generated=0,
                        first_token_latency_ms=None,
                        response_text="",
                        error_message=response["error"]
                    )
                    print(f"✗ {response['error']}")
                
                self.results.append(result)
        
        return self.results
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """Save raw results to JSON"""
        if filename is None:
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(
                [r.to_dict() for r in self.results],
                f,
                indent=2
            )
        
        return str(filepath)

def main():
    parser = argparse.ArgumentParser(description="Run benchmark suite against llama-server")
    parser.add_argument("--profile", help="Specific model profile to test (default: first profile only)")
    parser.add_argument("--all-profiles", action="store_true", help="Run against every profile in model-configs.ini")
    parser.add_argument("--prompt", help="Specific prompt to test (default: all)")
    parser.add_argument("--config", default="benchmark/model-configs.ini", help="Path to model config file")
    parser.add_argument("--prompts-dir", default="benchmark/prompts", help="Path to prompts directory")
    parser.add_argument("--output-dir", default="benchmark_results", help="Output directory for results")
    parser.add_argument("--host", default="localhost", help="llama-server host")
    parser.add_argument("--port", type=int, default=8080, help="llama-server port")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout per test in seconds (default: 600)")
    
    args = parser.parse_args()
    
    runner = BenchmarkRunner(
        config_path=args.config,
        prompts_dir=args.prompts_dir,
        output_dir=args.output_dir,
        host=args.host,
        port=args.port,
        timeout=args.timeout,
    )
    
    runner.run_benchmark(
        profile=args.profile,
        prompt_name=args.prompt,
        all_profiles=args.all_profiles
    )
    
    result_file = runner.save_results()
    print(f"\n✓ Results saved to: {result_file}")
    
    # Print summary
    successful = sum(1 for r in runner.results if r.status == "success")
    failed = len(runner.results) - successful
    total_tokens = sum(r.tokens_generated for r in runner.results)
    total_duration = sum(r.duration_seconds for r in runner.results)
    
    print(f"\n📈 Summary:")
    print(f"  ✓ Passed: {successful}/{len(runner.results)}")
    print(f"  ✗ Failed: {failed}/{len(runner.results)}")
    print(f"  📝 Total tokens: {total_tokens}")
    print(f"  ⏱️  Total time: {total_duration:.1f}s")
    if successful > 0:
        latencies = [r.first_token_latency_ms for r in runner.results 
                    if r.status == "success" and r.first_token_latency_ms]
        if latencies:
            print(f"  🎯 Avg first token latency: {statistics.mean(latencies):.1f}ms")

if __name__ == "__main__":
    main()
