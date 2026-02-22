import os
from abc import ABC, abstractmethod
from google import genai
from openai import OpenAI
import time
import numpy as np




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


class BaseAgent(ABC):
    """Shared contract every agent must satisfy."""
    monitor: "AgentLatencyAnalysis"
    errorLogs: "HandleErrorLogs"

    @abstractmethod
    def call(self, userPromptText: str) -> str:
        pass


#Actual code:

class AIBot(BaseAgent):
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chats = self.client.chats.create(model="gemini-2.5-flash")
        self.monitor = AgentLatencyAnalysis()
        self.errorLogs = HandleErrorLogs()
    

    def call(self, userPromptText):
        
        startTime = time.perf_counter()

        try:
            responseAi = self.chats.send_message_stream(userPromptText)

            fullUserText = ""

            for chunks in responseAi:
                text = getattr(chunks, "text", "")
                if text:
                    fullUserText += text
            return fullUserText

        finally:
            self.monitor.log_latency(time.perf_counter() - startTime)
        
        

class SecondAIBot(BaseAgent):
    def __init__(self):
        key = os.getenv("OPENROUTER_API_KEY")

        if not key:
            raise ValueError("Missing or invalid OPENROUTER_API_KEY")

        self.client = OpenAI(
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = "meta-llama/llama-3.1-8b-instruct:free"
        self.monitor = AgentLatencyAnalysis()
        self.errorLogs = HandleErrorLogs()
    
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
        

# a class which handles errors and test cases to store in a meta data 
# in python rather than string issues

class HandleErrorLogs:

    def __init__(self):
        self.meta = {}
    
    def set_from_result(self, model_result):
        
        self.meta = {}

        if isinstance(model_result, Exception):

            self.meta["ok"] = False
            self.meta["error_type"] = type(model_result).__name__
            self.meta["error_message"] = str(model_result)
            return f"ERROR: {self.meta['error_message']}"
        else:
            self.meta["ok"] = True
            return "" if model_result is None else str(model_result)
            
    def get_meta(self):
        return self.meta


_STUB_RESPONSES = {
    "Hi Open AI": "Hi! How can I assist you today?",
    "What is the most trending language in the market?": "According to the internet it seems python for now",
    "Can you give me the distance for the moon?": " ",
    "Ok Bye Open A.I.": "Bye :D",
}


class StubBot(BaseAgent):
    """Offline stub agent — deterministic responses, no API key required."""

    def __init__(self):
        self.monitor = AgentLatencyAnalysis()
        self.errorLogs = HandleErrorLogs()

    def call(self, userQuery: str) -> str:
        startTime = time.perf_counter()
        try:
            return _STUB_RESPONSES.get(userQuery, "I am not sure")
        finally:
            self.monitor.log_latency(time.perf_counter() - startTime)


def build_registry() -> dict:
    """Instantiate all agents after env vars are loaded.
    Agents that fail to initialise (missing API key) are skipped with a warning.
    """
    registry: dict = {}

    try:
        registry["gemini"] = ("Gemini-Flash-2.5", AIBot())
    except Exception as exc:
        print(f"[warn] gemini agent unavailable: {exc}")

    registry["stub"] = ("Open-A.I.-0.01", StubBot())

    try:
        registry["openai"] = ("meta-llama/llama-3.1-8b-instruct:free", SecondAIBot())
    except Exception as exc:
        print(f"[warn] openai agent unavailable: {exc}")

    return registry
