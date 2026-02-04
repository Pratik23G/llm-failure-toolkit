

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
from validators.basic_validators import EmptyOutputValidator

if __name__ == "__main__":

    #Condition which runs as long user does not type exit
    # This prompt helps to have converstion between user and Model  
    while True:
            userQuery = input(">- ")

            if userQuery == "exit":
                break
            
            time_stamps = datetime.now(timezone.utc).isoformat()
            startTime = time.perf_counter()
            response_text = SEGAI.callModel(userQuery)

            print(response_text)

            endTime = time.perf_counter()

            total_run_time = endTime - startTime

            run_logger.log_run(userQuery, response_text, "Gemini-Flask-2.5", total_run_time, time_stamps)

    # quick tests
    tests = [
        contextValidation("Hi", "Hello", "Gemini"),
        contextValidation("Hi", "", "Gemini"),
        contextValidation("Hi", "   ", "Gemini"),
        contextValidation("Hi", None, "Gemini"),
    ]

    v = EmptyOutputValidator()
    for t in tests:
        print(v.validateTests(t))

# TODO: NEED TO SOME HOW IMPLEMENT BASE.PY LOGIC TO RUN, SO THAT OUR MACHINE CAN VALIDATE THE RUN AND RESULT ON SAME INPUT