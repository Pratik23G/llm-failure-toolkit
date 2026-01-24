print("Hello this is a sample test run for analysis")

"""
Runner:

we need to make sure it responses to the text


model settings and imports

"""


from llm.client import  SEGAI

from logger import run_logger

# this line of code is only for test-purposes will be kater removed
print(run_logger.displayStats("GPT-4", "45 ms", "140 Degrees"))




while True:
        userQuery = input(">- ")

        if userQuery == "exit":
            break

        SEGAI.callModel(userQuery)