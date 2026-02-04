#TODO: Build and add logic here from base.py here

"""
    make some imports from base.py files for context validation and
    add ABC(abstract constructor ) from python contract validator

"""

from validators.base import contextValidation, BaseValidator

#deciding a consistent result dictionary contract to store results

#initiate the class contextValidation by making an object



#make an empty validator check detect for an empty string



class EmptyOutputValidator(BaseValidator):
    def validateTests(self, context: contextValidation) -> dict:
        model_resp = context.model_response or ""
        is_empty = not model_resp.strip()
        d = {
            "user_prompt" : context.user_prompt, 
            "model_response" : model_resp, 
            "model_name" : context.model_name,
            "passed" : not is_empty,
            "error" : "model_response is empty or whitespace" if is_empty else None
        }
        d["error"] = "..." if is_empty else None

        return d

