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




# Configuration de la page
st.set_page_config(page_title="RAPP 5", layout="wide", initial_sidebar_state="expanded")

# --- GESTION DE L'ETAT (STATE) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0
if 'show_profile' not in st.session_state:
    st.session_state.show_profile = False

def reset_callback():
    st.session_state.reset_key += 1
    # On reste sur la vue actuelle sauf si on veut forcer l'accueil
    st.session_state.nav_selection = "Accueil"
    if 'processed_data' in st.session_state:
        del st.session_state['processed_data']

def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = ""


# Gestion du logout via URL (pour le bouton dans le header)
if "logout" in st.query_params:
    logout()
    st.query_params.clear() # Nettoie l'URL


@st.cache_data(ttl=3600*24) # Cache pour 24h, le logo change rarement
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

# --- HACK: Récupération du Hash URL pour OAuth/Reset Password ---
# Streamlit ne voit pas le hash (#) de l'URL côté serveur.
# On injecte du JS pour détecter le hash de récupération (type=recovery)
# et recharger la page avec les tokens en query params (?recovery_token=...)

# On vérifie si on a déjà capturé les tokens via query params
query_params = st.query_params
recovery_access_token = query_params.get("access_token", None)
recovery_refresh_token = query_params.get("refresh_token", None)
recovery_type = query_params.get("type", None)



if (recovery_type == "recovery" or "access_token" in query_params) and recovery_access_token:
    # On a les tokens dans l'URL (suite au rechargement JS), on tente la connexion
    try:
        # On authentifie l'utilisateur avec ces tokens
        # st.info("Validation du token de récupération en cours...")
        res = auth_manager.supabase.auth.set_session(recovery_access_token, recovery_refresh_token)
        if res and res.user:
            st.session_state.authenticated = True
            st.session_state.user_email = res.user.email
            st.session_state.user_id = res.user.id
            st.session_state.password_reset_mode = True # Drapeau pour afficher le formulaire de changement
            # On nettoie l'URL pour la propreté
            st.query_params.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Erreur de validation du lien de récupération : {e}")

# Script JS d'interception amélioré
# Il va scanner le hash pour trouver access_token et type=recovery
# Et rediriger vers l'URL propre avec query params
st.markdown("""
<script>
console.log("Supabase Auth Listener Active");

const hash = window.location.hash;
console.log("Current Hash:", hash);

if (hash && hash.includes("access_token")) {
    console.log("Tokens detected in hash, processing...");
    
    // Parser le hash
    const params = new URLSearchParams(hash.substring(1));
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");
    const type = params.get("type");
    
    console.log("Type:", type);
    
    // On redirige si on trouve un access token (quel que soit le type pour l'instant, ou filtré sur recovery)
    if (accessToken) {
        // Construction de la nouvelle URL
        // On conserve le pathname actuel
        const baseUrl = window.location.origin + window.location.pathname;
        
        // On ajoute les params nécessaires pour Streamlit
        // Note: On ajoute un param 'auth_redirect=true' pour identifier ce reload
        const newUrl = `${baseUrl}?auth_redirect=true&access_token=${accessToken}&refresh_token=${refreshToken || ''}&type=${type || 'recovery'}`;
        
        console.log("Redirecting to:", newUrl);
        window.location.href = newUrl;
    }
}
</script>
""", unsafe_allow_html=True)



# --- UI STYLES ---
st.markdown(style.css_code, unsafe_allow_html=True)

# ==============================================================================
# PAGE D'AUTHENTIFICATION (Si non connecté)
# ==============================================================================

