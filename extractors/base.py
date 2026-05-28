import pandas as pd
from abc import ABC, abstractmethod


class BaseExtractor(ABC):

    @abstractmethod
    def extract_transactions(self, pdf_path: str) -> pd.DataFrame:
        """
        Extrait les transactions d'un PDF.
        Retourne un DataFrame avec les colonnes : date, libelle, debit, credit, solde
        """
        pass

    @abstractmethod
    def get_solde_precedent(self, pdf_path: str) -> float:
        """Retourne le solde d'ouverture trouvé dans le PDF."""
        pass
