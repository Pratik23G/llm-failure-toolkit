

"""
Runner:

we need to make sure it responses to the text


model settings and imports

"""

import time
import asyncio

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

        bots = [AIBot(), StubBot(), SecondAIBot()]
        names = ["Gemini-Flask-2.5", "Open-A.I.-0.01", "openai/gpt-oss-120b"]
        #Condition which runs as long user does not type exit
        # This prompt helps to have converstion between user and Model  
        while True:
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
                    threadTask = asyncio.wait_for(asyncio.to_thread(bot.call, userQuery), timeout = 20)

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
    
if __name__ == "__main__":
     asyncio.run(main())

                    
                    
        