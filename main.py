import os
import shutil
import sys
import time
import config
from split_pdf import generate_ocr_split
from extract_table import batch_process_pdf_folder, process_all_pdf_files, get_solde_precedent

# =================================================================================================
# SCRIPT PRINCIPAL : ORCHESTRATION DU FLUX DE TRAVAIL (PIPELINE)
# =================================================================================================
# Ce script exécute successivement les trois grandes étapes du traitement :
# 1. DÉCOUPAGE ET OCR : Conversion du PDF source en images, puis OCR pour obtenir des PDF "texte".
# 2. EXTRACTION DES DONNÉES : Analyse de chaque page OCRisée pour extraire les tableaux de transactions.
# 3. FUSION ET EXPORT : Regroupement de toutes les transactions dans un fichier Excel/CSV final.
# =================================================================================================

def run_extraction_pipeline(input_pdf_path, bank_name=None, status_callback=None):
    """
    Exécute le pipeline complet d'extraction pour un fichier PDF donné.
    Retourne le chemin du fichier Excel consolidé généré.
    """
    
    # Vérification de la banque supportée
    if bank_name and bank_name.strip().lower() != "orabank":
        raise ValueError(f"Désolé, cette banque ({bank_name}) n'a pas encore été paramétrée.")
    
    # -------------------------------------------------------------------------
    # ÉTAPE 0 : PRÉPARATION
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print(f"🚀 DÉMARRAGE DU TRAITEMENT : {input_pdf_path}")
    print("="*80)

    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Le fichier source '{input_pdf_path}' est introuvable.")

    start_time = time.time()
    
    # Dossiers temporaires spécifiques à ce run (basés sur le nom du fichier pour éviter conflits ?)
    # Pour simplifier, on utilise des dossiers fixes qu'on nettoie, comme l'ancien script.
    # Idéalement, on utiliserait un tempfile.TemporaryDirectory.
    
    base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
    # Nettoyage un peu bourrin des caractères spéciaux pour les noms de dossier
    safe_name = "".join([c for c in base_name if c.isalnum() or c in (' ', '-', '_')]).strip()
    
    # On crée une structure temporaire dans un dossier 'temp_proc' pour ne pas polluer la racine
    proc_dir = os.path.join("temp_proc", safe_name)
    ocr_output_dir = os.path.join(proc_dir, "ocr_split_pages")
    csv_output_dir = os.path.join(proc_dir, "extraction_files")
    
    os.makedirs(ocr_output_dir, exist_ok=True)
    os.makedirs(csv_output_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # ÉTAPE 1 : DÉCOUPAGE DU DOCUMENT SOURCE (MODE NATIF)
    # -------------------------------------------------------------------------
    print("\n" + "-"*50)
    print("📍 ÉTAPE 1 : Découpage du document source (sans OCR)")
    print("-"*50)
    
    # Appel Split
    if status_callback: status_callback("Découpage des pages...")
    ocr_result_dir = generate_ocr_split(input_pdf_path, ocr_output_dir, progress_callback=status_callback)
    
    if not ocr_result_dir:
        print("❌ CRITICAL: Split result dir is None.")
        raise RuntimeError("Échec du découpage du fichier PDF.")
        
    print(f"✅ Étape 1 terminée. Pages disponibles dans : {ocr_result_dir}")

    # -------------------------------------------------------------------------
    # ÉTAPE 2 : EXTRACTION DES DONNÉES STRUCTURÉES (TABLEAUX)
    # -------------------------------------------------------------------------
    print("\n" + "-"*50)
    print("📍 ÉTAPE 2 : Extraction des transactions bancaires")
    print("-"*50)

    # Extraction vers CSV intermédiaires
    if status_callback: status_callback("Extraction des tableaux (Parsing)...")
    batch_process_pdf_folder(ocr_result_dir, output_dir=csv_output_dir)
    
    print("✅ Étape 2 terminée. Fichiers intermédiaires générés.")

    # -------------------------------------------------------------------------
    # ÉTAPE 3 : CONSOLIDATION ET GÉNÉRATION DU RAPPORT FINAL
    # -------------------------------------------------------------------------
    print("\n" + "-"*50)
    print("📍 ÉTAPE 3 : Fusion et création du fichier final")
    print("-"*50)

    # Fusion
    import re
    
    start_solde = None
    try:
        # Identifier la première page (page_1.pdf) pour extraire le solde initial
        pdf_files = [f for f in os.listdir(ocr_result_dir) if f.lower().endswith(".pdf")]
        if pdf_files:
            # Tri intelligent (page_1 avant page_10)
            pdf_files.sort(key=lambda f: int(re.search(r'\d+', f).group()) if re.search(r'\d+', f) else 999)
            first_page_path = os.path.join(ocr_result_dir, pdf_files[0])
            
            print(f"💰 Recherche du solde initial dans : {first_page_path}")
            start_solde = get_solde_precedent(first_page_path)
            print(f"   => Solde initial trouvé : {start_solde:,.0f}")
    except Exception as e:
        print(f"⚠️ Erreur lors de la détection du solde initial : {e}")

    final_df = process_all_pdf_files(csv_output_dir, base_name, start_solde=start_solde)

    if not final_df.empty:
        elapsed_time = time.time() - start_time
        print("\n" + "="*80)
        print("✨ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print(f"⏱️  Durée totale : {elapsed_time:.1f} secondes")
        print(f"📊 Total transactions extraites : {len(final_df)}")
        print("="*80)
        
        # Retourne le chemin complet du fichier Excel
        output_excel_path = os.path.join(csv_output_dir, f"{base_name}.xlsx")
        
        # Vérification si le fichier existe bien (process_all_pdf_files l'a créé)
        if os.path.exists(output_excel_path):
             return output_excel_path
        else:
            # Fallback csv ?
            output_csv_path = os.path.join(csv_output_dir, f"{base_name}.csv")
            if os.path.exists(output_csv_path):
                return output_csv_path
            
    else:
        print("\n⚠️  Attention : Le fichier final semble vide ou n'a pas été généré.")
        return None

def cleanup_extraction_artifacts(input_pdf_path):
    """
    Nettoie les fichiers temporaires générés lors de l'extraction.
    Supprime le PDF source et le dossier de traitement associé.
    """
    try:
        # 1. Suppression du fichier PDF source
        if os.path.exists(input_pdf_path):
            os.remove(input_pdf_path)
            print(f"🗑️ Fichier source supprimé : {input_pdf_path}")
            
        # 2. Suppression du dossier de traitement
        base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
        safe_name = "".join([c for c in base_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        proc_dir = os.path.join("temp_proc", safe_name)
        
        if os.path.exists(proc_dir):
            shutil.rmtree(proc_dir)
            print(f"🧹 Dossier temporaire nettoyé : {proc_dir}")
            
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage : {e}")

def main():
    """
    Point d'entrée pour l'exécution directe via python main.py
    """
    if not os.path.exists(config.input_pdf):
        print(f"❌ Erreur critique : Le fichier source '{config.input_pdf}' est introuvable.")
        sys.exit(1)
        
    try:
        run_extraction_pipeline(config.input_pdf)
    except Exception as e:
        print(f"Erreur main : {e}")


if __name__ == "__main__":
    try:
        if not os.path.exists(config.input_pdf):
            print(f"❌ Erreur critique : Le fichier source '{config.input_pdf}' est introuvable.")
            sys.exit(1)
            
        try:
            run_extraction_pipeline(config.input_pdf)
        except Exception as e:
            print(f"Erreur main : {e}")
            
    except KeyboardInterrupt:
        print("\n🛑 Interruption par l'utilisateur.")
    except Exception as e:
        print(f"\n❌ Une erreur inattendue est survenue : {e}")
        import traceback
        traceback.print_exc()
