
from validators.base import contextValidation, BaseValidator
from typing import List


class RunAllTests:
    @staticmethod
    def run_validators( context: contextValidation, validators: List[BaseValidator]) -> dict:
        dict_stats = {
            
        }
        overall_passed = True
        results = []

        for validator in validators:
            value_validated = validator.validateTests(context)
            results.append(value_validated)

            if not value_validated.get("passed", False):
                overall_passed = False
        
        dict_stats["passed"] = overall_passed
        dict_stats["results"] = results
        
        return dict_stats