import json

"""
This function stores all the information
chat log between users and the AI model Gemini
Flask-2.5 in our case, to keep record of time
and latency

"""
def log_run(userQuery, response_text, model_name, fan_out_latency, time_stamps, agents_run_log, validation = None, agent_latency_last_sec = None, error_meta = None, run_id = None):

    imp_data = {
                "user_message": userQuery, 
                "ai_response": response_text,
                "model_name": model_name,
                "time_stamp": time_stamps,

                "fan_out_latency_sec": fan_out_latency,
                "agent_latency_last_sec": agent_latency_last_sec,
                "agent_latency_metrics": agents_run_log,

                "error_meta": error_meta,
               
                "validation": validation,
                "run_id": run_id
            }
    jsonData = json.dumps(imp_data, ensure_ascii = False)
    with open("data/runs.jsonl", 'a', encoding = 'utf-8') as file:
        file.write(jsonData + "\n")
    
   
    