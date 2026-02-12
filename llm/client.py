import os
from google import genai
from openai import OpenAI
import time
import numpy as np




#This is a test function please ignore its existence here
def sayAI(user):
    print("Hello", user)


# a helper function which tracks down the latency for every agentic model

class AgentLatencyAnalysis:
    def __init__(self, window_size = 100):
        self.latencies = []
        self.window_size = window_size
        self.last_latency = None
    
    def log_latency(self, latency):
        self.latencies.append(latency)
        if len(self.latencies) > self.window_size:
            self.latencies.pop(0)
        self.last_latency = latency

    def get_latency_metrics(self):
        if not self.latencies:
            return None
        return{
            "p50": float(np.percentile(self.latencies, 50)),
            "p95" : float(np.percentile(self.latencies, 95)),
            "p99" : float(np.percentile(self.latencies, 99)),
        }


#Actual code:

class AIBot:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chats = self.client.chats.create(model="gemini-2.5-flash")
        self.monitor = AgentLatencyAnalysis()

    def call(self, userPromptText):
        
        startTime = time.perf_counter()

        try:
            responseAi = self.chats.send_message_stream(userPromptText)

            fullUserText = ""

            for chunks in responseAi:
                fullUserText += chunks.text
            print()
            return fullUserText
        finally:
            self.monitor.log_latency(time.perf_counter() - startTime)
        

class SecondAIBot:
    def __init__(self):
        key = os.getenv("NEBIUS_API_KEY")

        if not key:
            raise ValueError("Missing or invalid NEBIUS_API_KEY")

        self.client = OpenAI(api_key = key,
                     base_url="https://api.tokenfactory.nebius.com/v1/"        
                    )
        self.model = "openai/gpt-oss-120b"
        self.monitor = AgentLatencyAnalysis()
    
    def call(self, userPromptText):
        
        startTime = time.perf_counter()
        try:
            aiResp = self.client.chat.completions.create(
                model = self.model,
                messages=[{"role":"user","content": userPromptText}]
            )
            return aiResp.choices[0].message.content
        
        finally:
            self.monitor.log_latency(time.perf_counter() - startTime)
        