# Cas Spécial : Si on est en mode Reset Password (connecté via lien magique)
if st.session_state.get('password_reset_mode', False):
    st.markdown(f"<div style='text-align: center; margin-bottom: 0px;'>{img_tag}</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Réinitialisation du mot de passe</h2>", unsafe_allow_html=True)
    
    with st.form("new_password_form"):
        st.info("Veuillez définir votre nouveau mot de passe.")
        new_pass = st.text_input("Nouveau mot de passe", type="password")
        new_pass_conf = st.text_input("Confirmer le mot de passe", type="password")
        btn_change = st.form_submit_button("Changer le mot de passe", type="primary")
        
    if btn_change:
        if new_pass != new_pass_conf:
            st.error("Les mots de passe ne correspondent pas.")
        elif len(new_pass) < 6:
            st.error("Le mot de passe doit faire au moins 6 caractères.")
        else:
            success, msg = auth_manager.update_password(new_pass)
            if success:
                st.success(msg)
                st.session_state.password_reset_mode = False # On quitte le mode reset
                time.sleep(2)
                st.rerun()
            else:
                st.error(msg)
    
    st.stop() # On affiche QUE ça


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
            
            st.write("")
            with st.expander("Mot de passe oublié ?"):
                st.write("Entrez votre email pour recevoir un lien de réinitialisation.")
                reset_email = st.text_input("Votre Email", key="reset_email_input")
                if st.button("Envoyer le lien"):
                    if reset_email:
                        success, msg = auth_manager.send_password_reset(reset_email)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Veuillez entrer une adresse email.")
                    
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
                        
                        # On vide les champs manuellement en forçant des valeurs vides
                        keys_to_clear = ["reg_email", "reg_nom", "reg_prenoms", "reg_tel_num", "reg_ent", "reg_pass", "reg_pass_conf"]
                        for key in keys_to_clear:
                             st.session_state[key] = ""
                        
                        # Pour le selectbox, on ne peut pas mettre "", on laisse le rerun le remettre à defaut ou on force l'index 0 si besoin
                        if "reg_ind" in st.session_state:
                             del st.session_state["reg_ind"]
                        
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
    user_id = st.session_state.get('user_id')
    user_credits = auth_manager.get_credits(user_id)
    user_name = auth_manager.get_user_name(user_id, st.session_state.user_email)
    st.sidebar.markdown(f"**Utilisateur :** {user_name}")
    st.sidebar.markdown(f"**Crédit :** {user_credits}")
    
    # Navigation
    # On utilise des espaces insécables ou simplement du texte brut. Le Markdown fonctionne dans st.radio pour les versions récentes
    menu_options = ["Accueil", "Mes rapprochements", "Maquette", "**Mon Profil**", "Nous contacter"]
    if auth_manager.is_admin(user_id):
        menu_options.append("Admin")
        
    nav = st.sidebar.radio("Navigation", menu_options, key="nav_selection")
    
    st.sidebar.markdown("---")

    
    # Espaceur
    st.sidebar.markdown("<br>" * 3, unsafe_allow_html=True)
    
    if st.sidebar.button("NOUVEL E.R", on_click=reset_callback):
        pass # Le callback fait tout

    # --- EN-TETE ---
    # (La fonction get_img_as_base64 est maintenant définie globalement)
    
    # En-tête (Barre avec logo)
    st.markdown(f"""
        <div class="fixed-title">
            {img_tag}
            <a href="?logout=true" target="_self" class="logout-btn-header">Log Out</a>
        </div>
    """, unsafe_allow_html=True)
    
    # --- VIEW: MES RAPPROCHEMENTS ---
    if nav == "Mes rapprochements":
        # Remonter le contenu avec une marge négative pour compenser le padding global
        st.markdown('<div class="main-content" style="margin-top: -60px;">', unsafe_allow_html=True)
        st.markdown("<h3>Mes Rapprochements</h3>", unsafe_allow_html=True)
        
        history = auth_manager.get_history(user_id)
        
        if not history:
            st.info("Aucun rapprochement effectué pour le moment.")
        else:
            # En-têtes du tableau
            with st.container():
                h1, h2, h3, h4, h5 = st.columns([2, 1, 2, 1, 1])
                h1.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>Date</div>", unsafe_allow_html=True)
                h2.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>Mois</div>", unsafe_allow_html=True)
                h3.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>Banque</div>", unsafe_allow_html=True)
                h4.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>Aperçu</div>", unsafe_allow_html=True)
                h5.markdown("<div style='font-weight:bold; color:#2c3e50; font-size:1.1rem;'>D/L</div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 5px 0; border: 2px solid #2c3e50;'>", unsafe_allow_html=True)

            # Lignes du tableau (Conteneur scrollable)
            # Utilisation de height=... pour fixer la zone et permettre le scroll vertical
            # tout en gardant l'en-tête (défini au dessus) fixe.
            with st.container(height=500):
                for idx, item in enumerate(history):
                    with st.container():
                        c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 1])
                        date_gen = item.get('date_gen', 'N/A')
                        mois_val = item.get('mois', '-') or '-' # Handle None/Empty
                        banque = item.get('banque', 'Inconnue')
                        pdf_path = item.get('url_pdf') or item.get('pdf_path', '')
                        excel_path = item.get('url_excel') or item.get('excel_path', '')
                        
                        # Alignement vertical du texte
                        c1.markdown(f"<div style='padding-top: 10px;'>{date_gen}</div>", unsafe_allow_html=True)
                        c2.markdown(f"<div style='padding-top: 10px;'>{mois_val}</div>", unsafe_allow_html=True)
                        c3.markdown(f"<div style='padding-top: 10px;'>{banque}</div>", unsafe_allow_html=True)
                        
                        if pdf_path:
                            if pdf_path.startswith("http"):
                                 # Lien vers le stockage cloud (Supabase)
                                 # Bouton Aperçu (Ouvre dans nouvel onglet)
                                 c4.markdown(f'<a href="{pdf_path}" target="_blank" style="text-decoration: none;"><button style="border: 1px solid #2196F3; background-color: white; color: #2196F3; padding: 5px 10px; border-radius: 5px; cursor: pointer;">👁️</button></a>', unsafe_allow_html=True)
                                 
                                 # Bouton Télécharger
                                 c5.markdown(f'<a href="{pdf_path}" target="_blank" style="text-decoration: none;"><button style="border: 1px solid #4CAF50; background-color: white; color: #4CAF50; padding: 5px 10px; border-radius: 5px; cursor: pointer;">⇩</button></a>', unsafe_allow_html=True)
                                 
                            elif os.path.exists(pdf_path):
                                # Fichier local
                                with open(pdf_path, "rb") as f:
                                    c4.download_button(
                                        label="⇩",
                                        data=f,
                                        file_name=os.path.basename(pdf_path),
                                        mime="application/pdf",
                                        key=f"dl_pdf_{idx}"
                                    )
                                    c5.write("")
                            else:
                                c4.markdown("<span style='color: grey;'>-</span>", unsafe_allow_html=True)
                                c5.markdown("<span style='color: grey;'>-</span>", unsafe_allow_html=True)
                        else:
                            c4.markdown("<span style='color: grey;'>-</span>", unsafe_allow_html=True)
                            c5.markdown("<span style='color: grey;'>-</span>", unsafe_allow_html=True)
                            

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
    
    # --- VIEW: MON PROFIL ---
    if nav == "**Mon Profil**":
        st.markdown('<div class="main-content" style="margin-top: -60px;">', unsafe_allow_html=True)
        st.markdown("<h3>Mon Profil</h3>", unsafe_allow_html=True)
        
        # Charge les infos
        current_profile = auth_manager.get_user_profile(user_id)
        
        if not current_profile:
            st.error("Impossible de charger le profil.")
        else:
            with st.form("profile_form"):
                st.subheader("Informations Personnelles")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    new_nom = st.text_input("Nom", value=current_profile.get('nom', ''))
                    new_tel = st.text_input("Téléphone", value=current_profile.get('telephone', ''))
                with col_p2:
                    new_prenoms = st.text_input("Prénoms", value=current_profile.get('prenoms', ''))
                    new_ent = st.text_input("Entreprise", value=current_profile.get('entreprise', ''))
                
                st.markdown("<br>", unsafe_allow_html=True)
                btn_update = st.form_submit_button("Mettre à jour", type="primary")
            
            if btn_update:
                success, msg = auth_manager.update_user_profile(user_id, new_nom, new_prenoms, new_tel, new_ent)
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
                    
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # --- VIEW: NOUS CONTACTER ---
    if nav == "Nous contacter":
        st.markdown('<div class="main-content" style="margin-top: -60px;">', unsafe_allow_html=True)
        st.markdown("<h3>Nous contacter</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-top: 20px; border: 1px solid #ddd;">
            <p style="font-size: 1.1rem; margin-bottom: 15px; color: #2c3e50;">
                📞 <strong>Contact :</strong> +228 97031387
            </p>
            <p style="font-size: 1.1rem; color: #2c3e50;">
                ✉️ <strong>Email :</strong> <a href="mailto:tayif01@gmail.com" style="text-decoration: none; color: #2980b9;">tayif01@gmail.com</a>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # --- VIEW: ADMINISTRATION ---
    if nav == "Admin":
        if not auth_manager.is_admin(user_id):
            st.error("Accès refusé.")
            st.stop()
            
        st.markdown('<div class="main-content" style="margin-top: -60px;">', unsafe_allow_html=True)
        st.markdown("<h3>🛡️ Administration</h3>", unsafe_allow_html=True)
        st.markdown("<p>Gestion des utilisateurs et des crédits.</p>", unsafe_allow_html=True)
        
        if st.button("🔄 Actualiser la liste"):
            auth_manager.get_all_users.clear()
            auth_manager._get_admin_client.clear()
            auth_manager.get_credits.clear()
            auth_manager.is_admin.clear()
            st.rerun()

        users = auth_manager.get_all_users()
        
        if not users:
            st.warning("Impossible de charger la liste des utilisateurs (vérifiez la clé service_role).")
        else:
            # Création d'une liste formatée pour le selectbox
            # On utilise le nom, prénoms et ID pour identifier
            user_options = {f"{u.get('nom','Inconnu')} {u.get('prenoms','Inconnu')} - {u.get('credits',0)} crédits (ID: {u.get('id', '')[:8]}...)": u['id'] for u in users}
            selected_label = st.selectbox("Sélectionner un utilisateur", list(user_options.keys()))
            
            if selected_label:
                selected_uid = user_options[selected_label]
                selected_user = next((u for u in users if u['id'] == selected_uid), None)
                
                # Card info user
                st.info(f"**Utilisateur sélectionné :** {selected_user.get('nom','')} {selected_user.get('prenoms','')}\n\n**Entreprise :** {selected_user.get('entreprise', 'N/A')}\n\n**Téléphone :** {selected_user.get('telephone', 'N/A')}")
                
                col_cred1, col_cred2, col_cred3 = st.columns([1, 1, 1])
                with col_cred1:
                     # Check overrides
                     display_credits = selected_user.get('credits', 0)
                     if "local_credits" in st.session_state and selected_uid in st.session_state["local_credits"]:
                         display_credits = st.session_state["local_credits"][selected_uid]
                     st.metric("Crédits actuels", display_credits)
                
                with col_cred2:
                    ad_key = f"cred_adj_{selected_uid}"
                    if ad_key not in st.session_state:
                        st.session_state[ad_key] = 0
                    credits_to_add = st.number_input("Ajustement (+/-)", step=1, key=ad_key)
                
                with col_cred3:
                    st.write("") 
                    st.write("") 
                    def update_credit_callback(uid):
                        # Récupère la valeur directement depuis le state
                        val = st.session_state.get(f"cred_adj_{uid}", 0)
                        if val != 0:
                            # Note: admin_update_credits renvoie maintenant (success, msg, NEW_TOTAL)
                            # On ne récupère que les 2 premiers pour compatibilité si l'edit n'est pas vu, 
                            # mais idéalement on unpack 3 valeurs.
                            res = auth_manager.admin_update_credits(uid, val)
                            if len(res) == 3:
                                success, msg, new_total = res
                            else:
                                success, msg = res
                                new_total = 0 # Should not happen with new code

                            if success:
                                st.session_state["admin_msg"] = ("success", msg)
                                # Le reset fonctionne ici car on est dans le callback (avant le rerun)
                                st.session_state[f"cred_adj_{uid}"] = 0
                                
                                # Mise à jour locale pour affichage instantané
                                if "local_credits" not in st.session_state: st.session_state["local_credits"] = {}
                                st.session_state["local_credits"][uid] = new_total
                            else:
                                st.session_state["admin_msg"] = ("error", msg)
                        else:
                            st.session_state["admin_msg"] = ("warning", "Veuillez saisir une valeur.")

                    
                    st.button("Valider l'ajustement", type="primary", key=f"btn_valid_{selected_uid}", on_click=update_credit_callback, args=(selected_uid,))
                    
                    # Affichage du message après le rerun
                    if "admin_msg" in st.session_state:
                         m_type, m_text = st.session_state["admin_msg"]
                         if m_type == "success": st.success(m_text)
                         elif m_type == "error": st.error(m_text)
                         elif m_type == "warning": st.warning(m_text)
                         del st.session_state["admin_msg"]

                st.markdown("---")
                
                with st.expander("Zone de danger (Suppression)"):
                    st.warning("Attention : La suppression est irréversible.")
                    if st.button("Supprimer cet utilisateur", type="secondary", key=f"btn_del_init_{selected_uid}"):
                        st.session_state[f"confirm_delete_{selected_uid}"] = True
                        
                    if st.session_state.get(f"confirm_delete_{selected_uid}"):
                         st.error(f"Êtes-vous VRAIMENT sûr de vouloir supprimer {selected_user.get('nom','')} ?")
                         col_del1, col_del2 = st.columns(2)
                         with col_del1:
                             def delete_user_callback(uid):
                                 success, msg = auth_manager.admin_delete_user(uid)
                                 if success:
                                     st.session_state["admin_msg"] = ("success", msg)
                                     # Reset du state de confirmation
                                     if f"confirm_delete_{uid}" in st.session_state:
                                         del st.session_state[f"confirm_delete_{uid}"]
                                     # IMPORTANT: Si l'user supprimé est celui affiché, il faut recharger la liste ou gérer l'erreur de display
                                     # Le plus simple est de clear le cache users
                                     auth_manager.get_all_users.clear()
                                 else:
                                     st.session_state["admin_msg"] = ("error", msg)
                             
                             st.button("OUI, Supprimer", key=f"btn_del_confirm_{selected_uid}", type="primary", on_click=delete_user_callback, args=(selected_uid,))

                         with col_del2:
                             def cancel_delete_callback(uid):
                                 st.session_state[f"confirm_delete_{uid}"] = False
                                 
                             st.button("Annuler", key=f"btn_del_cancel_{selected_uid}", on_click=cancel_delete_callback, args=(selected_uid,))


        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # --- VIEW: ACCUEIL ---
    # --- FORMULAIRE PRINCIPAL ---
    
    # Sélection de la banque et Date
    cols_sel = st.columns(4)
    with cols_sel[0]:
        banques = ["Orabank", "BOA", "UTB", "Sunu Bank"]
        choix_banque = st.selectbox("Sélectionnez votre banque", banques, key=f"banque_{st.session_state.reset_key}")
    
    with cols_sel[1]:
        mois_options = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        mois_rapprochement = st.selectbox("Mois de rapprochement", mois_options, key=f"mois_rap_{st.session_state.reset_key}")

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
        if auth_manager.get_credits(user_id) <= 0:
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
            start_time = time.time()
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
                        status_text.info("Etat de Rapprochement en cours de traitement... (Veuillez patienter quelques secondes)")
                        
                        # Création d'un fichier temporaire pour le PDF
                        try:
                            # Dossier temporaire pour les uploads
                            os.makedirs("temp_uploads", exist_ok=True)
                            temp_pdf_path = os.path.join("temp_uploads", file_upload.name)
                            
                            with open(temp_pdf_path, "wb") as f:
                                f.write(file_upload.getbuffer())
                                
                        # Lancement du pipeline d'extraction via main.py / run_extraction_pipeline
                            with st.status("Traitement en cours...", expanded=True) as status:
                                # st.write("Préparation de l'environnement...")
                                
                                # Callback pour mettre à jour le statut
                                def update_status(msg):
                                    if not msg.startswith("OCR page") and not msg.startswith("Traitement OCR"):
                                        status.update(label=msg)
                                
                                extracted_excel_path = pdf_extractor.run_extraction_pipeline(temp_pdf_path, bank_name=choix_banque, status_callback=update_status)                            
                                
                                if extracted_excel_path and os.path.exists(extracted_excel_path):
                                    status.update(label="Extraction terminée !", state="complete", expanded=False)
                                    
                                    df_releve = pd.read_excel(extracted_excel_path, engine='openpyxl')
                                    
                                    # Chargement des données pour le bouton de téléchargement (hors du bloc status pour visibilité)
                                    with open(extracted_excel_path, "rb") as f:
                                        excel_data = f.read()
                                    excel_name = os.path.basename(extracted_excel_path)
                                    
                                    time.sleep(1) 
                                else:
                                    status.update(label="Échec de l'extraction", state="error")
                                    st.error("L'extraction du PDF a échoué (Résultat vide). Vérifiez si le PDF est valide.")
                                    st.stop()
                                               
                        except ValueError as ve:
                             status_text.empty()
                             status.update(label="Opération annulée", state="error", expanded=False)
                             # Affiche le message "cette banque n'est pas actif..." proprement
                             st.error(str(ve))
                             st.stop()
                                
                        except Exception as e:
                            st.error(f"Erreur CRITIQUE lors de l'analyse du PDF : {e}")
                            with st.expander("Voir les détails techniques (pour support)"):
                                st.code(str(e))
                                import traceback
                                st.code(traceback.format_exc())
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
                    auth_manager.decrement_credits(user_id)
                    
                    date_display = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # On sauvegarde les URLs publiques dans l'historique
                    # Note: Si l'upload échoue (url=None), on aura None en base, ce qui est acceptable pour l'instant.
                    auth_manager.add_history_remote(user_id, {
                        'url_excel': url_excel,
                        'url_pdf': url_pdf,
                        'banque': choix_banque,
                        'date_gen': date_display,
                        'mois': mois_rapprochement
                    })


                    # Invalidation explicite du cache historique
                    # auth_manager.get_history.clear()

                    # NETTOYAGE DES FICHIERS TEMPORAIRES ET SOURCE
                    # Uniquement si un PDF a été traité (temp_pdf_path défini)
                    if 'temp_pdf_path' in locals() and temp_pdf_path:
                        # On appelle la fonction de nettoyage du module main (alias pdf_extractor)
                        pdf_extractor.cleanup_extraction_artifacts(temp_pdf_path)

                    end_time = time.time()
                    duration = end_time - start_time

                    # Stockage des résultats dans la session pour persistance
                    st.session_state['processed_data'] = {
                        'excel_bytes': excel_buffer.getvalue(),
                        'pdf_bytes': pdf_bytes,
                        'stats': stats,
                        'nom_fichier_sortie': nom_fichier_sortie,
                        'pdf_filename': pdf_filename,
                        'choix_banque': choix_banque,
                        'duration': duration
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
        duration = data.get('duration', 0)
        st.success(f"Rapprochement terminé pour {choix_banque} ! (durée de traitement : {duration:.2f} s)")
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


