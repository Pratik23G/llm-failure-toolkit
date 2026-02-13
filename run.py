

"""
Runner:

we need to make sure it responses to the text


model settings and imports

"""

import time
import asyncio

from argparse import ArgumentParser, Namespace


from datetime import datetime, timezone

from llm.client import AIBot, SecondAIBot, AgentLatencyAnalysis, HandleErrorLogs

from logger import run_logger

from validators.base import contextValidation, BaseValidator
from validators.basic_validators import EmptyOutputValidator, ShortOutputValidator, LongOutputValidator

from validators.runner import RunAllTests

from typing import List

from dotenv import load_dotenv

async def main():
        load_dotenv()

        parser = ArgumentParser(description = "User Prompt Failure Runner for LLM")

        parser.add_argument("--prompt" , type = str, help = "User prompt to send to the model")
        parser.add_argument("--interactive", action = "store_true", help = "Run in interactive mode")
        parser.add_argument("--agents", nargs = '+', default=["gemini", "stub", "openai"], help = "List of agent names to run")
        parser.add_argument("--max-tokens", type = int, default = 100, help = "Maximum tokens for the model response")
        parser.add_argument("--timeout", type = int, default = 20, help = "Timeout for each agent response in seconds")

        args: Namespace = parser.parse_args()

        if args.timeout <= 0:
            parser.error("--timeout must be > 0")
        
        if args.max_tokens <= 0:
             parser.error("--max-tokens must be > 0")
        
        if args.prompt is not None and not args.prompt.strip():
             parser.error("--prompt cannot be empty if provided")
        
        ALLOWED = ["gemini", "stub", "openai"]

        bad = [agent for agent in args.agents if agent not in ALLOWED]
        if bad:
            parser.error(f"Invalid agent(s) {bad}. Valid: {sorted(ALLOWED)}")
        
        if args.prompt and args.interactive:
            parser.error("Cannot use --prompt and --interactive together")

        #Global validators list
        validate_list = [EmptyOutputValidator(), ShortOutputValidator(), LongOutputValidator()]

        #Build a stub-agent OpenAI-0.01
        open_ai_stub_model = {
            "Hi Open AI": "Hi! How can I assist you today?",
            "What is the most trending language in the market?" : "According to the internet it seems python for now",
            "Can you give me the distance for the moon?" : " ",
            "Ok Bye Open A.I." : "Bye :D"
        }

        #function for stub_sgent which reeplies to user_prompts
        class StubBot:
            def __init__(self):
                self.monitor = AgentLatencyAnalysis()
                self.errorLogs = HandleErrorLogs()

            
            

            def call(self, userQuery):
                startTime = time.perf_counter()
                try: 
                    if userQuery in open_ai_stub_model:
                        response_text2 = open_ai_stub_model[userQuery]
                    else:
                        response_text2 = "I am not sure"
                    return response_text2
                finally:
                     self.monitor.log_latency(time.perf_counter() - startTime)

        REGISTRY = {
             "gemini": ("Gemini-Flask-2.5", AIBot()),
             "stub": ("Open-A.I.-0.01", StubBot()),
             "openai": ("openai/gpt-oss-120b", SecondAIBot())
        }

        selected_agents = [REGISTRY[agent] for agent in args.agents]
        names = [n for (n, _) in selected_agents]
        bots = [b for (_, b) in selected_agents]
        
       
        #Condition which runs as long user does not type exit
        # This prompt helps to have converstion between user and Model  
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


                tasks = []

                fan_out_start = time.perf_counter()

                for bot in bots:
                    threadTask = asyncio.wait_for(asyncio.to_thread(bot.call, userQuery), timeout = args.timeout)

                    tasks.append(threadTask) 

                    
                results = await asyncio.gather(*tasks , return_exceptions = True)

                fan_elapsed_time = time.perf_counter() - fan_out_start

                for agents, bot, result in  zip(names, bots, results):
                    
                    response_text  = bot.errorLogs.set_from_result(result)
                    error_meta = bot.errorLogs.get_meta()
                    """  if isinstance(result, Exception):
                         error_message = str(result)
                         response_text = f"ERROR: {error_message}"
                    else:
                         response_text = result """

                    context_r = contextValidation(userQuery, response_text, agents)
                    validation = RunAllTests.run_validators(context_r, validate_list)
                    print(f"\n[{agents}]")
                    print(response_text)

                    agent_latency_last_sec = bot.monitor.last_latency
                    agents_run_log = bot.monitor.get_latency_metrics()
                    run_logger.log_run(userQuery, response_text, agents , fan_elapsed_time, time_stamps, agents_run_log, validation = validation, agent_latency_last_sec = agent_latency_last_sec, error_meta = error_meta, run_id=run_id)

                if args.prompt:
                    break
    
if __name__ == "__main__":
     asyncio.run(main())

                    
                    
        