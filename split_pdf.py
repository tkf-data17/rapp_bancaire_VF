import fitz # PyMuPDF
import os
import shutil 
import config 

def generate_ocr_split(input_pdf_path, output_split_dir=config.input_dir, progress_callback=None):
    """
    Traite le PDF page par page et sauvegarde chaque page 
    individuellement dans un dossier (Mode Natif sans OCR).
    """
    
    try:
        # Nettoyage et création du dossier de sortie
        if os.path.exists(output_split_dir):
            print(f"Nettoyage du dossier existant : '{output_split_dir}'")
            for filename in os.listdir(output_split_dir):
                file_path = os.path.join(output_split_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Erreur lors de la suppression de {file_path}: {e}")
        else:
            os.makedirs(output_split_dir)
            print(f"Création du dossier de sortie : '{output_split_dir}'")
            
        doc = fitz.open(input_pdf_path)
        total_pages = doc.page_count
        print(f"Démarrage du découpage sur {total_pages} pages (Mode Natif)...")
        
        if progress_callback: progress_callback(f"PDF chargé : {total_pages} pages à traiter.")
        
        for i in range(total_pages):
            # Update Progress
            msg = f"Traitement : Page {i+1} sur {total_pages}..."
            print(msg)
            if progress_callback: progress_callback(msg)

            # Création d'un nouveau PDF pour la page unique
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            
            split_output_file = os.path.join(output_split_dir, f"ocr_page_{i+1}.pdf")
            new_doc.save(split_output_file)
            new_doc.close()
            
        doc.close()
        
        return output_split_dir

    except Exception as e:
        print(f"\nERREUR: Une erreur est survenue pendant le découpage: {e}")
        return None
    
# ----------------- EXÉCUTION DU SCRIPT -----------------
if __name__ == "__main__":
    input_pdf = config.input_pdf
    # Appel de la nouvelle fonction qui ne fait pas de fusion
    result_dir = generate_ocr_split(input_pdf)
    
    if result_dir:
        print(f"\nLe dossier contenant les pages est : {result_dir}")