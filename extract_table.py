import pandas as pd
import re
import os
import shutil
import difflib
import config
from _00_logger import log


def clean_amount(text: str) -> float:
    if not text:
        return 0.0
    # Supprimer la partie décimale (",00") avant de nettoyer
    text = re.sub(r',\d+$', '', str(text).strip())
    cleaned = re.sub(r'[^\d]', '', text)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


# Wrappers de compatibilité (délèguent à OrabankExtractor)
def extract_transactions_from_pdf(pdf_path: str) -> pd.DataFrame:
    from extractors import OrabankExtractor
    return OrabankExtractor().extract_transactions(pdf_path)


def get_solde_precedent(pdf_path: str) -> float:
    from extractors import OrabankExtractor
    return OrabankExtractor().get_solde_precedent(pdf_path)


def clean_and_format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    for col in ['debit', 'credit', 'solde']:
        if col in df.columns:
            def clean_val(x):
                if not isinstance(x, str):
                    return x
                x = re.sub(r',\d+$', '', x.strip())
                c = re.sub(r'[^\d]', '', x)
                if not c:
                    return 0.0
                return float(c)
            df[col] = df[col].apply(clean_val)

    # dayfirst=True gère à la fois DD/MM/YYYY et DD.MM.YYYY
    for col in ['date', 'date_valeur']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce').dt.date

    if 'date' in df.columns:
        df = df.dropna(subset=['date'])
        df = df.sort_values('date').reset_index(drop=True)

    return df


def check_and_correct_balances(df: pd.DataFrame, start_solde: float) -> pd.DataFrame:
    if df.empty or 'solde' not in df.columns:
        return df

    solde_precedent_calcule = start_solde
    corrected_count = 0

    log("DEBUG", "extract_table", "Correction des soldes démarrée", {"nb_lignes": len(df), "solde_depart": start_solde})

    def is_plausible(original_val: float, suggested_val: float) -> bool:
        s_orig = str(int(original_val))
        s_sugg = str(int(suggested_val))

        if s_orig == s_sugg:
            return True
        if (s_orig.endswith(s_sugg) or s_orig.startswith(s_sugg)) and len(s_orig) > len(s_sugg):
            return True
        ratio = difflib.SequenceMatcher(None, s_orig, s_sugg).ratio()
        if ratio > 0.85:
            return True
        if len(s_orig) == len(s_sugg) + 1:
            for k in range(len(s_orig)):
                temp = s_orig[:k] + s_orig[k+1:]
                if temp == s_sugg:
                    return True
        return False

    for i, row in df.iterrows():
        solde_lu_n   = row.get('solde', 0.0)
        debit_lu_n   = row.get('debit', 0.0)
        credit_lu_n  = row.get('credit', 0.0)

        solde_theo_transactions = solde_precedent_calcule + credit_lu_n - debit_lu_n

        if abs(solde_lu_n - solde_theo_transactions) > 1.0:
            if is_plausible(solde_lu_n, solde_theo_transactions):
                print(f"  Correction Solde Ligne {i+1}: {solde_lu_n:,.0f} -> {solde_theo_transactions:,.0f}")
                log("INFO", "extract_table", "Correction solde ligne", {"ligne": i+1, "avant": solde_lu_n, "apres": solde_theo_transactions})
                df.at[i, 'solde'] = solde_theo_transactions
                solde_lu_n = solde_theo_transactions

        mouvement_net_theorique = solde_lu_n - solde_precedent_calcule
        applied_correction = False

        if mouvement_net_theorique > 0:
            theorique_credit = mouvement_net_theorique
            if abs(credit_lu_n - theorique_credit) > 1.0:
                libelle_val = str(row.get('libelle', '')).strip()
                first_word = libelle_val.split(' ')[0] if ' ' in libelle_val else libelle_val

                if credit_lu_n == 0 and clean_amount(first_word) == theorique_credit:
                    log("INFO", "extract_table", "Correction spillover crédit", {"ligne": i+1, "mot": first_word, "montant": theorique_credit})
                    df.at[i, 'credit'] = theorique_credit
                    df.at[i, 'libelle'] = libelle_val[len(first_word):].strip()
                    applied_correction = True
                elif credit_lu_n > 0 and is_plausible(credit_lu_n, theorique_credit):
                    log("INFO", "extract_table", "Correction plausible crédit", {"ligne": i+1, "avant": credit_lu_n, "apres": theorique_credit})
                    df.at[i, 'credit'] = theorique_credit
                    df.at[i, 'debit'] = 0.0
                    applied_correction = True
                elif debit_lu_n > 0 and is_plausible(debit_lu_n, theorique_credit):
                    log("INFO", "extract_table", "Correction colonne débit->crédit", {"ligne": i+1, "avant": debit_lu_n, "apres": theorique_credit})
                    df.at[i, 'credit'] = theorique_credit
                    df.at[i, 'debit'] = 0.0
                    applied_correction = True

        elif mouvement_net_theorique < 0:
            theorique_debit = abs(mouvement_net_theorique)
            if abs(debit_lu_n - theorique_debit) > 1.0:
                libelle_val = str(row.get('libelle', '')).strip()
                first_word = libelle_val.split(' ')[0] if ' ' in libelle_val else libelle_val

                if debit_lu_n == 0 and clean_amount(first_word) == theorique_debit:
                    log("INFO", "extract_table", "Correction spillover débit", {"ligne": i+1, "mot": first_word, "montant": theorique_debit})
                    df.at[i, 'debit'] = theorique_debit
                    df.at[i, 'libelle'] = libelle_val[len(first_word):].strip()
                    applied_correction = True
                elif debit_lu_n > 0 and is_plausible(debit_lu_n, theorique_debit):
                    log("INFO", "extract_table", "Correction plausible débit", {"ligne": i+1, "avant": debit_lu_n, "apres": theorique_debit})
                    df.at[i, 'debit'] = theorique_debit
                    df.at[i, 'credit'] = 0.0
                    applied_correction = True
                elif credit_lu_n > 0 and is_plausible(credit_lu_n, theorique_debit):
                    log("INFO", "extract_table", "Correction colonne crédit->débit", {"ligne": i+1, "avant": credit_lu_n, "apres": theorique_debit})
                    df.at[i, 'debit'] = theorique_debit
                    df.at[i, 'credit'] = 0.0
                    applied_correction = True

        if applied_correction:
            corrected_count += 1

        solde_precedent_calcule = solde_lu_n

    if corrected_count > 0:
        log("INFO", "extract_table", f"{corrected_count} corrections OCR appliquées")
    else:
        log("DEBUG", "extract_table", "Aucune correction nécessaire")

    return df


