import json

"""
This function stores all the information
chat log between users and the AI model Gemini
Flask-2.5 in our case, to keep record of time
and latency

"""
def log_run(userQuery, response_text, model_name, latency, time_stamps):

    imp_data = {"user_message ": userQuery, 
                "ai_response ": response_text,
                "model_name ": model_name,
                "latency(ms) ": latency,
                "time_stamp ": time_stamps}
    jsonData = json.dumps(imp_data)
    with open("data/runs.jsonl", 'a') as file:
        file.write(jsonData + "\n")
    
   
    