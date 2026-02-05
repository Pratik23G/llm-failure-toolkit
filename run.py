

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

    test2 = [
         contextValidation("Hi", "Hi", "Gemini"),
         contextValidation("Wnat is the current largest dominating bill?", "The British Pound follwoed by The U.S. Dollar Bill", "Gemini"),
         contextValidation("How do you write hello in spanish? ", "hola", "Gemini"),
         contextValidation("Ok bye gemini", None, "Gemini")
    ]

    x = ShortOutputValidator()
    for tst in test2:
         print(x.validateTests(tst))

    
    test3 = [
         contextValidation("Hi", "Hi", "Gemini"),
         contextValidation("Wnat is the current largest dominating bill?", "The British Pound follwoed by The U.S. Dollar Bill", "Gemini"),
         contextValidation("What is largest galaxy we have known so far?", "The largest galaxy we have known so far, in terms of sheer physical size and number of stars, is **IC 1101**.\n\nHere are some details about it:\n\n*   **Type:** It's a **supergiant elliptical galaxy**.\n*   **Size:** Its luminous disk stretches for an incredible **2 to 6 million light-years** across. To put that into perspective:\n    *   Our Milky Way galaxy is only about 100,000 light-years across.\n    *   The Andromeda galaxy, our nearest large neighbor, is about 220,000 light-years across.\n*   **Stars:** It's estimated to contain up to **100 trillion (10^14) stars**, whereas the Milky Way has about 200-400 billion.\n*   **Location:** It's located about 1.04 billion light-years away from Earth, at the center of the Abell 2029 galaxy cluster.\n\nIt's truly a behemoth of the universe!", "Gemini"),
         contextValidation("Ok bye gemini", None, "Gemini")
    ]

    z_test = LongOutputValidator()
    for tests in test3:
         print(z_test.validateTests(tests))