def analyze_and_export(df: pd.DataFrame, output_prefix: str = "transactions", solde_precedent: float = 0.0, output_dir: str = config.output_dir):
    print("\n" + "="*70)
    print("ANALYSE DES TRANSACTIONS")
    print("="*70)

    if solde_precedent != 0.0:
        first_date = df['date'].iloc[0] if not df.empty and 'date' in df.columns else None
        row_solde = {
            "date": first_date, "date_valeur": first_date,
            "libelle": "SOLDE PRECEDENT", "debit": 0.0, "credit": 0.0,
            "solde": solde_precedent
        }
        df_final = pd.concat([pd.DataFrame([row_solde]), df], ignore_index=True)
    else:
        df_final = df.copy()

    if df.empty:
        print("Aucune transaction a analyser")
        return

    print(f"Nombre de transactions: {len(df)}")
    if 'debit' in df.columns:
        print(f"Total des debits: {df['debit'].sum():,.0f} FCFA")

    df_export = df_final.copy()
    for col in ['date', 'date_valeur']:
        if col in df_export.columns:
            df_export[col] = pd.to_datetime(df_export[col]).dt.strftime('%d/%m/%Y')

    os.makedirs(output_dir, exist_ok=True)
    csv_file = os.path.join(output_dir, f"{output_prefix}.csv")
    df_export.to_csv(csv_file, index=False, encoding='utf-8-sig', sep=';')
    print(f"Exporte vers: {csv_file}")


