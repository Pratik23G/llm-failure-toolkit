This is a PET PRJECT FOR MY FINAL CAPSTONE PROJECT BASED ON LLM Failure 
Analysis and Debugging Toolkit

For this project The goal is simple:

I would like to build a "A.I. prompt Runner and Logging Harness"

##Project Goal##:
<-------->*************************************<------------------------------->
    What this project does?
    ---> Goal is to build a simple engine that runs prompts/ on LLM
        models take them as tasks and store their logs and latency

    There are 2 parts in the project:
        Prompt Runner: A simple program that takes prompts from users, sends it
        to a LLM model like OPEN A.I. GPT, OLAMA, Gemini, receives model's
        answer and prints and returns the answer.

        Logging Harness: We then store those results in a DataBase, it stores
            what happens in each prompt, it saves a copy report:
                1. What did user prompt
                2. How long did it take for the model to response
                3. What was their response
                4. How accurate was the response
                5. Compare the statistics among the different models
                6. What prompts took longer for the correct response

==================================***===========================================
Some major tools and components of the project:
    Runner: run.py [This is our main program runner which shows the stat for both projects]

    Logger: runLogger.py [This project focuses on keeping track of the records]

    Client prompts: client.py [This program specifically talks with LLM models and sends prompts]

    data stored: runs.jsonl [Stores the records and necessary data]

================================***============================================