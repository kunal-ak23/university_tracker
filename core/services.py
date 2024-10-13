# core/services.py

from django.core.exceptions import ValidationError

class ContractService:
    @staticmethod
    def validate_contract(contract):
        if not contract.streams.exists():
            raise ValidationError("Contract must have at least one stream.")
        if not contract.courses.exists():
            raise ValidationError("Contract must have at least one course.")
        if not contract.contract_files.exists():
            raise ValidationError("Contract must have at least one contract file.")