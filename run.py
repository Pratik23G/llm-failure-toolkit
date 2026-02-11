

"""
Runner:

we need to make sure it responses to the text


model settings and imports

"""

import time
import asyncio

from datetime import datetime, timezone

from llm.client import AIBot, SecondAIBot

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
            def call(self, userQuery):
                if userQuery in open_ai_stub_model:
                    response_text2 = open_ai_stub_model[userQuery]
                else:
                    response_text2 = "I am not sure"
                return response_text2

        bots = [AIBot(), StubBot(), SecondAIBot()]
        names = ["Gemini-Flask-2.5", "Open-A.I.-0.01", "openai/gpt-oss-120b"]
        #Condition which runs as long user does not type exit
        # This prompt helps to have converstion between user and Model  
        while True:
                userQuery = input(">- ")

                if userQuery == "exit":
                    break
                
                time_stamps = datetime.now(timezone.utc).isoformat()

                tasks = []

                fan_out_start = time.perf_counter()

                for agent_name, bot in zip(names, bots):
                    threadTask = asyncio.wait_for(asyncio.to_thread(bot.call, userQuery), timeout = 20)

                    tasks.append(threadTask)

                    
                results = await asyncio.gather(*tasks , return_exceptions = True)

                fan_elapsed_time = time.perf_counter() - fan_out_start

                for agents, result in  zip(names, results):

                    if isinstance(result, Exception):
                         error_message = str(result)
                         response_text = f"ERROR: {error_message}"
                    else:
                         response_text = result

                    context_r = contextValidation(userQuery, response_text, agents)
                    report_log = RunAllTests.run_validators(context_r, validate_list)
                    print(f"\n[{agents}]")
                    print(response_text)

                    run_logger.log_run(userQuery, response_text, agents , fan_elapsed_time, time_stamps, report_log)
    
if __name__ == "__main__":
     asyncio.run(main())

                    
                    
        