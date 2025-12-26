import streamlit as st
import os
import _02_rapp as rapp  # Import du module de traitement
import _05_style as style # Import du fichier de style
import base64
import _03_auth_manager as auth_manager # Gestionnaire d'authentification
import main as pdf_extractor # Pipeline d extraction

import pandas as pd
import datetime
import time
import config
import importlib

importlib.reload(style)
importlib.reload(auth_manager)

importlib.reload(style) # Force le rechargement du style à chaque run
importlib.reload(auth_manager) # Force le rechargement de l'auth


# Configuration de la page
st.set_page_config(page_title="RAPP 5", layout="wide", initial_sidebar_state="expanded")

# --- GESTION DE L'ETAT (STATE) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def reset_callback():
    st.session_state.reset_key += 1
    st.session_state.nav_selection = "Accueil"
    if 'processed_data' in st.session_state:
        del st.session_state['processed_data']

def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    # st.rerun()

# Gestion du logout via URL (pour le bouton dans le header)
if "logout" in st.query_params:
    logout()
    st.query_params.clear() # Nettoie l'URL


def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    img_path = os.path.join("src_image", "logo_cropped.png")
    img_base64 = get_img_as_base64(img_path)
    img_tag = f'<img src="data:image/png;base64,{img_base64}" class="logo-img">'
except Exception:
    img_tag = ""

# --- UI STYLES ---
st.markdown(style.css_code, unsafe_allow_html=True)

# ==============================================================================
# PAGE D'AUTHENTIFICATION (Si non connecté)
# ==============================================================================
if not st.session_state.authenticated:
    
    # Centre le contenu
    col_auth_cw, col_auth_c, col_auth_ce = st.columns([1, 2, 1])
    
    with col_auth_c:
        # Affiche le logo centré
        st.markdown(f"<div style='text-align: center; margin-bottom: 0px;'>{img_tag}</div>", unsafe_allow_html=True)

        st.markdown("""
            <h1 style='text-align: center; color: #2c3e50; font-family: Poppins, sans-serif;'>Bienvenue sur RAPP 30</h1>
            <p style='text-align: center; color: #666;'>Votre outil de rapprochement bancaire en 30s.</p>
            <br>
        """, unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["Se connecter", "S'inscrire"])
        
        # --- TAB CONNEXION ---
        with tab_login:
            st.subheader("Connexion")
            with st.form("login_form"):
                login_email = st.text_input("Email", key="login_email")
                login_pass = st.text_input("Mot de passe", type="password", key="login_pass")
                submitted = st.form_submit_button("Se connecter", type="primary")
            
            if submitted:
                success, msg = auth_manager.login_user(login_email, login_pass)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_email = login_email
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        # --- TAB INSCRIPTION ---
        with tab_signup:
            st.subheader("Créer un compte")
            with st.form("signup_form"):
                reg_email = st.text_input("Email", key="reg_email")
                reg_nom = st.text_input("Nom", key="reg_nom")
                reg_prenoms = st.text_input("Prénoms", key="reg_prenoms")
                
                # Zone Téléphone avec indicatif
                col_ind, col_tel = st.columns([1, 3])
                with col_ind:
                    indicatifs = [
                        "+1", "+20", "+27", "+33", "+211", "+212", "+213", "+216", "+218", "+220", "+221", "+222", "+223", "+224", "+225", 
                        "+226", "+227", "+228", "+229", "+230", "+231", "+232", "+233", "+234", "+235", "+236", "+237", "+238", "+239", 
                        "+240", "+241", "+242", "+243", "+244", "+245", "+246", "+248", "+249", "+250", "+251", "+252", "+253", "+254", 
                        "+255", "+256", "+257", "+258", "+260", "+261", "+262", "+263", "+264", "+265", "+266", "+267", "+268", "+269", 
                        "+291", "+297", "+298", "+299"
                    ]
                    phone_code = st.selectbox("Indicatif", indicatifs, key="reg_ind")
                with col_tel:
                    phone_number = st.text_input("N° telephone (Sans indicatif)", key="reg_tel_num")
                
                reg_ent = st.text_input("Nom de l'entreprise", key="reg_ent")
                reg_pass = st.text_input("Mot de passe", type="password", key="reg_pass")
                reg_pass_confirm = st.text_input("Confirmer le mot de passe", type="password", key="reg_pass_conf")
                submitted_reg = st.form_submit_button("S'inscrire")
            
            if submitted_reg:
                if reg_pass != reg_pass_confirm:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    full_phone = f"{phone_code} {phone_number}"
                    success, msg = auth_manager.register_user(reg_email, reg_pass, reg_nom, reg_prenoms, full_phone, reg_ent)
                    if success:
                        st.success(msg)
                        time.sleep(2)
                        # On vide les champs manuellement
                        keys_to_clear = ["reg_email", "reg_nom", "reg_prenoms", "reg_tel_num", "reg_ent", "reg_pass", "reg_pass_conf"]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error(msg)

