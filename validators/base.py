from abc import ABC
from abc import abstractmethod

class contextValidation:
    def __init__(self, user_prompt: str, model_response: str, model_name: str):
        self.user_prompt = user_prompt
        self.model_response = model_response
        self.model_name = model_name

class BaseValidator(ABC):
    @abstractmethod
    def validateTests(self, context: contextValidation) -> dict:
        pass

