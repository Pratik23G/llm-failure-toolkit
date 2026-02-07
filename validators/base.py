from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Any

#use od dataclass from python built-in library to make a boilerplate and avoid
# repetition of result dictionaries
@dataclass
class contextValidation:
        user_prompt: str
        model_response: str
        model_name: str
        max_output_chars: Optional[int] = None
        max_output_tkns: Optional[int] = None


class BaseValidator(ABC):
    def build_result(self, context: contextValidation, passed: bool, 
                     error: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> dict:
        d = { 
             "user_prompt":context.user_prompt,
            "model_response":context.model_response or "",
            "model_name" :context.model_name,
            "passed": passed,
            "error":error
        }
        if meta:
             d["meta"] = meta
        return d

    @abstractmethod
    def validateTests(self, context: contextValidation) -> dict:
        pass

