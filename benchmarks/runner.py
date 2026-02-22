"""
Benchmark Runner
================
Runs a predefined set of prompts (benchmarks/prompts.json) against all
selected agents concurrently, validates each response, and writes results to
data/benchmark_results.jsonl.

Usage:
    python -m benchmarks.runner
    python -m benchmarks.runner --agents stub
    python -m benchmarks.runner --agents gemini openai --timeout 30
"""

import asyncio
import json
import time
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from llm.client import build_registry
from validators.base import contextValidation
from validators.basic_validators import EmptyOutputValidator, ShortOutputValidator, LongOutputValidator
from validators.runner import RunAllTests

PROMPTS_FILE  = Path(__file__).parent / "prompts.json"
RESULTS_FILE  = Path("data/benchmark_results.jsonl")
ALLOWED_AGENTS = ["gemini", "stub", "openai"]


def load_prompts() -> list:
    with open(PROMPTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_results(results: list) -> None:
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def print_summary(results: list) -> None:
    print("\n" + "=" * 62)
    print("  BENCHMARK SUMMARY")
    print("=" * 62)

    # Group results by agent key
    agents: dict = {}
    for r in results:
        key = r["agent_key"]
        agents.setdefault(key, {"name": r["agent_name"], "records": []})
        agents[key]["records"].append(r)

    for agent_key, data in agents.items():
        records = data["records"]
        name    = data["name"]
        total   = len(records)
        passed  = sum(1 for r in records if r["validation"]["passed"])
        errors  = sum(1 for r in records if not r["error_meta"].get("ok", True))

        latencies = [r["latency_sec"] for r in records if r["latency_sec"] is not None]
        avg_lat   = sum(latencies) / len(latencies) if latencies else 0.0

        print(f"\n  Agent : {name}  [{agent_key}]")
        print(f"  -----------------------------------------------")
        print(f"  Prompts run  : {total}")
        print(f"  Passed       : {passed}  ({100 * passed // total}%)")
        print(f"  Failed       : {total - passed}")
        print(f"  API errors   : {errors}")
        print(f"  Avg latency  : {avg_lat:.3f}s")

        # Per-validator failure breakdown
        failures: dict = {}
        for r in records:
            for vr in r["validation"]["results"]:
                if not vr["passed"] and vr.get("error"):
                    err = vr["error"]
                    failures[err] = failures.get(err, 0) + 1

        if failures:
            print("  Failure breakdown:")
            for err, count in sorted(failures.items(), key=lambda x: -x[1]):
                print(f"    • {err}: {count}")

    print("\n" + "=" * 62)
    print(f"  Results saved → {RESULTS_FILE}")
    print("=" * 62 + "\n")


async def run_benchmark(agent_keys: List[str], registry: dict, timeout: int) -> list:
    prompts    = load_prompts()
    validators = [EmptyOutputValidator(), ShortOutputValidator(), LongOutputValidator()]
    all_results: list = []

    selected_keys  = [k for k in agent_keys if k in registry]
    selected_names = [registry[k][0] for k in selected_keys]
    selected_bots  = [registry[k][1] for k in selected_keys]

    total = len(prompts)
    print(f"\nRunning {total} prompts × {len(selected_keys)} agent(s)...\n")

    for i, item in enumerate(prompts, 1):
        prompt    = item["prompt"]
        prompt_id = item["id"]
        tags      = item.get("tags", [])

        preview = prompt[:55] + "..." if len(prompt) > 55 else prompt
        print(f"  [{i:2}/{total}] {prompt_id:<28} \"{preview}\"")

        tasks = [
            asyncio.wait_for(asyncio.to_thread(bot.call, prompt), timeout=timeout)
            for bot in selected_bots
        ]

        fan_start = time.perf_counter()
        results   = await asyncio.gather(*tasks, return_exceptions=True)
        fan_elapsed = time.perf_counter() - fan_start

        ts = datetime.now(timezone.utc).isoformat()

        for agent_key, agent_name, bot, result in zip(
            selected_keys, selected_names, selected_bots, results
        ):
            response_text = bot.errorLogs.set_from_result(result)
            error_meta    = bot.errorLogs.get_meta()

            ctx        = contextValidation(prompt, response_text, agent_name)
            validation = RunAllTests.run_validators(ctx, validators)

            record = {
                "run_id":             f"bench-{ts}-{prompt_id}-{agent_key}",
                "prompt_id":          prompt_id,
                "tags":               tags,
                "prompt":             prompt,
                "agent_key":          agent_key,
                "agent_name":         agent_name,
                "response":           response_text,
                "validation":         validation,
                "latency_sec":        bot.monitor.last_latency,
                "fan_out_latency_sec": fan_elapsed,
                "error_meta":         error_meta,
                "timestamp":          ts,
            }
            all_results.append(record)

    return all_results


async def main() -> None:
    load_dotenv()

    parser = ArgumentParser(description="Benchmark runner — runs predefined prompts against LLM agents")
    parser.add_argument("--agents", nargs="+", default=["gemini", "stub", "openai"],
                        help="Agents to benchmark (default: all)")
    parser.add_argument("--timeout", type=int, default=20,
                        help="Per-agent call timeout in seconds (default: 20)")
    args = parser.parse_args()

    bad = [a for a in args.agents if a not in ALLOWED_AGENTS]
    if bad:
        parser.error(f"Invalid agent(s) {bad}. Valid: {sorted(ALLOWED_AGENTS)}")

    registry = build_registry()

    missing = [a for a in args.agents if a not in registry]
    if missing:
        print(f"[warn] Agent(s) {missing} not available — check API keys. Skipping.")

    available = [a for a in args.agents if a in registry]
    if not available:
        parser.error("No agents could be initialised. Check your API keys.")

    results = await run_benchmark(available, registry, args.timeout)
    save_results(results)
    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
