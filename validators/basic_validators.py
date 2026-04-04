#TODO: Build and add logic here from base.py here

"""
    make some imports from base.py files for context validation and
    add ABC(abstract constructor ) from python contract validator

"""

import re

from validators.base import contextValidation, BaseValidator

#deciding a consistent result dictionary contract to store results

#initiate the class contextValidation by making an object



#make an empty validator check detect for an empty string

MIN_LENGTH = 10
MODEL_CONTEXT_LENGTH = 300

REFUSAL_PATTERN_RESP = [
    re.compile( r"i (cannot|can't|won't|not allowed) (help|assist|fulfill|provide|do that)"),
    re.compile( r"(as an| i am an) (ai|language model|assistant)"),
    re.compile( r"(is|are) (illegal|againstmy work|unethical) "),
    re.compile( r" against my (guidelines|policy) ")
]

class EmptyOutputValidator(BaseValidator):
    def validateTests(self, context: contextValidation) -> dict:
        model_resp = context.model_response or ""
        is_empty = not model_resp.strip()
        return self.build_result(
            context = context,
            passed = not is_empty,
            error = "model_response is empty or whitespace" if is_empty else None,
        )

#TODO: Implement a validator for short inputs

class ShortOutputValidator(BaseValidator):
    def validateTests(self, context: contextValidation) -> dict:
        models_resp = context.model_response or ""
        clean = models_resp.strip()
        is_short = len(clean) < MIN_LENGTH 
        is_white_space = (clean == "")
    
        return self.build_result(
            context = context,
            passed = not is_short,
            error = "model_response is short or whitespaces" if is_short or is_white_space else  None,
            meta={"length": len(clean), "min_length": MIN_LENGTH},
        )
    
#TODO: Implement context_validation for longer responses and if it passes the models limit
class LongOutputValidator(BaseValidator):
    def validateTests(self, context: contextValidation) -> dict:
        model_longer_resp = context.model_response or ""
        cleaned_resp = model_longer_resp.strip()
        limit = context.max_output_chars or MODEL_CONTEXT_LENGTH
        is_too_long = len(cleaned_resp) > limit
   
        return self.build_result(
            context=context,
            passed=not is_too_long,
            error="model_response exceeds max_output_chars" if is_too_long else None,
            meta={"length": len(cleaned_resp), "limit": limit}
        )

class RefusalValidator(BaseValidator):
    def validateTests(self, context: contextValidation) -> dict:
        model_resp = context.model_response or ""
        cleaned_resp = model_resp.strip().lower()
        limit = context.max_output_chars or MODEL_CONTEXT_LENGTH
        
        is_refusal = any(pattern.search(cleaned_resp) for pattern in REFUSAL_PATTERN_RESP)

        
        return self.build_result(
            context=context,
            passed=not is_refusal,
            error="model_response contains refusal phrases" if is_refusal else None,
            meta={"length": len(cleaned_resp), "limit": limit}
        )


""" 
This class makes sure to check for repeated prompts from agents
so we could avoid repeated responses and loose token usage.
"""

class RepetitionValidator(BaseValidator):
    def validateTests(self, context: contextValidation) -> dict:
        model_resp = context.model_response or ""
        
        cleaned_resp = model_resp.strip().lower()
        clean_sentence_resp = [s for s in re.split(r'[.\n]', cleaned_resp) if s.strip()]
        

        unique_sentences = set(clean_sentence_resp)
        has_repeats = len(unique_sentences) < len(clean_sentence_resp)

        return self.build_result(
            context = context,
            passed = not has_repeats,
            error = "model_response contains repeated sentences" if has_repeats else None,
            meta = {"length": len(clean_sentence_resp), "unique_sentences": len(unique_sentences)}
        )