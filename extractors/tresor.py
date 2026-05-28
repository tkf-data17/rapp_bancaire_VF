import re
import pandas as pd
from .base import BaseExtractor
from _00_logger import log

try:
    import fitz
except ImportError:
    fitz = None

# Bornes x de chaque colonne (limite droite)
_BOUNDS = {
    "date":       55,
    "libelle":   235,
    "reference": 275,
    "valeur":    350,
    "debit":     440,
    "credit":    520
    # x >= 520 → solde
}

_IGNORE_PATTERNS = [
    "Date", "Libélle", "Reférence", "Valeur", "Débit", "Crédit", "Solde",
    "Dernier solde avant",
    "Total des mouvements", "Nouveau solde",
    "Sauf erreur",
    "BANQUE DE DEPOTS DU TRESOR",
    "dob@", "BP 324", "Tél +228",
    "Rubrique comptable", "Relevé Du",
]


class TresorExtractor(BaseExtractor):

    def extract_transactions(self, pdf_path: str) -> pd.DataFrame:
        if not fitz:
            raise ImportError("PyMuPDF non installé. pip install PyMuPDF")

        log("DEBUG", "tresor", "Analyse layout PDF", {"pdf": pdf_path})
        doc = fitz.open(pdf_path)
        transactions = []
        current_tx = {}

        for page in doc:
            words = page.get_text("words")
            if not words:
                continue

            lines = {}
            for w in words:
                y1 = int(w[3])
                lines.setdefault(y1, []).append(w)

            for y, line_words in sorted(lines.items()):
                line_words.sort(key=lambda x: x[0])
                if not line_words:
                    continue

                full_line_text = " ".join([w[4] for w in line_words])

                # Arrêt sur les lignes de totaux/pieds
                if any(p.lower() in full_line_text.lower() for p in _IGNORE_PATTERNS):
                    # Sauvegarder la transaction courante avant de passer
                    if any(p in full_line_text for p in ["Total des mouvements", "Nouveau solde"]):
                        if current_tx:
                            transactions.append(current_tx)
                            current_tx = {}
                    continue

                first_word_x = line_words[0][0]
                first_word_text = line_words[0][4]

                # Nouvelle transaction : date au format DD.MM.YYYY
                if (first_word_x < _BOUNDS["date"]
                        and re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", first_word_text)):
                    if current_tx:
                        transactions.append(current_tx)
                    current_tx = {
                        "Date": "", "Date Valeur": "", "Référence": "",
                        "Libellé": "", "Débit": "", "Crédit": "", "Solde": ""
                    }

                if not current_tx:
                    continue

                for w in line_words:
                    x, text = w[0], w[4]

                    if x < _BOUNDS["date"]:
                        if not current_tx["Date"]:
                            # DD.MM.YYYY → DD/MM/YYYY pour compatibilité downstream
                            current_tx["Date"] = text.replace(".", "/")
                    elif x < _BOUNDS["libelle"]:
                        current_tx["Libellé"] += text + " "
                    elif x < _BOUNDS["reference"]:
                        current_tx["Référence"] += text
                    elif x < _BOUNDS["valeur"]:
                        current_tx["Date Valeur"] += text.replace(".", "/")
                    else:
                        # Zone montants
                        cleaned_digits = re.sub(r'[^\d]', '', text)
                        is_amount_like = (
                            not re.search(r'[a-zA-Z]', text)
                            and len(cleaned_digits) < 12
                        )
                        if x < _BOUNDS["debit"]:
                            target_col = "Débit"
                        elif x < _BOUNDS["credit"]:
                            target_col = "Crédit"
                        else:
                            target_col = "Solde"

                        if is_amount_like:
                            current_tx[target_col] += text
                        else:
                            current_tx["Libellé"] += text + " "

        if current_tx:
            transactions.append(current_tx)

        doc.close()

        if not transactions:
            log("WARN", "tresor", "Aucune transaction extraite", {"pdf": pdf_path})
            return pd.DataFrame()

        df = pd.DataFrame(transactions)
        log("INFO", "tresor", "Transactions extraites", {"pdf": pdf_path, "nb": len(df)})

        if 'Libellé' in df.columns:
            df['Libellé'] = df['Libellé'].str.strip().str.replace(r'\s+', ' ', regex=True)

        # Supprimer la partie décimale ",XX" sur les montants avant le nettoyage commun
        for col in ['Débit', 'Crédit', 'Solde']:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda v: re.sub(r',\d+$', '', str(v).strip()) if isinstance(v, str) else v
                )

        return df.rename(columns={
            "Date": "date", "Date Valeur": "date_valeur",
            "Référence": "reference", "Libellé": "libelle",
            "Débit": "debit", "Crédit": "credit", "Solde": "solde"
        })

    def get_solde_precedent(self, pdf_path: str) -> float:
        """Cherche la ligne 'Dernier solde avant' et retourne le montant de la colonne Solde."""
        if not fitz:
            return 0.0
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            words = page.get_text("words")
            doc.close()

            dernier_y = -1
            for w in words:
                if w[4].lower() == "dernier":
                    dernier_y = w[1]
                    break

            if dernier_y != -1:
                montant_parts = []
                for w in words:
                    if abs(w[1] - dernier_y) < 5 and w[0] > _BOUNDS["credit"]:
                        text = w[4]
                        if re.match(r'^[\d\s,\.]+$', text):
                            montant_parts.append(text)
                if montant_parts:
                    full_str = "".join(montant_parts)
                    full_str = re.sub(r',\d+$', '', full_str)
                    cleaned = re.sub(r'[^\d]', '', full_str)
                    try:
                        return float(cleaned)
                    except Exception:
                        pass
        except Exception as e:
            log("ERROR", "tresor", "Erreur extraction solde précédent", {"pdf": pdf_path}, exc=e)

        return 0.0
