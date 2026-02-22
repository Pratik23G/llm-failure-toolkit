"""
Runner:
Fan-out a user prompt to all selected agents concurrently, validate each
response, and log everything to data/runs.jsonl.
"""

import time
import asyncio

from argparse import ArgumentParser, Namespace
from datetime import datetime, timezone
from typing import List

from dotenv import load_dotenv

from llm.client import build_registry
from logger import run_logger
from validators.base import contextValidation, BaseValidator
from validators.basic_validators import EmptyOutputValidator, ShortOutputValidator, LongOutputValidator
from validators.runner import RunAllTests

ALLOWED_AGENTS = ["gemini", "stub", "openai"]


async def main():
        load_dotenv()

        parser = ArgumentParser(description="User Prompt Failure Runner for LLM")
        parser.add_argument("--prompt", type=str, help="User prompt to send to the model")
        parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
        parser.add_argument("--agents", nargs='+', default=["gemini", "stub", "openai"],
                            help="List of agent names to run")
        parser.add_argument("--timeout", type=int, default=20,
                            help="Timeout for each agent response in seconds")

        args: Namespace = parser.parse_args()

        if args.timeout <= 0:
            parser.error("--timeout must be > 0")

        if args.prompt is not None and not args.prompt.strip():
            parser.error("--prompt cannot be empty if provided")

        bad = [a for a in args.agents if a not in ALLOWED_AGENTS]
        if bad:
            parser.error(f"Invalid agent(s) {bad}. Valid: {sorted(ALLOWED_AGENTS)}")

        if args.prompt and args.interactive:
            parser.error("Cannot use --prompt and --interactive together")

        validate_list = [EmptyOutputValidator(), ShortOutputValidator(), LongOutputValidator()]

        REGISTRY = build_registry()

        # Filter to only agents that were successfully initialised
        available = {k: v for k, v in REGISTRY.items() if k in args.agents}
        if not available:
            parser.error("None of the requested agents could be initialised. Check your API keys.")

        names = [n for (n, _) in available.values()]
        bots  = [b for (_, b) in available.values()]

        # Condition which runs as long as user does not type exit
        # This prompt helps to have a conversation between user and Model
        while True:
                if args.prompt:
                    userQuery = args.prompt
                else:
                    try:
                        userQuery = input(">- ")
                    except EOFError:
                        break

                if userQuery == "exit":
                    break

                time_stamps = datetime.now(timezone.utc).isoformat()
                run_id = f"{time_stamps}-{userQuery}"

                tasks = [
                    asyncio.wait_for(asyncio.to_thread(bot.call, userQuery), timeout=args.timeout)
                    for bot in bots
                ]

                fan_out_start = time.perf_counter()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                fan_elapsed_time = time.perf_counter() - fan_out_start

                for agent_name, bot, result in zip(names, bots, results):
                    response_text = bot.errorLogs.set_from_result(result)
                    error_meta    = bot.errorLogs.get_meta()

                    context_r  = contextValidation(userQuery, response_text, agent_name)
                    validation = RunAllTests.run_validators(context_r, validate_list)

                    print(f"\n[{agent_name}]")
                    print(response_text)

                    agent_latency_last_sec = bot.monitor.last_latency
                    agents_run_log = bot.monitor.get_latency_metrics()
                    run_logger.log_run(
                        userQuery, response_text, agent_name,
                        fan_elapsed_time, time_stamps, agents_run_log,
                        validation=validation,
                        agent_latency_last_sec=agent_latency_last_sec,
                        error_meta=error_meta,
                        run_id=run_id,
                    )

                if args.prompt:
                    break


if __name__ == "__main__":
    asyncio.run(main())