# ==============================================================================
# APPLICATION PRINCIPALE (Si connecté)
# ==============================================================================
else:
    # --- BARRE LATERALE ---
    st.sidebar.title("Menu")
    
    # Crédits
    user_credits = auth_manager.get_credits(st.session_state.user_email)
    user_name = auth_manager.get_user_name(st.session_state.user_email)
    st.sidebar.markdown(f"**Utilisateur :** {user_name}")
    st.sidebar.markdown(f"**Crédit :** {user_credits}")
    
    # Navigation
    nav = st.sidebar.radio("Navigation", ["Accueil", "Mes rapprochements", "Maquette"], key="nav_selection")
    
    st.sidebar.markdown("---")

    
    # Espaceur
    st.sidebar.markdown("<br>" * 3, unsafe_allow_html=True)
    
    if st.sidebar.button("NOUVEL E.R", on_click=reset_callback):
        pass # Le callback fait tout

    # --- EN-TETE ---
    # (La fonction get_img_as_base64 est maintenant définie globalement)
    
    # En-tête (Barre avec logo)

    # En-tête (Barre avec logo)
    st.markdown(f"""
        <div class="fixed-title">
            {img_tag}
            <a href="?logout=true" target="_self" class="logout-btn-header">Log Out</a>
        </div>
    """, unsafe_allow_html=True)
    
    # --- VIEW: MES RAPPROCHEMENTS ---
    # --- VIEW: MES RAPPROCHEMENTS ---
    if nav == "Mes rapprochements":
        # Remonter le contenu avec une marge négative pour compenser le padding global
        st.markdown('<div class="main-content" style="margin-top: -60px;">', unsafe_allow_html=True)
        st.markdown("<h3>Mes Rapprochements</h3>", unsafe_allow_html=True)
        
        history = auth_manager.get_history(st.session_state.user_email)
        
        if not history:
            st.info("Aucun rapprochement effectué pour le moment.")
        else:
            # En-têtes du tableau
            with st.container():
                h1, h2, h3, h4 = st.columns([2, 3, 1, 1])
                h1.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>Date</div>", unsafe_allow_html=True)
                h2.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>Banque</div>", unsafe_allow_html=True)
                h3.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>Aperçu</div>", unsafe_allow_html=True)
                h4.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>Télécharger</div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 5px 0; border: 2px solid #2c3e50;'>", unsafe_allow_html=True)

            # Lignes du tableau (Conteneur scrollable)
            # Utilisation de height=... pour fixer la zone et permettre le scroll vertical
            # tout en gardant l'en-tête (défini au dessus) fixe.
            with st.container(height=500):
                for idx, item in enumerate(reversed(history)):
                    with st.container():
                        c1, c2, c3, c4 = st.columns([2, 3, 1, 1])
                        date_gen = item.get('date_gen', 'N/A')
                        banque = item.get('banque', 'Inconnue')
                        pdf_path = item.get('url_pdf') or item.get('pdf_path', '')
                        excel_path = item.get('url_excel') or item.get('excel_path', '')
                        
                        # Alignement vertical du texte
                        c1.markdown(f"<div style='padding-top: 10px;'>{date_gen}</div>", unsafe_allow_html=True)
                        c2.markdown(f"<div style='padding-top: 10px;'>{banque}</div>", unsafe_allow_html=True)
                        
                        if pdf_path:
                            if pdf_path.startswith("http"):
                                 # Lien vers le stockage cloud (Supabase)
                                 # Bouton Aperçu (Ouvre dans nouvel onglet)
                                 c3.markdown(f'<a href="{pdf_path}" target="_blank" style="text-decoration: none;"><button style="border: 1px solid #2196F3; background-color: white; color: #2196F3; padding: 5px 10px; border-radius: 5px; cursor: pointer;">👁️</button></a>', unsafe_allow_html=True)
                                 
                                 # Bouton Télécharger (Ouvre aussi dans nouvel onglet car c'est un lien direct)
                                 # Ou on peut essayer de forcer le téléchargement si le navigateur le permet, mais target_blank est standard pour PDF.
                                 # On change juste le label pour différencier.
                                 # Pour un vrai "download" silencieux cross-origin, c'est compliqué sans proxy.
                                 # Ici on met un bouton explicite "Télécharger" qui pointe vers le même lien.
                                 c4.markdown(f'<a href="{pdf_path}" target="_blank" style="text-decoration: none;"><button style="border: 1px solid #4CAF50; background-color: white; color: #4CAF50; padding: 5px 10px; border-radius: 5px; cursor: pointer;">⇩</button></a>', unsafe_allow_html=True)
                                 
                            elif os.path.exists(pdf_path):
                                # Fichier local
                                with open(pdf_path, "rb") as f:
                                    c3.download_button(
                                        label="⇩",
                                        data=f,
                                        file_name=os.path.basename(pdf_path),
                                        mime="application/pdf",
                                        key=f"dl_pdf_{idx}"
                                    )
                                    c4.write("") # Pas d'aperçu simple pour fichiers locaux sans serveur de fichiers static
                            else:
                                c3.markdown("<span style='color: grey;'>-</span>", unsafe_allow_html=True)
                                c4.markdown("<span style='color: grey;'>-</span>", unsafe_allow_html=True)
                        else:
                            c3.markdown("<span style='color: grey;'>-</span>", unsafe_allow_html=True)
                            c4.markdown("<span style='color: grey;'>-</span>", unsafe_allow_html=True)
                            

                        # Séparateur de ligne
                        st.markdown("<hr style='margin: 0; border: 0; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop() # Arrête l'exécution ici pour ne pas afficher le formulaire "Nouveau"

    # --- VIEW: MAQUETTE ---
    if nav == "Maquette":
        st.markdown('<div class="main-content" style="margin-top: -60px;">', unsafe_allow_html=True)
        st.markdown("<h3>Maquettes</h3>", unsafe_allow_html=True)
        st.markdown("<p>Téléchargez les modèles de fichiers nécessaires pour vos rapprochements ci-dessous.</p>", unsafe_allow_html=True)
        
        maquette_dir = "maquette"
        if os.path.exists(maquette_dir):
            files = [f for f in os.listdir(maquette_dir) if os.path.isfile(os.path.join(maquette_dir, f))]
            
            if not files:
                st.info("Aucun fichier disponible dans le dossier maquette.")
            else:
                # Création d'une grille pour l'affichage (optionnel, ou liste simple)
                for file_name in files:
                    file_path = os.path.join(maquette_dir, file_name)
                    
                    # Détermination du mime type approximatif
                    mime_type = "application/octet-stream"
                    if file_name.endswith(".xlsx"):
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    elif file_name.endswith(".pdf"):
                        mime_type = "application/pdf"
                    
                    col_file, col_btn = st.columns([3, 1])
                    with col_file:
                        st.markdown(f"**{file_name}**")
                    with col_btn:
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="Télécharger",
                                data=f,
                                file_name=file_name,
                                mime=mime_type,
                                key=f"dl_maquette_{file_name}"
                            )
                    st.markdown("<hr style='margin: 5px 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

        else:
            st.error(f"Le dossier '{maquette_dir}' est introuvable.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # --- VIEW: ACCUEIL ---
    # --- FORMULAIRE PRINCIPAL ---
    
    # Sélection de la banque et Date
    cols_sel = st.columns(4)
    with cols_sel[0]:
        banques = ["Orabank", "BOA", "UTB", "Sunu Bank"]
        choix_banque = st.selectbox("Sélectionnez votre banque", banques, key=f"banque_{st.session_state.reset_key}")
    
    with cols_sel[2]:
        date_arrete = st.date_input("Date de rapprochement", key=f"date_{st.session_state.reset_key}")
    
    st.markdown("---")
    
    # Zone d'inputs alignées horizontalement
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("1. Relevé Bancaire")
        releve_file = st.file_uploader("Ajoutez votre relevé bancaire original", type=['pdf'], key=f"releve_{st.session_state.reset_key}")
    
    with col2:
        st.subheader("2. E.R Précédent")
        etat_prec_file = st.file_uploader("Ajoutez votre etat de rapprochement du mois précédent", type=['xlsx', 'xls'], key=f"etat_{st.session_state.reset_key}")
    
    with col3:
        st.subheader("3. Journal Banque")
        journal_file = st.file_uploader("Ajoutez votre journal banque", type=['xlsx', 'xls'], key=f"journal_{st.session_state.reset_key}")
    
    st.markdown("---")
    
    # Bouton de validation
    if st.button("Valider"):
        if auth_manager.get_credits(st.session_state.user_email) <= 0:
            st.error("Crédits insuffisants. Vous ne pouvez plus faire de rapprochements.")
            st.stop()

        missing_files = []
        if not releve_file:
            missing_files.append("Relevé bancaire")
        if not journal_file:
            missing_files.append("Journal banque")
        
        if missing_files:
            st.error(f"Veuillez charger les fichiers manquants : {', '.join(missing_files)}")
        else:
            with st.spinner('Traitement en cours...'):
                try:
                    # Préparation des données en mémoire (sans sauvegarde des inputs)
                    def load_input(file_upload):
                        ext = file_upload.name.split('.')[-1].lower()
                        if ext == 'csv':
                             return pd.read_csv(file_upload)
                        elif ext == 'xls':
                            return pd.read_excel(file_upload, engine='xlrd')
                        else:
                            # Default to openpyxl for xlsx or others
                            return pd.read_excel(file_upload, engine='openpyxl')

                    # Gestion du Relevé Bancaire (PDF OBLIGATOIRE selon la demande, mais on gère si jamais)
                    df_releve = None
                    file_upload = releve_file
                    ext_releve = file_upload.name.split('.')[-1].lower()
                    
                    if ext_releve == 'pdf':
                        status_text = st.empty()
                        status_text.info("Etat de Rapprochement en cours de traitement... (Cela peut prendre plus d'une minute)")
                        
                        # Création d'un fichier temporaire pour le PDF
                        try:
                            # Dossier temporaire pour les uploads
                            os.makedirs("temp_uploads", exist_ok=True)
                            temp_pdf_path = os.path.join("temp_uploads", file_upload.name)
                            
                            with open(temp_pdf_path, "wb") as f:
                                f.write(file_upload.getbuffer())
                                
                            # Lancement du pipeline d'extraction via main.py / run_extraction_pipeline
                            extracted_excel_path = pdf_extractor.run_extraction_pipeline(temp_pdf_path)                            
                            if extracted_excel_path and os.path.exists(extracted_excel_path):
                                df_releve = pd.read_excel(extracted_excel_path, engine='openpyxl')
                                status_text.success("Extraction PDF terminée avec succès !")
                                time.sleep(1) # Petit temps pour lire le message
                                status_text.empty()
                            else:
                                st.error("L'extraction du PDF a échoué ou n'a produit aucun résultat.")
                                st.stop()
                                
                        except Exception as e:
                            st.error(f"Erreur lors de l'analyse du PDF : {e}")
                            st.stop()
                        finally:
                            # Nettoyage facultatif du PDF uploadé
                            pass 

                    else:
                        # Si l'utilisateur force un Excel (non recommandé vu la consigne, mais robuste)
                        df_releve = load_input(releve_file)

                    df_journal = load_input(journal_file)
                    
                    df_etat = None
                    if etat_prec_file:
                        # Etat prec: header=None car structure brute lue par rapp.py
                        ext_etat = etat_prec_file.name.split('.')[-1].lower()
                        engine_etat = 'xlrd' if ext_etat == 'xls' else 'openpyxl'
                        df_etat = pd.read_excel(etat_prec_file, header=None, engine=engine_etat)
    
                    # Définition du nom de fichier de sortie
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    nom_fichier_sortie = f"Etat_Rapprochement_{choix_banque}_{timestamp}.xlsx"
                    
                    # Exécution du rapprochement en mémoire
                    # IMPORTANT : df_releve contient maintenant les données extraites
                    excel_buffer, pdf_bytes, stats = rapp.executer_rapprochement(df_releve, df_journal, df_etat, date_rapprochement=date_arrete)

                    # Sauvegarde des RÉSULTATS dans Supabase Storage (Cloud)
                    url_excel = auth_manager.upload_to_storage(
                        excel_buffer.getvalue(), 
                        nom_fichier_sortie, 
                        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    url_pdf = None
                    if pdf_bytes:
                         pdf_filename = nom_fichier_sortie.replace('.xlsx', '.pdf')
                         url_pdf = auth_manager.upload_to_storage(
                             pdf_bytes,
                             pdf_filename,
                             content_type="application/pdf"
                         )

                    # Mise à jour Crédits et Historique
                    auth_manager.decrement_credits(st.session_state.user_email)
                    
                    date_display = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # On sauvegarde les URLs publiques dans l'historique
                    # Note: Si l'upload échoue (url=None), on aura None en base, ce qui est acceptable pour l'instant.
                    auth_manager.add_history_remote(st.session_state.user_email, {
                        'url_excel': url_excel,
                        'url_pdf': url_pdf,
                        'banque': choix_banque,
                        'date_gen': date_display 
                    })


                    # Stockage des résultats dans la session pour persistance
                    st.session_state['processed_data'] = {
                        'excel_bytes': excel_buffer.getvalue(),
                        'pdf_bytes': pdf_bytes,
                        'stats': stats,
                        'nom_fichier_sortie': nom_fichier_sortie,
                        'pdf_filename': pdf_filename,
                        'choix_banque': choix_banque
                    }
                    
                except Exception as e:
                    st.error(f"Une erreur est survenue lors du traitement : {e}")

    # --- AFFICHAGE PERSISTANT DES RÉSULTATS ---
    if 'processed_data' in st.session_state:
        data = st.session_state['processed_data']
        
        # Reconstruction du buffer Excel
        import io
        excel_buffer = io.BytesIO(data['excel_bytes'])
        pdf_bytes = data['pdf_bytes']
        stats = data['stats']
        nom_fichier_sortie = data['nom_fichier_sortie']
        pdf_filename = data['pdf_filename']
        choix_banque = data['choix_banque']

        st.success(f"Rapprochement terminé pour {choix_banque} !")
        if stats:
             st.info(f"Suspendus : Banque ({stats.get('suspens_banque', 0)}), Compta ({stats.get('suspens_compta', 0)})")
        
        # Zone Output
        st.markdown("### Résultat")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="Télécharger E.R Excel",
                data=excel_buffer,
                file_name=nom_fichier_sortie,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_d2:
            if pdf_bytes:
                st.download_button(
                    label="Télécharger E.R PDF",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )
            
        st.markdown("### Aperçu des résultats")
        
        try:
            # Lecture pour affichage depuis le buffer
            excel_buffer.seek(0)
            df_rapp = pd.read_excel(excel_buffer, sheet_name='RAPPROCHEMENT', header=None).fillna("")
            
            # Reformater les chiffres pour l'affichage (Séparateur millier, 0 décimale)
            def format_accounting(val):
                try:
                    f = float(val)
                    # Format: espace pour milliers, 0 décimales
                    return "{:,.0f}".format(f).replace(",", " ")
                except:
                    return str(val)

            # On applique le formatage sur tout le dataframe (car structure mixte)
            # On ne touche pas aux dates/libellés qui ne sont pas des floats convertibles (ou alors on checke l'erreur)
            # L'astuce est d'appliquer uniquement si c'est convertible
            
            df_rapp = df_rapp.applymap(lambda x: format_accounting(x))

            # Force string type for all columns to avoid PyArrow mixed type errors (int vs str)
            # Déjà fait par le formatage qui retourne des strings
            
            st.subheader("Tableau de Rapprochement")
            st.dataframe(df_rapp, width=None, use_container_width=True, hide_index=True)
            
            with st.expander("Voir les détails des suspens"):
                excel_buffer.seek(0)
                st.write("#### Opérations Non Pointées - Journal")
                df_jn = pd.read_excel(excel_buffer, sheet_name='JOURNAL_NON_POINTEE', dtype=str).fillna("")
                st.dataframe(df_jn, use_container_width=True)

                excel_buffer.seek(0)
                st.write("#### Opérations Non Pointées - Relevé")
                df_rn = pd.read_excel(excel_buffer, sheet_name='RELEVE_NON_POINTEE', dtype=str).fillna("")
                st.dataframe(df_rn, use_container_width=True)
                
        except Exception as e:
            st.warning(f"Impossible d'afficher l'aperçu complet : {e}")


