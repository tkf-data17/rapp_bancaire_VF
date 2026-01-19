"""
Script d'extraction des transactions bancaires sur le relevé Orabank à partir d'un PDF.
Utilise PyMuPDF (fitz) et l'analyse de layout (coordonnées) pour une extraction précise.
"""

import pandas as pd
import re
import os
import sys
import shutil
import config
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Définition des bornes de colonnes (estimées d'après l'analyse)
# Date < 90
# Libellé: 90 - 280
# Valeur: 280 - 350
# Débit: 350 - 430
# Crédit: 430 - 515
# Solde: > 515


COLUMN_BOUNDS = {
    "date_limit": 90,
    "libelle_limit": 260, # Reduced from 280 to capture Date Value starting around 280 more reliably
    "valeur_limit": 350,
    "debit_limit": 430,
    "credit_limit": 515
}

def clean_amount(text: str) -> float:
    """Nettoie une chaîne de montant et la convertit en float."""
    if not text:
        return 0.0
    # Enlever les espaces et caractères non numériques (sauf virgule/point)
    # Format '767 000' -> 767000
    cleaned = re.sub(r'[^\d]', '', text)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def extract_transactions_from_pdf(pdf_path: str) -> pd.DataFrame:
    """
    Extrait les transactions en utilisant les coordonnées des mots.
    """
    if not fitz:
        raise ImportError("Le module 'PyMuPDF' n'est pas installé. pip install PyMuPDF")

    print(f"📄 Analyse précise (layout) du fichier PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    transactions = []
    
    # Variables pour suivre l'état courant
    current_tx = {}
    
    for page_num, page in enumerate(doc):
        words = page.get_text("words")
        if not words:
            continue

        # Reconstruire les lignes en se basant sur la coordonnée verticale (y)
        # Ceci est plus robuste que de se fier aux numéros de ligne/bloc de PyMuPDF
        lines = {}
        for w in words:
            # Regrouper les mots par leur coordonnée y1 (partie entière)
            y1 = int(w[3]) 
            if y1 not in lines:
                lines[y1] = []
            lines[y1].append(w)
        
        # Trier les lignes par leur position verticale
        sorted_lines = sorted(lines.items())

        for y, line_words in sorted_lines:
            line_words.sort(key=lambda x: x[0]) # Trier les mots par leur position x
            
            if not line_words:
                continue
            
            # --- TRONCATURE DES TOTAUX FUSIONNÉS ---
            # Si "Total général" est détecté, on coupe la ligne à cet endroit
            # pour ne garder que la transaction qui précède.
            trunc_index = -1
            matches_total_footer = False
            
            for i, w in enumerate(line_words):
                # Check simple "Total" (insensible à la casse)
                if "total" in w[4].lower():
                    # Vérifier le contexte
                    snippet = "".join([wx[4] for wx in line_words[i:i+8]]).replace(" ", "").lower()
                    
                    # with open("debug_total.log", "a", encoding="utf-8") as f:
                    #     f.write(f"Word: {w[4]}, Snippet: {snippet}\n")

                    # Normalisation stricte pour détection
                    clean_snippet = snippet.replace("é", "e").replace("è", "e")
                    
                    if ("totalgeneral" in clean_snippet or 
                        "totalmouvements" in clean_snippet or 
                        "totaldesmouvements" in clean_snippet or 
                        "totaldeb" in clean_snippet or
                        "totalcred" in clean_snippet):
                         trunc_index = i
                         matches_total_footer = True
                         break
                    
                    # Check direct variations in the word itself or next word
                    if "totalgénéral" in w[4].replace(" ", "").lower():

                         trunc_index = i
                         matches_total_footer = True
                         break
            
            if trunc_index != -1:
                line_words = line_words[:trunc_index]

                
                # Si c'était un footer "Total", on doit clôre la transaction courante
                # car les lignes suivantes risquent d'être les montants de ce total
                if matches_total_footer:
                    # Cas 1: La ligne ne contenait QUE le total (donc line_words est vide maintenant)
                    # On ferme tout de suite.
                    if not line_words:
                        if current_tx:
                            transactions.append(current_tx)
                            current_tx = {}
                        continue # On passe la ligne
                
                if not line_words: continue # Si la ligne ne contenait que le total (cas non total_general aussi), on passe
            
            # Filter Header/Footer based on content
            full_line_text = " ".join([w[4] for w in line_words])
            
            # Suppression des lignes inutiles (En-têtes, Pieds de page, Mentions légales)
            ignore_patterns = [
                "Date", "Libellé", "Valeur", "Débit", "Crédit", "Solde", # En-tête tableau
                "Solde précédent", # Ligne de solde initial
                "Page", "Edité le", "www.orabank.net", "ORABANK", "Capital de", "RCCM", # Pied de page
                "Veuillez noter que vous disposez", "Place de l'indépendance", "Tél. :", # Mentions légales
                "Total général", "Total des mouvements", # Totaux
                "RELEVE D'IDENTITE BANCAIRE", "EXTRAIT DE COMPTE" # En-têtes parasites
            ]
            
            should_skip = False
            for pattern in ignore_patterns:
                if pattern in full_line_text:
                    if pattern == "Date" and not ("Date" in full_line_text and "Libellé" in full_line_text):
                        # Attention à ne pas filtrer une ligne qui contiendrait juste le mot "Date" par hasard dans le libellé ?
                        # Mais ici on filtre l'en-tête, qui contient "Date" ET "Libellé"
                         pass
                    elif pattern == "Page":
                         if "/" in full_line_text: should_skip = True
                    else:
                        should_skip = True
            
            # Raffinement pour l'en-tête exact
            if "Date" in full_line_text and "Libellé" in full_line_text:
                should_skip = True
                
            if should_skip:
                continue

            first_word_x = line_words[0][0]
            first_word_text = line_words[0][4]
            
            # Check for New Transaction (Date in first column)
            if first_word_x < COLUMN_BOUNDS["date_limit"] and re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", first_word_text):
                # Save previous
                if current_tx:
                    transactions.append(current_tx)
                
                # New Tx
                current_tx = {
                    "Date": "",
                    "Date Valeur": "",
                    "Libellé": "",
                    "Débit": "",
                    "Crédit": "",
                    "Solde": ""
                }
            
            # Si pas de transaction active, on ignore (ex: texte avant le tableau)
            if not current_tx:
                continue

            # Distribute words to columns
            for w in line_words:
                x, text = w[0], w[4]
                
                # Special handling: "Date" in Date column is already handled by new tx check,
                # but we need to capture the text.
                # However, ensure we don't capture Libelle content that overflows left (rare)
                
                if x < COLUMN_BOUNDS["date_limit"]:
                    # Avoid appending duplicate date if we just created it? 
                    # Actually valid date is only one word.
                    # Use = instead of += for Date to avoid "06/10/202506/10/2025" if line repeats? 
                    # Usually Date is single word.
                    if not current_tx["Date"]:
                         current_tx["Date"] = text
                    # Else ignore? Or could be a multiline date (unlikely)
                    
                elif x < COLUMN_BOUNDS["libelle_limit"]:
                    current_tx["Libellé"] += text + " "
                
                elif x < COLUMN_BOUNDS["valeur_limit"]:
                    # Date Valeur - keep as is, usually dates
                    current_tx["Date Valeur"] += text
                    
                else:
                    # Débit (350-430), Crédit (430-515), Solde (>515)
                    # Heuristic: If the word contains letters or slashes (dates), it's likely a Libellé spillover.
                    # Also check length: A single word representing an amount part shouldn't be excessively long (e.g. RIB/ID).
                    # Valid amounts in this PDF are space-separated (e.g. "3 298 028"), so words are length 1-3.
                    # We allow up to 6 to support "100000" but reject "0110124" (7 digits) or RIB (11+).
                    
                    cleaned_digits = re.sub(r'[^\d]', '', text)
                    is_amount_like = (
                        not re.search(r'[a-zA-Z/]', text) and 
                        len(cleaned_digits) < 10
                    )
                    
                    target_col = ""
                    if x < COLUMN_BOUNDS["debit_limit"]:
                        target_col = "Débit"
                    elif x < COLUMN_BOUNDS["credit_limit"]:
                        target_col = "Crédit"
                    else:
                        target_col = "Solde"
                    
                    if is_amount_like:
                        current_tx[target_col] += text
                    else:
                        # It's spillover text, put it back in Libellé
                        current_tx["Libellé"] += text + " "
            
            # Si c'était la ligne de total (cas mixte), on ferme la transaction maintenant
            if matches_total_footer:
                if current_tx:
                    transactions.append(current_tx)
                    current_tx = {}

    # Add last
    if current_tx:
        transactions.append(current_tx)
        
    doc.close()
    
    if not transactions:
        return pd.DataFrame()
        
    df = pd.DataFrame(transactions)
    
    # Cleaning
    if 'Libellé' in df.columns:
        df['Libellé'] = df['Libellé'].str.replace('|', '', regex=False).str.strip()
        df['Libellé'] = df['Libellé'].str.replace(r'\s+', ' ', regex=True)
        
    df = df.rename(columns={
        "Date": "date",
        "Date Valeur": "date_valeur",
        "Libellé": "libelle",
        "Débit": "debit",
        "Crédit": "credit",
        "Solde": "solde"
    })
    
    return df

def get_solde_precedent(pdf_path: str) -> float:
    """Extrait le solde précédent en utilisant les coordonnées (plus sûr)."""
    if not fitz: return 0.0
    
    try:
        doc = fitz.open(pdf_path)
        # On ne regarde que la première page généralement pour le solde précédent
        page = doc[0] 
        words = page.get_text("words")
        doc.close()
        
        # Trouver la ligne "Solde précédent"
        # On cherche les mots "Solde" et "précédent" qui sont proches
        solde_label_y = -1
        
        for w in words:
            if "précédent" in w[4] and solde_label_y == -1:
                # Vérifier si "Solde" est juste avant ou sur la même ligne
                # Pour simplifier, on suppose que si on trouve "précédent" isolé ou "Solde précédent", c'est bon.
                # Dans le debug, "Solde" (187) et "précédent" (216) sont sur la même "line" (item 94, 95).
                solde_label_y = w[1] # y0 coord
                break
        
        if solde_label_y != -1:
            # Chercher des montants sur la même ligne (avec une marge d'erreur Y)
            # Le montant est normalement dans la colonne Solde (> 515)
            montant_parts = []
            
            for w in words:
                # Marge d'erreur de +/- 5 pixels sur Y
                if abs(w[1] - solde_label_y) < 5:
                    text = w[4]
                    x = w[0]
                    
                    # On veut les chiffres qui sont à droite du label (disons > 300)
                    if x > 300 and re.match(r'^[\d.,]+$', text):
                         montant_parts.append(text)
            
            if montant_parts:
                full_str = "".join(montant_parts)
                # Nettoyer
                try:
                    return float(full_str.replace('.', '').replace(',', ''))
                except:
                    # Retry light clean
                     return float(re.sub(r'[^\d]', '', full_str))
                     
    except Exception as e:
        print(f"⚠️ Erreur extraction solde précédent: {e}")
        
    return 0.0


def clean_and_format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie et formate le DataFrame (Adapté)."""
    
    # Nettoyage des montants
    for col in ['debit', 'credit', 'solde']:
        if col in df.columns:
            # Fonction locale de nettoyage
            def clean_val(x):
                if not isinstance(x, str): return x
                # Garder chiffres
                c = re.sub(r'[^\d]', '', x)
                if not c: return 0.0
                return float(c)
            
            df[col] = df[col].apply(clean_val)
    
    # Dates
    for col in ['date', 'date_valeur']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce').dt.date

    # Filtrer les lignes vides (si date invalide)
    if 'date' in df.columns:
        df = df.dropna(subset=['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
    return df

def check_and_correct_balances(df: pd.DataFrame, start_solde: float) -> pd.DataFrame:
    """
    Vérifie la cohérence des soldes (Solde Prec +/- Mvt = Solde Fin)
    et tente de corriger automatiquement les erreurs d'OCR (ex: 29 au lieu de 2).
    """
    if df.empty or 'solde' not in df.columns:
        return df

    # Le solde calculé précédent (n-1) commence au solde initial
    solde_precedent_calcule = start_solde
    corrected_count = 0
    
    print(f"\n🔧 Vérification et correction des soldes (Départ: {start_solde:,.0f})")

    def is_plausible(original_val: float, suggested_val: float) -> bool:
        """
        Vérifie si la valeur suggérée est une 'correction crédible' de la valeur originale
        (ex: erreur OCR, chiffre en trop, faute de frappe).
        Ne valide PAS une valeur totalement différente.
        """
        s_orig = str(int(original_val))
        s_sugg = str(int(suggested_val))
        
        # 0. Import (local d'urgence ou en haut du fichier idéalement)
        import difflib

        # 1. Identité (pas de changement)
        if s_orig == s_sugg: return True
        
        # 2. Spillover / Préfixe en trop (ex: "29979725" -> "2979725")
        # ou Suffixe en trop (ex: "32980282224" -> "329802822")
        # Si le suggéré est contenu dans l'original
        if (s_orig.endswith(s_sugg) or s_orig.startswith(s_sugg)) and len(s_orig) > len(s_sugg):
            return True
        
        # 3. Fuzzy match (Insertion d'un chiffre parasite au milieu ex: 29979 vs 2979)
        # Ratio de similitude > 0.85
        ratio = difflib.SequenceMatcher(None, s_orig, s_sugg).ratio()
        if ratio > 0.85:
            return True
            
        # 4. Un chiffre en trop (Noise) n'importe où
        # Si en retirant 1 char de s_orig on tombe sur s_sugg
        if len(s_orig) == len(s_sugg) + 1:
            for k in range(len(s_orig)):
                temp = s_orig[:k] + s_orig[k+1:]
                if temp == s_sugg:
                    return True
        
        return False

    for i, row in df.iterrows():
        # 1. Récupération des données lues
        solde_lu_n = row.get('solde', 0.0)
        debit_lu_n = row.get('debit', 0.0)
        credit_lu_n = row.get('credit', 0.0)
        
        # 0. Pré-vérification du Solde Lu
        # Si le Solde Lu est corrompu (ex: "3298...24" au lieu de "3298..."), on le corrige d'abord
        # en se basant sur le Solde Précédent + Mouvements Lus (si ceux-ci semblent corrects/petits par rapport à la corruption)
        solde_theo_transactions = solde_precedent_calcule + credit_lu_n - debit_lu_n
        
        if abs(solde_lu_n - solde_theo_transactions) > 1.0:
             # Si le solde théorique (calculé) est une version "propre" du solde lu
             if is_plausible(solde_lu_n, solde_theo_transactions):
                 print(f"  ✅ Correction Solde Ligne {i+1}: {solde_lu_n:,.0f} -> {solde_theo_transactions:,.0f}")
                 df.at[i, 'solde'] = solde_theo_transactions
                 solde_lu_n = solde_theo_transactions # Mise à jour locale pour la suite
        
        # 2. Calcul du mouvement théorique (Net)
        # Net = Solde(n) - Solde(n-1)
        # Si positif => Crédit. Si négatif => Débit.
        mouvement_net_theorique = solde_lu_n - solde_precedent_calcule
        
        applied_correction = False
        
        # Cas A: On s'attend à un CRÉDIT (Solde augmente)
        if mouvement_net_theorique > 0:
            theorique_credit = mouvement_net_theorique
            
            # Si on a extrait un débit par erreur, ou un crédit faux
            if abs(credit_lu_n - theorique_credit) > 1.0:
                 libelle_val = str(row.get('libelle', '')).strip()
                 first_word = libelle_val.split(' ')[0] if ' ' in libelle_val else libelle_val
                 
                 # Scénario 0: Le montant est dans le Libellé (spillover gauche)
                 # Ex: Libellé = "2812950 ESPECE..." et Credit = 0
                 if credit_lu_n == 0 and clean_amount(first_word) == theorique_credit:
                     print(f"  ✅ Correction Spillover Ligne {i+1} (Libellé->Crédit): {first_word} -> {theorique_credit:,.0f}")
                     df.at[i, 'credit'] = theorique_credit
                     # Nettoyer le libellé
                     new_lib = libelle_val[len(first_word):].strip()
                     df.at[i, 'libelle'] = new_lib
                     applied_correction = True
                 
                 # Scénario 1 : Le montant est dans Crédit mais mal lu (ex: 29M vs 2M)
                 elif credit_lu_n > 0 and is_plausible(credit_lu_n, theorique_credit):
                     print(f"  ✅ Correction Plausible Ligne {i+1} (Crédit): {credit_lu_n:,.0f} -> {theorique_credit:,.0f}")
                     df.at[i, 'credit'] = theorique_credit
                     df.at[i, 'debit'] = 0.0
                     applied_correction = True
                 
                 # Scénario 2 : Le montant a été mis dans Débit par erreur ? (Peu probable ici mais possible)
                 elif debit_lu_n > 0 and is_plausible(debit_lu_n, theorique_credit):
                     print(f"  ✅ Correction Colonne Ligne {i+1} (Débit->Crédit): {debit_lu_n:,.0f} -> {theorique_credit:,.0f}")
                     df.at[i, 'credit'] = theorique_credit
                     df.at[i, 'debit'] = 0.0
                     applied_correction = True
        
        # Cas B: On s'attend à un DÉBIT (Solde diminue)     
        elif mouvement_net_theorique < 0:
            theorique_debit = abs(mouvement_net_theorique)
            
            if abs(debit_lu_n - theorique_debit) > 1.0:
                 libelle_val = str(row.get('libelle', '')).strip()
                 first_word = libelle_val.split(' ')[0] if ' ' in libelle_val else libelle_val
                 
                 # Scénario 0: Spillover Libellé
                 if debit_lu_n == 0 and clean_amount(first_word) == theorique_debit:
                     print(f"  ✅ Correction Spillover Ligne {i+1} (Libellé->Débit): {first_word} -> {theorique_debit:,.0f}")
                     df.at[i, 'debit'] = theorique_debit
                     # Nettoyer libellé
                     new_lib = libelle_val[len(first_word):].strip()
                     df.at[i, 'libelle'] = new_lib
                     applied_correction = True

                 elif debit_lu_n > 0 and is_plausible(debit_lu_n, theorique_debit):
                     print(f"  ✅ Correction Plausible Ligne {i+1} (Débit): {debit_lu_n:,.0f} -> {theorique_debit:,.0f}")
                     df.at[i, 'debit'] = theorique_debit
                     df.at[i, 'credit'] = 0.0
                     applied_correction = True
                      
                 elif credit_lu_n > 0 and is_plausible(credit_lu_n, theorique_debit):
                     print(f"  ✅ Correction Colonne Ligne {i+1} (Crédit->Débit): {credit_lu_n:,.0f} -> {theorique_debit:,.0f}")
                     df.at[i, 'debit'] = theorique_debit
                     df.at[i, 'credit'] = 0.0
                     applied_correction = True
        
        if applied_correction:
            corrected_count += 1
            
        # 6. Mise à jour pour la boucle suivante
        # IMPORTANT : On prend le solde LU comme référence, SAUF si le user veut qu'on recalcule tout.
        # Mais pour de la correction OCR, faire confiance au Solde écrit (souvent OCRisé plus proprement ou check digits) est mieux.
        # Toutefois, si le Solde lui-même est faux, tout s'écroule.
        solde_precedent_calcule = solde_lu_n 
    
    if corrected_count > 0:
        print(f"✨ {corrected_count} corrections plausibles appliquées.")
    else:
        print("✅ Aucune correction nécessaire.")
        
    return df

def analyze_and_export(df: pd.DataFrame, output_prefix: str = "transactions", solde_precedent: float = 0.0, output_dir: str = config.output_dir):
    print("\n" + "="*70); print("📊 ANALYSE DES TRANSACTIONS"); print("="*70)
    
    # Ajouter le solde précédent au DataFrame pour l'export
    # On l'insère en première position
    if solde_precedent != 0.0:
        print(f"🏦 Solde précédent détecté: {solde_precedent:,.0f} FCFA")
        # Créer une ligne de départ
        first_date = df['date'].iloc[0] if not df.empty and 'date' in df.columns else None
        
        row_solde = {
            "date": first_date,
            "date_valeur": first_date,
            "libelle": "SOLDE PRECEDENT",
            "debit": 0.0,
            "credit": 0.0,
            "solde": solde_precedent
        }
        # Concaténer au début (pandas concat est mieux que append qui est déprécié)
        df_solde = pd.DataFrame([row_solde])
        df_final = pd.concat([df_solde, df], ignore_index=True)
    else:
        df_final = df.copy()

    if df.empty: print("❌ Aucune transaction à analyser"); return
    
    print(f"📈 Nombre de transactions: {len(df)}")
    if 'debit' in df.columns: print(f"💸 Total des débits: {df['debit'].sum():,.0f} FCFA")
    
    df_export = df_final.copy() # Travailler sur le DF avec solde
    
    # Format dates for Excel
    for col in ['date', 'date_valeur']:
        if col in df_export.columns: 
            df_export[col] = pd.to_datetime(df_export[col]).dt.strftime('%d/%m/%Y')
            
    # Création du dossier de sortie s'il n'existe pas
    # Création du dossier de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)

    csv_file = os.path.join(output_dir, f"{output_prefix}.csv")
    df_export.to_csv(csv_file, index=False, encoding='utf-8-sig', sep=';') # Point-virgule pour Excel FR
    print(f"\n✅ Exporté vers: {csv_file}")
    
    # try:
    #     excel_file = os.path.join(output_dir, f"{output_prefix}.xlsx")
    #     try:
    #         df_export.to_excel(excel_file, index=False)
    #         print(f"✅ Exporté vers: {excel_file}")
    #     except PermissionError:
    #         print(f"⚠️ Impossible d'écrire dans {excel_file}. Le fichier est-il ouvert dans Excel ?")
            
    # except ImportError:
    #     print("\n💡 Pour exporter vers Excel, installez openpyxl: pip install openpyxl")



def batch_process_pdf_folder(source_dir=config.input_dir, output_dir=config.output_dir):
    """
    Parcourt tous les fichiers PDF du dossier source et lance l'extraction pour chacun.
    """
    if not os.path.exists(source_dir):
        print(f"❌ Le dossier {source_dir} n'existe pas.")
        return

    # Nettoyage du dossier de sortie "extraction_files"
    if os.path.exists(output_dir):
        print(f"🧹 Nettoyage du dossier de sortie : '{output_dir}'")
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"⚠️ Impossible de supprimer {file_path}: {e}")
    else:
        os.makedirs(output_dir)
        print(f"📁 Création du dossier de sortie : '{output_dir}'")

    # Lister les PDF
    files = [f for f in os.listdir(source_dir) if f.strip().lower().endswith(".pdf")]
    
    # Tri naturel pour traiter page_1, page_2... dans l'ordre
    files.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
    
    print(f"\n🚀 Démarrage du traitement par lot dans: {source_dir}")
    print(f"📂 {len(files)} fichiers trouvés.\n")
    
    for filename in files:
        pdf_path = os.path.join(source_dir, filename)
        print(f"👉 Traitement de {filename}...")
        
        try:
            # 1. Solde
            solde_prec = get_solde_precedent(pdf_path)
            
            # 2. Extraction
            df = extract_transactions_from_pdf(pdf_path)
            
            # 3. Export
            if not df.empty:
                print(f"   ✅ {len(df)} transactions.")
                df_clean = clean_and_format_dataframe(df)
                
                # Correction d'erreurs OCR via le solde
                df_clean = check_and_correct_balances(df_clean, solde_prec)
                
                # Nom du fichier de sortie basé sur le PDF
                output_name = os.path.splitext(filename)[0]
                analyze_and_export(df_clean, output_name, solde_prec, output_dir=output_dir)
            else:
                print("   ⚠️ Aucune transaction trouvée sur cette page.")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print("-" * 50)


#-------------------------------------------------------------------------------------------------
# Fonction pour parcourir le dossier de sauvegarde et recréér le dataframe complet
#-------------------------------------------------------------------------------------------------
def process_all_pdf_files(output_dir, final_output_name, start_solde=None):
    """
    Parcourt le dossier extraction_files, lit les CSV et les combine dans l'ordre.
    Ignore le fichier global s'il existe déjà pour éviter la récursion lors de multiples exécutions.
    Applique la validation/correction des soldes si start_solde est fourni.
    """
    if not os.path.exists(output_dir):
        print(f"❌ Le dossier {output_dir} n'existe pas.")
        return pd.DataFrame()

    # Lister tous les fichiers CSV
    files = [f for f in os.listdir(output_dir) if f.endswith(".csv")]
    
    # Exclure le fichier de sortie s'il est déjà présent
    files = [f for f in files if final_output_name not in f]

    # Tri naturel (ex: page_2 avant page_10)
    # On extrait le premier nombre trouvé dans le nom du fichier
    def get_sort_key(filename):
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return int(numbers[0])
        return 0
    
    files.sort(key=get_sort_key)
    
    print(f"\n🔄 Fusion de {len(files)} fichiers CSV trouvés dans '{output_dir}'...")
    
    all_dfs = []
    for filename in files:
        filepath = os.path.join(output_dir, filename)
        try:
            # Lecture avec le séparateur point-virgule utilisé à l'export
            df = pd.read_csv(filepath, sep=';')
            # Ajout d'une colonne source pour traçabilité (optionnel)
            # df['source_file'] = filename
            all_dfs.append(df)
            print(f"  - Chargé: {filename} ({len(df)} lignes)")
        except Exception as e:
            print(f"  ⚠️ Erreur lors de la lecture de {filename}: {e}")

    if not all_dfs:
        print("❌ Aucun fichier valide n'a été chargé.")
        return pd.DataFrame()

    # Concaténation
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # -----------------------------------------------------------
    # Correction et Auto-Guérison des Soldes / Montants
    # -----------------------------------------------------------
    if start_solde is not None:
        try:
            full_df = check_and_correct_balances(full_df, start_solde)
        except Exception as e:
            print(f"⚠️ Erreur lors de la correction des soldes : {e}")
    
    # Ajout de la colonne N° d'ordre en première position
    full_df.insert(0, "N° d'ordre", range(1, len(full_df) + 1))
    
    # Export du résultat global
    output_csv = os.path.join(output_dir, f"{final_output_name}.csv")
    output_xlsx = os.path.join(output_dir, f"{final_output_name}.xlsx")
    
    print(f"\n💾 Sauvegarde du fichier global ({len(full_df)} lignes)...")
    
    full_df.to_csv(output_csv, index=False, sep=';', encoding='utf-8-sig')
    print(f"  ✅ CSV: {output_csv}")
    
    try:
        full_df.to_excel(output_xlsx, index=False)
        print(f"  ✅ Excel: {output_xlsx}")
    except ImportError:
        print("  ⚠️ Module openpyxl manquant pour l'export Excel.")
    except Exception as e:
        print(f"  ⚠️ Erreur export Excel: {e}")
        
    return full_df


