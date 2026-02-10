import os
from google import genai
from openai import OpenAI


from dotenv import load_dotenv 

#This is a test function please ignore its existence here
def sayAI(user):
    print("Hello", user)


load_dotenv()

#Actual code:

class AIBot:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chats = self.client.chats.create(model="gemini-2.5-flash")

    def call(self, userPromptText):

        responseAi = self.chats.send_message_stream(userPromptText)

        fullUserText = " "

        for chunks in responseAi:
            fullUserText += chunks.text
        print()

        return fullUserText

class SecondAIBot:
    def __init__(self):
        key = os.getenv("NEBIUS_API_KEY")

        if not key:
            raise ValueError("Missing or invalid NEBIUS_API_KEY")

        self.client = OpenAI(api_key = key,
                     base_url="https://api.tokenfactory.nebius.com/v1/"        
                    )
        self.model = "openai/gpt-oss-120b"

    
    def call(self, userPromptText):

        aiResp = self.client.chat.completions.create(
            model = self.model,
            messages=[{"role":"user","content": userPromptText}]
        )

        return aiResp.choices[0].message.content




