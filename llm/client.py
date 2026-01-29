import os
from google import genai

from dotenv import load_dotenv 

#This is a test function please ignore its existence here
def sayAI(user):
    print("Hello", user)

def config():
    load_dotenv()

#Actual code:
class AIBot:
    
    config()

    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chats = self.client.chats.create(model="gemini-2.5-flash")

    def callModel(self, userPromptText):

        responseAi = self.chats.send_message_stream(userPromptText)

        fullUserText = " "

        for chunks in responseAi:
            fullUserText += chunks.text
        print()

        return fullUserText


SEGAI = AIBot()


