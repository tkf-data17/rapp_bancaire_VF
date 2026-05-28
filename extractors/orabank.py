import re
import pandas as pd
from .base import BaseExtractor
from _00_logger import log

try:
    import fitz
except ImportError:
    fitz = None

_BOUNDS = {
    "date_limit":    90,
    "libelle_limit": 260,
    "valeur_limit":  350,
    "debit_limit":   430,
    "credit_limit":  515
}


class OrabankExtractor(BaseExtractor):

    def extract_transactions(self, pdf_path: str) -> pd.DataFrame:
        if not fitz:
            raise ImportError("PyMuPDF non installé. pip install PyMuPDF")

        log("DEBUG", "orabank", "Analyse layout PDF", {"pdf": pdf_path})
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

                # Troncature sur les lignes de totaux fusionnées
                trunc_index = -1
                matches_total_footer = False

                for i, w in enumerate(line_words):
                    if "total" in w[4].lower():
                        snippet = "".join([wx[4] for wx in line_words[i:i+8]]).replace(" ", "").lower()
                        clean_snippet = snippet.replace("é", "e").replace("è", "e")
                        if any(p in clean_snippet for p in [
                            "totalgeneral", "totalmouvements", "totaldesmouvements",
                            "totaldeb", "totalcred"
                        ]):
                            trunc_index = i
                            matches_total_footer = True
                            break
                        if "totalgénéral" in w[4].replace(" ", "").lower():
                            trunc_index = i
                            matches_total_footer = True
                            break

                if trunc_index != -1:
                    line_words = line_words[:trunc_index]
                    if matches_total_footer and not line_words:
                        if current_tx:
                            transactions.append(current_tx)
                            current_tx = {}
                        continue
                    if not line_words:
                        continue

                full_line_text = " ".join([w[4] for w in line_words])

                ignore_patterns = [
                    "Libellé", "Valeur", "Débit", "Crédit", "Solde",
                    "Solde précédent",
                    "Edité le", "www.orabank.net", "ORABANK", "Capital de", "RCCM",
                    "Veuillez noter", "Place de l'indépendance", "Tél. :",
                    "Total général", "Total des mouvements",
                    "RELEVE D'IDENTITE BANCAIRE", "EXTRAIT DE COMPTE",
                ]

                should_skip = any(p in full_line_text for p in ignore_patterns)
                if "Page" in full_line_text and "/" in full_line_text:
                    should_skip = True
                if "Date" in full_line_text and "Libellé" in full_line_text:
                    should_skip = True

                if should_skip:
                    continue

                first_word_x = line_words[0][0]
                first_word_text = line_words[0][4]

                if (first_word_x < _BOUNDS["date_limit"]
                        and re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", first_word_text)):
                    if current_tx:
                        transactions.append(current_tx)
                    current_tx = {
                        "Date": "", "Date Valeur": "", "Libellé": "",
                        "Débit": "", "Crédit": "", "Solde": ""
                    }

                if not current_tx:
                    continue

                for w in line_words:
                    x, text = w[0], w[4]

                    if x < _BOUNDS["date_limit"]:
                        if not current_tx["Date"]:
                            current_tx["Date"] = text
                    elif x < _BOUNDS["libelle_limit"]:
                        current_tx["Libellé"] += text + " "
                    elif x < _BOUNDS["valeur_limit"]:
                        current_tx["Date Valeur"] += text
                    else:
                        cleaned_digits = re.sub(r'[^\d]', '', text)
                        is_amount_like = (
                            not re.search(r'[a-zA-Z/]', text)
                            and len(cleaned_digits) < 10
                        )
                        if x < _BOUNDS["debit_limit"]:
                            target_col = "Débit"
                        elif x < _BOUNDS["credit_limit"]:
                            target_col = "Crédit"
                        else:
                            target_col = "Solde"

                        if is_amount_like:
                            current_tx[target_col] += text
                        else:
                            current_tx["Libellé"] += text + " "

                if matches_total_footer and current_tx:
                    transactions.append(current_tx)
                    current_tx = {}

        if current_tx:
            transactions.append(current_tx)

        doc.close()

        if not transactions:
            log("WARN", "orabank", "Aucune transaction extraite", {"pdf": pdf_path})
            return pd.DataFrame()

        df = pd.DataFrame(transactions)
        log("INFO", "orabank", "Transactions extraites", {"pdf": pdf_path, "nb": len(df)})

        if 'Libellé' in df.columns:
            df['Libellé'] = df['Libellé'].str.replace('|', '', regex=False).str.strip()
            df['Libellé'] = df['Libellé'].str.replace(r'\s+', ' ', regex=True)

        return df.rename(columns={
            "Date": "date", "Date Valeur": "date_valeur",
            "Libellé": "libelle", "Débit": "debit",
            "Crédit": "credit", "Solde": "solde"
        })

    def get_solde_precedent(self, pdf_path: str) -> float:
        if not fitz:
            return 0.0
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            words = page.get_text("words")
            doc.close()

            solde_label_y = -1
            for w in words:
                if "précédent" in w[4] and solde_label_y == -1:
                    solde_label_y = w[1]
                    break

            if solde_label_y != -1:
                montant_parts = []
                for w in words:
                    if abs(w[1] - solde_label_y) < 5:
                        x, text = w[0], w[4]
                        if x > 300 and re.match(r'^[\d.,]+$', text):
                            montant_parts.append(text)
                if montant_parts:
                    full_str = "".join(montant_parts)
                    try:
                        return float(full_str.replace('.', '').replace(',', ''))
                    except Exception:
                        return float(re.sub(r'[^\d]', '', full_str))
        except Exception as e:
            log("ERROR", "orabank", "Erreur extraction solde précédent", {"pdf": pdf_path}, exc=e)

        return 0.0
