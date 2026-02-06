

"""
Runner:

we need to make sure it responses to the text


model settings and imports

"""

import time

from datetime import datetime, timezone

from llm.client import  SEGAI

from logger import run_logger

from validators.base import contextValidation, BaseValidator
from validators.basic_validators import EmptyOutputValidator, ShortOutputValidator, LongOutputValidator

from validators.runner import RunAllTests

from typing import List

if __name__ == "__main__":

    #Global validators list
    validate_list = [EmptyOutputValidator(), ShortOutputValidator(), LongOutputValidator()]
    #Condition which runs as long user does not type exit
    # This prompt helps to have converstion between user and Model  
    while True:
            userQuery = input(">- ")

            if userQuery == "exit":
                break
            
            time_stamps = datetime.now(timezone.utc).isoformat()
            startTime = time.perf_counter()
            response_text = SEGAI.callModel(userQuery)

            context_r = contextValidation(userQuery, response_text, "Gemini-Flask-2.5")
            print(response_text)

            endTime = time.perf_counter()

            total_run_time = endTime - startTime

            
            report_log = RunAllTests.run_validators(context_r, validate_list)
            run_logger.log_run(userQuery, response_text, "Gemini-Flask-2.5", total_run_time, time_stamps, report_log)
            

    