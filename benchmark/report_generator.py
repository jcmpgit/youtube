#!/usr/bin/env python3
"""
Report Generator for Benchmark Results
Creates interactive HTML reports from benchmark JSON results
"""

import json
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import argparse
import glob as glob_module

@dataclass
class Stats:
    """Statistics for a single metric"""
    count: int
    mean: float
    median: float
    min: float
    max: float
    stdev: float

def compute_stats(values: List[float]) -> Stats:
    """Compute statistics for a list of values"""
    if not values:
        return Stats(0, 0, 0, 0, 0, 0)
    
    return Stats(
        count=len(values),
        mean=statistics.mean(values),
        median=statistics.median(values),
        min=min(values),
        max=max(values),
        stdev=statistics.stdev(values) if len(values) > 1 else 0
    )

class ReportGenerator:
    """Generate HTML reports from benchmark results"""
    
    def __init__(self, results_files: List[str]):
        self.results = []
        for f in results_files:
            path = Path(f)
            if path.exists():
                with open(path) as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        self.results.extend(data)
                    else:
                        self.results.append(data)
                print(f"  ✓ Loaded {path.name}")
            else:
                print(f"  ⚠ File not found: {path}")
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze results and compute statistics"""
        
        by_profile = {}
        by_prompt = {}
        all_durations = []
        all_tokens = []
        all_latencies = []
        all_throughputs = []
        
        for result in self.results:
            profile = result["model_config"]
            prompt = result["prompt_name"]
            status = result["status"]
            tps = result.get("tokens_per_second", 0.0)
            # Backward compatibility: compute throughput from tokens/duration if not set
            if tps <= 0 and result.get("tokens_generated", 0) > 0 and result.get("duration_seconds", 0) > 0:
                tps = result["tokens_generated"] / result["duration_seconds"]
            
            # By profile
            if profile not in by_profile:
                by_profile[profile] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "durations": [],
                    "tokens": [],
                    "latencies": [],
                    "throughputs": [],
                }
            
            by_profile[profile]["total"] += 1
            
            # By prompt
            if prompt not in by_prompt:
                by_prompt[prompt] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "durations": [],
                    "tokens": [],
                    "throughputs": [],
                }
            
            by_prompt[prompt]["total"] += 1
            
            if status == "success":
                by_profile[profile]["success"] += 1
                by_prompt[prompt]["success"] += 1
                
                by_profile[profile]["durations"].append(result["duration_seconds"])
                by_prompt[prompt]["durations"].append(result["duration_seconds"])
                all_durations.append(result["duration_seconds"])
                
                tokens = result["tokens_generated"]
                by_profile[profile]["tokens"].append(tokens)
                by_prompt[prompt]["tokens"].append(tokens)
                all_tokens.append(tokens)
                
                if tps > 0:
                    by_profile[profile]["throughputs"].append(tps)
                    by_prompt[prompt]["throughputs"].append(tps)
                    all_throughputs.append(tps)
                
                if result["first_token_latency_ms"]:
                    by_profile[profile]["latencies"].append(result["first_token_latency_ms"])
                    all_latencies.append(result["first_token_latency_ms"])
            else:
                by_profile[profile]["failed"] += 1
                by_prompt[prompt]["failed"] += 1
        
        # Compute stats
        for profile_data in by_profile.values():
            profile_data["stats"] = {
                "duration": asdict(compute_stats(profile_data["durations"])),
                "tokens": asdict(compute_stats(profile_data["tokens"])),
                "latency": asdict(compute_stats(profile_data["latencies"])),
                "throughput": asdict(compute_stats(profile_data["throughputs"])),
            }
        
        for prompt_data in by_prompt.values():
            prompt_data["stats"] = {
                "duration": asdict(compute_stats(prompt_data["durations"])),
                "tokens": asdict(compute_stats(prompt_data["tokens"])),
                "throughput": asdict(compute_stats(prompt_data["throughputs"])),
            }
        
        return {
            "by_profile": by_profile,
            "by_prompt": by_prompt,
            "overall_stats": {
                "total_tests": len(self.results),
                "total_success": sum(1 for r in self.results if r["status"] == "success"),
                "total_failed": sum(1 for r in self.results if r["status"] != "success"),
                "duration": asdict(compute_stats(all_durations)),
                "tokens": asdict(compute_stats(all_tokens)),
                "latency": asdict(compute_stats(all_latencies)),
                "throughput": asdict(compute_stats(all_throughputs)),
            }
        }
    
    def generate_html(self, analysis: Dict[str, Any], output_file: str = "reports/benchmark_report.html"):
        """Generate HTML report"""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Report</title>
    <style>
        :root {{
            --brand-bg: #1c1430;
            --brand-text: #f3f5fc;
            --brand-gradient-start: #7c3aed;
            --brand-gradient-end: #06b6d4;
            --bg: #120d1f;
            --card: #231a36;
            --card-border: rgba(124, 58, 237, 0.25);
            --text: #f3f5fc;
            --muted: rgba(243, 245, 252, 0.65);
            --border: rgba(243, 245, 252, 0.12);
            --accent-soft: rgba(6, 182, 212, 0.12);
            --success: #10b981;
            --error: #ef4444;
            --warning: #f59e0b;
        }}
        
        * {{ box-sizing: border-box; }}
        
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        
        .brand-header {{
            background: var(--brand-bg);
            border-bottom: 1px solid var(--card-border);
            padding: 28px 20px;
        }}
        
        .brand-inner {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            margin: 0;
            font-size: 2rem;
            background: linear-gradient(135deg, var(--brand-gradient-start), var(--brand-gradient-end));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }}
        
        .subtitle {{
            color: var(--muted);
            margin-top: 8px;
            font-size: 1rem;
        }}
        
        main {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 32px 0;
        }}
        
        .stat-card {{
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        
        .stat-label {{
            color: var(--muted);
            font-size: 0.875rem;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
        }}
        
        .stat-value.success {{ color: var(--success); }}
        .stat-value.error {{ color: var(--error); }}
        .stat-value.warning {{ color: var(--warning); }}
        
        .section {{
            margin: 40px 0;
        }}
        
        .section h2 {{
            font-size: 1.5rem;
            margin: 0 0 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--card-border);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        th {{
            background: rgba(124, 58, 237, 0.1);
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            color: var(--text);
            border-bottom: 1px solid var(--card-border);
        }}
        
        td {{
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        tr:last-child td {{ border-bottom: none; }}
        
        .progress-bar {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            height: 8px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            background: linear-gradient(90deg, var(--brand-gradient-start), var(--brand-gradient-end));
            height: 100%;
            transition: width 0.3s ease;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 600;
        }}
        
        .badge.success {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
        }}
        
        .badge.error {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--error);
        }}
        
        .metric {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }}
        
        .metric-value {{
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .metric-label {{
            color: var(--muted);
            font-size: 0.875rem;
        }}
        
        .footer {{
            text-align: center;
            color: var(--muted);
            padding: 20px;
            border-top: 1px solid var(--card-border);
            margin-top: 40px;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <header class="brand-header">
        <div class="brand-inner">
            <h1>Benchmark Report</h1>
            <p class="subtitle">AI Model Performance Evaluation</p>
        </div>
    </header>
    
    <main>
"""
        
        # Overall Summary
        stats = analysis["overall_stats"]
        html += f"""
        <section class="section">
            <h2>Overview</h2>
            <div class="summary-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Tests</div>
                    <div class="stat-value">{stats['total_tests']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Passed</div>
                    <div class="stat-value success">{stats['total_success']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Failed</div>
                    <div class="stat-value error">{stats['total_failed']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Success Rate</div>
                    <div class="stat-value">
                        {stats['total_success'] / stats['total_tests'] * 100:.1f}%
                    </div>
                </div>
            </div>
        </section>
        
        <section class="section">
            <h2>Performance Metrics</h2>
            <div>
                <h3 style="margin-top: 0; color: var(--muted);">Duration (seconds)</h3>
                <div class="metric">
                    <div class="metric-label">Mean</div>
                    <div class="metric-value">{stats['duration']['mean']:.2f}s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Median</div>
                    <div class="metric-value">{stats['duration']['median']:.2f}s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Min</div>
                    <div class="metric-value">{stats['duration']['min']:.2f}s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Max</div>
                    <div class="metric-value">{stats['duration']['max']:.2f}s</div>
                </div>
            </div>
            
            <div style="margin-top: 30px;">
                <h3 style="margin-top: 0; color: var(--muted);">Tokens Generated</h3>
                <div class="metric">
                    <div class="metric-label">Mean</div>
                    <div class="metric-value">{stats['tokens']['mean']:.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Median</div>
                    <div class="metric-value">{stats['tokens']['median']:.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total</div>
                    <div class="metric-value">{sum(r['tokens_generated'] for r in self.results)}</div>
                </div>
            </div>
            
            {f'''
            <div style="margin-top: 30px;">
                <h3 style="margin-top: 0; color: var(--muted);">First Token Latency (ms)</h3>
                <div class="metric">
                    <div class="metric-label">Mean</div>
                    <div class="metric-value">{stats['latency']['mean']:.1f}ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Median</div>
                    <div class="metric-value">{stats['latency']['median']:.1f}ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Min</div>
                    <div class="metric-value">{stats['latency']['min']:.1f}ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Max</div>
                    <div class="metric-value">{stats['latency']['max']:.1f}ms</div>
                </div>
            </div>
            ''' if stats['latency']['count'] > 0 else ''}
            
            {f'''
            <div style="margin-top: 30px;">
                <h3 style="margin-top: 0; color: var(--muted);">Throughput (tokens/sec)</h3>
                <div class="metric">
                    <div class="metric-label">Mean</div>
                    <div class="metric-value">{stats['throughput']['mean']:.1f} tok/s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Median</div>
                    <div class="metric-value">{stats['throughput']['median']:.1f} tok/s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Min</div>
                    <div class="metric-value">{stats['throughput']['min']:.1f} tok/s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Max</div>
                    <div class="metric-value">{stats['throughput']['max']:.1f} tok/s</div>
                </div>
            </div>
            ''' if stats['throughput']['count'] > 0 else ''}
        </section>
        
        <section class="section">
            <h2>Results by Model Profile</h2>
            <table>
                <tr>
                    <th>Profile</th>
                    <th>Success Rate</th>
                    <th>Avg Duration</th>
                    <th>Avg Tokens</th>
                    <th>Avg Throughput</th>
                    <th>Avg Latency</th>
                </tr>
"""
        
        for profile, data in sorted(analysis["by_profile"].items()):
            success_rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
            avg_duration = data["stats"]["duration"]["mean"]
            avg_tokens = data["stats"]["tokens"]["mean"]
            avg_throughput = data["stats"]["throughput"]["mean"]
            avg_latency = data["stats"]["latency"]["mean"]
            throughput_display = f"{avg_throughput:.1f} tok/s" if avg_throughput > 0 else "—"
            
            html += f"""
                <tr>
                    <td><strong>{profile}</strong></td>
                    <td>
                        <span class="badge {'success' if success_rate == 100 else 'warning' if success_rate > 0 else 'error'}">
                            {data['success']}/{data['total']} ({success_rate:.0f}%)
                        </span>
                    </td>
                    <td>{avg_duration:.2f}s</td>
                    <td>{avg_tokens:.0f}</td>
                    <td>{throughput_display}</td>
                    <td>{avg_latency:.1f}ms</td>
                </tr>
"""
        
        html += """
            </table>
        </section>
        
        <section class="section">
            <h2>Results by Prompt</h2>
            <table>
                <tr>
                    <th>Prompt</th>
                    <th>Success Rate</th>
                    <th>Avg Duration</th>
                    <th>Avg Tokens</th>
                    <th>Avg Throughput</th>
                </tr>
"""
        
        for prompt, data in sorted(analysis["by_prompt"].items()):
            success_rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
            avg_duration = data["stats"]["duration"]["mean"]
            avg_tokens = data["stats"]["tokens"]["mean"]
            avg_throughput = data["stats"]["throughput"]["mean"]
            throughput_display = f"{avg_throughput:.1f} tok/s" if avg_throughput > 0 else "—"
            
            html += f"""
                <tr>
                    <td><strong>{prompt}</strong></td>
                    <td>
                        <span class="badge {'success' if success_rate == 100 else 'warning' if success_rate > 0 else 'error'}">
                            {data['success']}/{data['total']} ({success_rate:.0f}%)
                        </span>
                    </td>
                    <td>{avg_duration:.2f}s</td>
                    <td>{avg_tokens:.0f}</td>
                    <td>{throughput_display}</td>
                </tr>
"""
        
        html += """
            </table>
        </section>
        
        <div class="footer">
            <p>Benchmark Report Generated by Benchmark Suite</p>
        </div>
    </main>
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"✓ Report generated: {output_file}")

def asdict(stats: Stats) -> Dict[str, float]:
    """Convert Stats to dict"""
    return {
        'count': stats.count,
        'mean': stats.mean,
        'median': stats.median,
        'min': stats.min,
        'max': stats.max,
        'stdev': stats.stdev
    }

def main():
    parser = argparse.ArgumentParser(description="Generate HTML report from benchmark results")
    parser.add_argument("results_file", nargs="+", help="Path(s) to benchmark results JSON file(s). Supports glob patterns like benchmark_results/results_*.json")
    parser.add_argument("--output", default="reports/benchmark_report.html", help="Output HTML file")
    
    args = parser.parse_args()
    
    # Expand any glob patterns
    files_to_load = []
    for pattern in args.results_file:
        expanded = glob_module.glob(pattern)
        if expanded:
            files_to_load.extend(expanded)
        else:
            files_to_load.append(pattern)
    
    print(f"Loading {len(files_to_load)} result file(s)...")
    generator = ReportGenerator(files_to_load)
    print(f"  Total results loaded: {len(generator.results)}")
    
    analysis = generator.analyze_results()
    generator.generate_html(analysis, args.output)
    print(f"\n✓ Report generated: {args.output}")
    print(f"  Open with: open {args.output}")

if __name__ == "__main__":
    main()
