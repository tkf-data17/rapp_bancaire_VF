from .orabank import OrabankExtractor
from .tresor import TresorExtractor

__all__ = ["OrabankExtractor", "TresorExtractor", "BankExtractorFactory"]


class BankExtractorFactory:
    _registry = {
        "orabank" : OrabankExtractor,
        "trésor"  : TresorExtractor,
        "tresor"  : TresorExtractor,
    }

    @staticmethod
    def get(bank_name: str):
        key = (bank_name or "orabank").strip().lower()
        cls = BankExtractorFactory._registry.get(key)
        if cls is None:
            supported = list(BankExtractorFactory._registry.keys())
            raise ValueError(
                f"Banque non supportée : '{bank_name}'. "
                f"Banques disponibles : {supported}"
            )
        return cls()

    @staticmethod
    def list_banks():
        return list(BankExtractorFactory._registry.keys())
