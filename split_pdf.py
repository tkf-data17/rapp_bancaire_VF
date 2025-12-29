import fitz # PyMuPDF
import subprocess
import pytesseract
import platform
from PIL import Image
import io
import os
import shutil 
import config 

# 🚨 CHEMINS TESSERACT : UTILISEZ CEUX QUE VOUS AVEZ VÉRIFIÉS 🚨
if platform.system() == "Windows":
    TESSERACT_PATH = r"C:\Users\HP ELITE BOOK\AppData\Local\Programs\Tesseract-OCR\tesseract.exe" 
    TESSDATA_DIR = r"C:\Users\HP ELITE BOOK\AppData\Local\Programs\Tesseract-OCR\tessdata"
else:
    # Configuration pour Linux (Docker / Cloud)
    TESSERACT_PATH = "tesseract"
    # On tente un chemin standard, mais on laisse vide si non trouvé pour que Tesseract utilise son défaut
    TESSDATA_DIR = "/usr/share/tesseract-ocr/4.00/tessdata"  # Valeur par défaut Debian
    if not os.path.exists(TESSDATA_DIR):
         TESSDATA_DIR = "/usr/share/tesseract-ocr/5/tessdata" # Autre standard
    
    # Si toujours pas trouvé, on ne définit pas la variable, on laisse le système gérer
    if not os.path.exists(TESSDATA_DIR):
        TESSDATA_DIR = None

# Configuration de l'environnement Python pour Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Définit la variable d'environnement TESSDATA_PREFIX (plus fiable)
if "Windows" in platform.system() or TESSDATA_DIR:
    # Sous Linux, on ne met la variable que si on a trouvé un dossier valide
    if TESSDATA_DIR:
        os.environ['TESSDATA_PREFIX'] = TESSDATA_DIR 

def generate_ocr_split(input_pdf_path, output_split_dir=config.input_dir, progress_callback=None):
    """
    Traite le PDF page par page, effectue l'OCR et sauvegarde chaque page 
    individuellement dans un dossier.
    """
    
    TESSERACT_LANG = "fra" 
    
    try:
        # Debug Tesseract Path (Logs serveur)
        if progress_callback: progress_callback("Vérification de Tesseract...")
        try:
            ver_check = subprocess.run([TESSERACT_PATH, "--version"], capture_output=True, text=True)
            print(f"DEBUG: Tesseract Version: {ver_check.stdout}")
        except Exception as e:
            print(f"WARNING: Impossible de lancer tesseract --version: {e}")

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
        print(f"Démarrage de l'OCR sur {total_pages} pages...")
        
        if progress_callback: progress_callback(f"PDF chargé : {total_pages} pages à traiter.")
        
        for i in range(total_pages):
            # Update Progress
            msg = f"Traitement OCR : Page {i+1} sur {total_pages}..."
            print(msg)
            if progress_callback: progress_callback(msg)

            page = doc.load_page(i)
            
            # 1. Conversion de la page en image PNG (haute résolution)
            # Réduction légère du DPI pour accélérer sur le cloud si nécessaire (200 est souvent suffisant)
            pix = page.get_pixmap(dpi=300) 
            temp_image_file = f"temp_ocr_page_{i+1}.png"
            pix.save(temp_image_file)
            
            # 2. Définition des chemins de sortie
            temp_pdf_file = f"temp_ocr_page_{i+1}.pdf"
            split_output_file = os.path.join(output_split_dir, f"ocr_page_{i+1}.pdf")
            
            # 3. Exécution de Tesseract (génère temp_pdf_file)
            command = [
                TESSERACT_PATH,
                temp_image_file, 
                temp_pdf_file[:-4], # Fichier de sortie temporaire (nom sans extension .pdf)
                '-l', TESSERACT_LANG,
                'pdf' 
            ]
            
            subprocess.run(command, check=True, capture_output=True, text=True)
            
            # 4. Déplacement du fichier OCR final vers le dossier de split
            shutil.move(temp_pdf_file, split_output_file)
            
            # 5. Nettoyage
            if os.path.exists(temp_image_file): os.remove(temp_image_file)
            
            # print(f"Page {i+1} : OCR terminé et enregistré dans '{split_output_file}'")

        doc.close()
        
        # print("\n✅ Succès : Toutes les pages OCR ont été enregistrées individuellement.")
        return output_split_dir

    except subprocess.CalledProcessError as e:
        print(f"\nERREUR TESSERACT: Tesseract a échoué avec le code {e.returncode}. Sortie : {e.stderr}")
        return None
    except Exception as e:
        print(f"\nERREUR: Une erreur est survenue pendant l'OCR: {e}")
        return None
    
# ----------------- EXÉCUTION DU SCRIPT -----------------
if __name__ == "__main__":
    input_pdf = config.input_pdf
    # Appel de la nouvelle fonction qui ne fait pas de fusion
    result_dir = generate_ocr_split(input_pdf)
    
    if result_dir:
        print(f"\nLe dossier contenant les pages OCR est : {result_dir}")