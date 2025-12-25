import streamlit as st
from supabase import create_client, Client
import datetime

# Initialisation du client Supabase via les secrets Streamlit
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Erreur de configuration Supabase : {e}")
    supabase = None

def login_user(email, password):
    """Connecte l'utilisateur via Supabase Auth"""
    if not supabase: return False, "Erreur connexion DB"
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return True, "Connexion réussie."
    except Exception as e:
        msg = str(e)
        if "Invalid login credentials" in msg:
            return False, "Identifiants incorrects."
        return False, f"Erreur de connexion : {msg}"

def register_user(email, password, nom, prenoms, telephone, entreprise):
    """Inscrit un nouvel utilisateur via Supabase Auth + Metadata"""
    if not supabase: return False, "Erreur connexion DB"
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "nom": nom,
                    "prenoms": prenoms,
                    "telephone": telephone,
                    "entreprise": entreprise
                }
            }
        })
        # Note: Si email confirmation activé, user ne pourra pas se loguer tout de suite.
        # Mais le trigger handle_new_user créera l'entrée dans user_profiles.
        return True, "Compte créé avec succès ! Veuillez vérifier votre boîte mail pour confirmer votre email afin de pouvoir vous connecter."
    except Exception as e:
        return False, f"Erreur d'inscription : {e}"

def get_current_user_id(email):
    """Récupère l'ID utilisateur à partir de l'email (nécessite d'être connecté ou admin service role, 
       mais ici on triche un peu on requête user_profiles car on est en mode 'anon' client qui a des droits RLS pour 'own').
       Atttention: Avec l'API Client 'anon', on ne peut voir que SON propre profil si RLS activé.
       Si l'utilisateur n'est pas logué dans le contexte 'supabase', ça peut échouer.
       
       Cependant, streamlit tourne côté serveur python. 
       L'auth state n'est pas persisté automatiquement dans l'objet 'supabase' global entre les reruns sans session token.
       
       Solution robuste pour cette app : On doit re-signin ou utiliser le token stocké en session state.
    """
    # Pour faire simple dans ce contexte Streamlit :
    # On va faire une query sur user_profiles en filtrant par email.
    # SI RLS est bien configuré pour 'select using (auth.uid() = id)', 
    # ALORS il faut que le client supabase soit authentifié.
    # Dans login_user, on a récupéré une session. Il faudrait la stocker.
    pass

# HACK: Pour l'instant, comme on ne gère pas le token de session Supabase persistant dans l'objet global,
# on va supposer que pour des actions "serveur" critiques (décrémenter crédits), on devrai peut-être utiliser la Service Key
# ou alors, plus simple : On stocke le session_access_token et on le set sur le client supabase.

def _get_authenticated_client(email):
    """
    Essaie de récupérer un client authentifié pour l'utilisateur.
    En environnement réel, on utiliserait le access_token stocké en session_state.
    Ici, simplifions en supposant que l'utilisateur vient de se loguer ou on fait confiance aux appels.
    PROBLÈME : Avec RLS, on ne pourra pas lire/écrire les données d'un user sans son token.
    
    ALTERNATIVE : Utiliser la clé 'service_role' (admin) pour faire les opérations au nom de l'utilisateur.
    C'est souvent plus simple pour une petite app Streamlit interne/perso.
    Mais on n'a que la clé ANON.
    
    Donc on doit stocker la session lors du login.
    """
    if 'supabase_session' in st.session_state:
        session = st.session_state['supabase_session']
        # On crée un client avec le token
        # supabase.auth.set_session(session.access_token, session.refresh_token) # Pas toujours dispo en py
        # On configure le header Auth
        supabase.postgrest.auth(session.access_token)
        return supabase
    return supabase


def login_user(email, password):
    if not supabase: return False, "Erreur DB"
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        # On stocke la session complète
        st.session_state['supabase_session'] = res.session
        st.session_state['user_id'] = res.user.id
        return True, "Connexion réussie."
    except Exception as e:
        msg = str(e)
        if "Invalid login credentials" in msg:
            return False, "Email ou mot de passe incorrect."
        return False, f"Erreur de connexion : {msg}"

