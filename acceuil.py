import streamlit as st
import os
import rapp  # Import du module de traitement
import style # Import du fichier de style
import base64
import importlib
import auth_manager # Gestionnaire d'authentification
import pandas as pd

importlib.reload(style) # Force le rechargement du style à chaque run

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

def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    # st.rerun() # Utilisé par Streamlit récent, sinon pas nécessaire si l'app se redessine

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
                reg_pass = st.text_input("Mot de passe", type="password", key="reg_pass")
                reg_pass_confirm = st.text_input("Confirmer le mot de passe", type="password", key="reg_pass_conf")
                submitted_reg = st.form_submit_button("S'inscrire")
            
            if submitted_reg:
                if reg_pass != reg_pass_confirm:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    success, msg = auth_manager.register_user(reg_email, reg_pass)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

# ==============================================================================
# APPLICATION PRINCIPALE (Si connecté)
# ==============================================================================
else:
    # --- BARRE LATERALE ---
    st.sidebar.markdown(f"**Utilisateur :** {st.session_state.user_email}")
    st.sidebar.button("Nouvel ER", on_click=reset_callback)
    if st.sidebar.button("Log out"):
        logout()
        st.rerun()

    # --- EN-TETE ---
    # (La fonction get_img_as_base64 est maintenant définie globalement)
    
    # En-tête (Barre avec logo)

    # En-tête (Barre avec logo)
    st.markdown(f"""
        <div class="fixed-title">
            {img_tag}
        </div>
    """, unsafe_allow_html=True)
    
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
        releve_file = st.file_uploader("Ajoutez votre relevé bancaire original", type=['xlsx', 'xls', 'csv', 'pdf'], key=f"releve_{st.session_state.reset_key}")
    
    with col2:
        st.subheader("2. E.R Précédent")
        etat_prec_file = st.file_uploader("Ajoutez votre etat de rapprochement du mois précédent", type=['xlsx', 'xls'], key=f"etat_{st.session_state.reset_key}")
    
    with col3:
        st.subheader("3. Journal Banque")
        journal_file = st.file_uploader("Ajoutez votre journal banque", type=['xlsx', 'xls', 'csv'], key=f"journal_{st.session_state.reset_key}")
    
    st.markdown("---")
    
    # Bouton de validation
    if st.button("Valider"):
        missing_files = []
        # Le champ 2 est optionnel pour le moment
        if not releve_file:
            missing_files.append("Relevé bancaire")
        if not journal_file:
            missing_files.append("Journal banque")
        
        if missing_files:
            st.error(f"Veuillez charger les fichiers manquants : {', '.join(missing_files)}")
        else:
            with st.spinner('Traitement en cours...'):
                try:
                    # Création du dossier documents s'il n'existe pas
                    upload_dir = "documents"
                    os.makedirs(upload_dir, exist_ok=True)
    
                    path_releve = os.path.join(upload_dir, "relevé.xlsx")
                    path_journal = os.path.join(upload_dir, "journal_banque.xlsx")
    
                    # Fonction de conversion/sauvegarde
                    def save_converted(upload, target):
                        # Détection de l'extension d'origine
                        ext = upload.name.split('.')[-1].lower()
                        
                        if ext == 'csv':
                            # Lecture CSV et sauvegarde Excel
                            df = pd.read_csv(upload)
                            df.to_excel(target, index=False)
                        elif ext in ['xls', 'xlsx']:
                            try:
                                df = pd.read_excel(upload)
                                df.to_excel(target, index=False)
                            except Exception as e:
                                # Fallback: écriture directe
                                if ext == 'xlsx':
                                    upload.seek(0)
                                    with open(target, "wb") as f:
                                        f.write(upload.getbuffer())
                                else:
                                    raise e
                        else:
                            raise ValueError(f"Format non supporté: {ext}")
    
                    # Sauvegarde Convertie
                    save_converted(releve_file, path_releve)
                                 
                    # Sauvegarde directe du journal (toujours Excel)
                    with open(path_journal, "wb") as f:
                        f.write(journal_file.getbuffer())
    
                    path_etat = None
                    # Si etat_prec_file est fourni
                    if etat_prec_file:
                        path_etat = os.path.join(upload_dir, "Etat_prec.xlsx")
                        with open(path_etat, "wb") as f:
                            f.write(etat_prec_file.getbuffer())
    
                    # Définition du nom de fichier de sortie dynamique
                    nom_fichier_sortie = f"Etat_Rapprochement_{choix_banque}.xlsx"
                    output_path = os.path.join("documents", nom_fichier_sortie)
    
                    # Exécution du rapprochement
                    rapp.executer_rapprochement(path_releve, path_journal, path_etat, output_path, date_rapprochement=date_arrete)
                    
                    st.success(f"Rapprochement terminé pour {choix_banque} !")
                    
                    # Zone Output
                    st.markdown("### Résultat")
                    
                    if os.path.exists(output_path):
                        with open(output_path, "rb") as file:
                            btn = st.download_button(
                                label="télécharger ER",
                                data=file,
                                file_name=nom_fichier_sortie,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        st.markdown("### Aperçu des résultats")
                        
                        try:
                            # Lecture des différentes feuilles pour affichage, header=None pour préserver la structure
                            df_rapp = pd.read_excel(output_path, sheet_name='RAPPROCHEMENT', header=None)
                            df_rapp = df_rapp.fillna("")
                            
                            # Logique d'affichage (Similaire à avant)
                            # ... (Code recalcul totaux identique) ...
                            mask_totaux = df_rapp[1].astype(str).str.contains("Totaux", case=False, na=False)
                            if mask_totaux.any():
                                idx_totaux = df_rapp[mask_totaux].index[0]
                                cols_nums = [2, 3, 4, 5]
                                subset = df_rapp.iloc[2:idx_totaux, cols_nums].apply(pd.to_numeric, errors='coerce').fillna(0)
                                totaux = subset.sum()
                                for col_idx in cols_nums:
                                    df_rapp.iat[idx_totaux, col_idx] = totaux[col_idx]
                                
                                idx_rectif = idx_totaux + 1
                                if idx_rectif < len(df_rapp):
                                    tot_c, tot_d = totaux[2], totaux[3]
                                    tot_e, tot_f = totaux[4], totaux[5]
                                    
                                    rect_c = (tot_d - tot_c) if (tot_d - tot_c) > 0 else 0
                                    rect_d = (tot_c - tot_d) if (tot_c - tot_d) > 0 else 0
                                    rect_e = (tot_f - tot_e) if (tot_f - tot_e) > 0 else 0
                                    rect_f = (tot_e - tot_f) if (tot_e - tot_f) > 0 else 0
                                    
                                    df_rapp.iat[idx_rectif, 2] = rect_c if rect_c!=0 else ""
                                    df_rapp.iat[idx_rectif, 3] = rect_d if rect_d!=0 else ""
                                    df_rapp.iat[idx_rectif, 4] = rect_e if rect_e!=0 else ""
                                    df_rapp.iat[idx_rectif, 5] = rect_f if rect_f!=0 else ""
                                    
                                    idx_gen = idx_rectif + 1
                                    if idx_gen < len(df_rapp):
                                        gen_c = tot_c + rect_c
                                        gen_d = tot_d + rect_d
                                        gen_e = tot_e + rect_e
                                        gen_f = tot_f + rect_f
                                        df_rapp.iat[idx_gen, 2] = gen_c
                                        df_rapp.iat[idx_gen, 3] = gen_d
                                        df_rapp.iat[idx_gen, 4] = gen_e
                                        df_rapp.iat[idx_gen, 5] = gen_f
    
                            def format_num(x):
                                if isinstance(x, (int, float)):
                                    if x == 0: return ""
                                    return f"{x:,.0f}".replace(",", " ")
                                return x
    
                            col_indices = [2, 3, 4, 5]
                            for i in col_indices:
                                 df_rapp.iloc[2:, i] = df_rapp.iloc[2:, i].apply(format_num)
    
                            st.subheader("Tableau de Rapprochement")
                            st.dataframe(df_rapp, use_container_width=True, hide_index=True)
                            
                            with st.expander("Voir les détails des suspens"):
                                st.write("#### Opérations Non Pointées - Journal")
                                df_jn = pd.read_excel(output_path, sheet_name='JOURNAL_NON_POINTEE', dtype=str).fillna("")
                                st.dataframe(df_jn, use_container_width=True)
    
                                st.write("#### Opérations Non Pointées - Relevé")
                                df_rn = pd.read_excel(output_path, sheet_name='RELEVE_NON_POINTEE', dtype=str).fillna("")
                                st.dataframe(df_rn, use_container_width=True)
                                
                        except Exception as e:
                            st.warning(f"Impossible d'afficher l'aperçu complet : {e}")
    
                    else:
                        st.error("Erreur : Le fichier de résultat n'a pas été généré.")
    
                except Exception as e:
                    st.error(f"Une erreur est survenue lors du traitement : {e}")