def batch_process_pdf_folder(source_dir=config.input_dir, output_dir=config.output_dir, extractor=None):
    """
    Parcourt tous les fichiers PDF du dossier source et lance l'extraction.
    extractor : instance de BaseExtractor (OrabankExtractor par défaut)
    """
    if extractor is None:
        from extractors import OrabankExtractor
        extractor = OrabankExtractor()

    if not os.path.exists(source_dir):
        log("ERROR", "extract_table", "Dossier source introuvable", {"dir": source_dir})
        return

    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Impossible de supprimer {file_path}: {e}")
    else:
        os.makedirs(output_dir)

    files = [f for f in os.listdir(source_dir) if f.strip().lower().endswith(".pdf")]
    files.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)

    log("INFO", "extract_table", "Traitement par lot démarré", {"source": source_dir, "nb_fichiers": len(files), "extractor": type(extractor).__name__})

    for filename in files:
        pdf_path = os.path.join(source_dir, filename)
        print(f"Traitement de {filename}...")

        try:
            solde_prec = extractor.get_solde_precedent(pdf_path)
            df = extractor.extract_transactions(pdf_path)

            if not df.empty:
                print(f"   {len(df)} transactions.")
                df_clean = clean_and_format_dataframe(df)
                df_clean = check_and_correct_balances(df_clean, solde_prec)
                output_name = os.path.splitext(filename)[0]
                analyze_and_export(df_clean, output_name, solde_prec, output_dir=output_dir)
            else:
                print("   Aucune transaction trouvee sur cette page.")

        except Exception as e:
            log("ERROR", "extract_table", "Erreur traitement fichier", {"fichier": filename}, exc=e)

        print("-" * 50)


def process_all_pdf_files(output_dir, final_output_name, start_solde=None):
    if not os.path.exists(output_dir):
        log("ERROR", "extract_table", "Dossier de sortie introuvable pour fusion", {"dir": output_dir})
        return pd.DataFrame()

    files = [f for f in os.listdir(output_dir) if f.endswith(".csv")]
    files = [f for f in files if final_output_name not in f]

    def get_sort_key(filename):
        numbers = re.findall(r'\d+', filename)
        return int(numbers[0]) if numbers else 0

    files.sort(key=get_sort_key)
    print(f"\nFusion de {len(files)} fichiers CSV trouves dans '{output_dir}'...")

    all_dfs = []
    for filename in files:
        filepath = os.path.join(output_dir, filename)
        try:
            df = pd.read_csv(filepath, sep=';')
            all_dfs.append(df)
            print(f"  - Charge: {filename} ({len(df)} lignes)")
        except Exception as e:
            print(f"  Erreur lors de la lecture de {filename}: {e}")

    if not all_dfs:
        log("WARN", "extract_table", "Aucun fichier CSV valide charge dans le dossier", {"dir": output_dir})
        return pd.DataFrame()

    full_df = pd.concat(all_dfs, ignore_index=True)

    if start_solde is not None:
        try:
            full_df = check_and_correct_balances(full_df, start_solde)
        except Exception as e:
            log("WARN", "extract_table", "Erreur lors de la correction des soldes", exc=e)

    full_df.insert(0, "N° d'ordre", range(1, len(full_df) + 1))

    output_csv  = os.path.join(output_dir, f"{final_output_name}.csv")
    output_xlsx = os.path.join(output_dir, f"{final_output_name}.xlsx")

    print(f"\nSauvegarde du fichier global ({len(full_df)} lignes)...")
    full_df.to_csv(output_csv, index=False, sep=';', encoding='utf-8-sig')
    log("INFO", "extract_table", "Fichier CSV global sauvegarde", {"path": output_csv, "nb_lignes": len(full_df)})

    try:
        full_df.to_excel(output_xlsx, index=False)
        log("INFO", "extract_table", "Fichier Excel global sauvegarde", {"path": output_xlsx})
    except ImportError:
        log("WARN", "extract_table", "Module openpyxl manquant pour l'export Excel")
    except Exception as e:
        log("ERROR", "extract_table", "Erreur export Excel", {"path": output_xlsx}, exc=e)

    return full_df