def get_credits(email):
    # On utilise le client authentifié
    client = _get_authenticated_client(email)
    try:
        # On suppose que l'utilisateur est connecté et qu'on a son ID
        user_id = st.session_state.get('user_id')
        if not user_id: return 0
        
        data = client.table("user_profiles").select("credits").eq("id", user_id).single().execute()
        return data.data.get('credits', 0)
    except:
        return 0

def get_user_name(email):
    client = _get_authenticated_client(email)
    try:
        user_id = st.session_state.get('user_id')
        if not user_id: return email
        
        data = client.table("user_profiles").select("nom, prenoms").eq("id", user_id).single().execute()
        res = data.data
        if res:
            nom = res.get('nom', '')
            prenoms = res.get('prenoms', '')
            full_name = f"{prenoms} {nom}".strip()
            return full_name if full_name else email
        return email
    except:
        return email

def decrement_credits(email):
    client = _get_authenticated_client(email)
    try:
        current = get_credits(email)
        if current > 0:
            user_id = st.session_state.get('user_id')
            client.table("user_profiles").update({"credits": current - 1}).eq("id", user_id).execute()
            return True
    except Exception as e:
        print(e)
    return False

def upload_to_storage(file_bytes, file_name, content_type="application/pdf"):
    """
    Upload un fichier dans le bucket 'reports' de Supabase.
    Retourne l'URL publique ou None en cas d'échec.
    """
    # Récupération de la session
    session = st.session_state.get('supabase_session')
    
    # On recrée un client léger pour s'assurer que l'auth est isolée
    local_supabase = create_client(url, key)
    
    if session:
        # Authentification propre utilisant l'access token ET le refresh token
        try:
             local_supabase.auth.set_session(session.access_token, session.refresh_token)
        except Exception as auth_err:
             st.warning(f"Attention auth: {auth_err}")
             # Fallback si set_session échoue (ex: token expiré sans refresh auto ici)
             local_supabase.postgrest.auth(session.access_token)
             local_supabase.storage.session.headers["Authorization"] = f"Bearer {session.access_token}"

    try:
        user_id = st.session_state.get('user_id')
        if not user_id:
            st.error("Erreur interne : ID utilisateur introuvable. Veuillez vous reconnecter.")
            return None
            
        destination_path = f"{user_id}/{file_name}"
        
        # Upload
        res = local_supabase.storage.from_("reports").upload(
            file=file_bytes,
            path=destination_path,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        
        # URL publique
        public_url = local_supabase.storage.from_("reports").get_public_url(destination_path)
        return public_url

    except Exception as e:
        # Affiche l'erreur complète pour le débogage
        st.error(f"Echec de l'upload vers le cloud ({content_type}): {e}")
        # Souvent l'erreur est "The resource was not found" si le bucket n'existe pas
        # ou "new row violates row-level security policy" si pas les droits.
        return None

def add_history_remote(email, file_info):
    """
    Version modifiée pour stocker les URLs distantes.
    file_info attend désormais 'url_excel' et 'url_pdf' (optionnel) au lieu de paths locaux.
    """
    client = _get_authenticated_client(email)
    try:
        user_id = st.session_state.get('user_id')
        data = {
            "user_id": user_id,
            "path": file_info.get('url_excel'), # On réutilise les colonnes existantes
            "pdf_path": file_info.get('url_pdf'),
            "banque": file_info.get('banque'),
            "date_gen": file_info.get('date_gen')
        }
        client.table("reconciliation_history").insert(data).execute()
    except Exception as e:
        print(f"Erreur historique: {e}")

def get_history(email):
    client = _get_authenticated_client(email)
    try:
        user_id = st.session_state.get('user_id')
        # Order by created_at desc
        response = client.table("reconciliation_history").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Erreur get history: {e}")
        return []
