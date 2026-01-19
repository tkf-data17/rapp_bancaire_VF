import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. INITIALISATION AVEC CACHE ---
import os

def get_config(section, key, env_var_name=None):
    """Récupère une config depuis st.secrets ou os.environ."""
    # 1. Essai via st.secrets (Priorité Dev Local)
    try:
        if section in st.secrets and key in st.secrets[section]:
            return st.secrets[section][key]
    except Exception:
        pass
    
    # 2. Essai via os.environ (Priorité Prod / Docker)
    if env_var_name:
         val = os.environ.get(env_var_name)
         if val: return val
         
    return None

# On utilise cache_resource pour que le client soit créé UNE SEULE FOIS pour toute la session
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        # Récupération URL
        url = get_config("supabase", "url", "SUPABASE_URL")
        
        # Récupération Key (Plusieurs variantes possibles)
        key = get_config("supabase", "key", "SUPABASE_KEY") or \
              get_config("supabase", "anon_key", "SUPABASE_ANON_KEY") or \
              get_config("supabase", "api_key", "SUPABASE_API_KEY")

        if not url or not key:
            # Initialisation échouée : On l'affiche clairement pour le débogage sur le cloud
            error_msg = "❌ Configuration Supabase incomplète. Les variables d'environnement 'SUPABASE_URL' et 'SUPABASE_KEY' sont introuvables."
            print(error_msg)
            st.error(error_msg)
            return None

        # Fix warning: Storage endpoint URL should have a trailing slash
        if not url.endswith("/"):
             url += "/"
             
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erreur de configuration Supabase : {e}")
        return None

supabase = get_supabase_client()

# --- 2. FONCTION UTILITAIRE POUR L'AUTH ---
def _get_authenticated_client():
    """Configure le client avec le token de session actuel."""
    session = st.session_state.get('supabase_session')
    if session and supabase:
        # On injecte le token dans les headers pour le RLS sans recréer le client
        supabase.postgrest.auth(session.access_token)
        supabase.storage.session.headers["Authorization"] = f"Bearer {session.access_token}"
    return supabase

@st.cache_resource
def _get_admin_client():
    """Crée un client Supabase avec les droits d'admin (service_role)."""
    try:
        url = get_config("supabase", "url", "SUPABASE_URL")
        if url and not url.endswith("/"):
             url += "/"
             
        key = get_config("supabase", "service_role", "SUPABASE_SERVICE_ROLE") or \
              get_config("supabase", "service_role_key", "SUPABASE_SERVICE_ROLE_KEY")
              
        if not key:
            print("DEBUG: 'service_role' key NOT FOUND in secrets/env!")
            return None
        return create_client(url, key)
    except Exception as e:
        print(f"DEBUG: Error creating admin client: {e}")
        return None

# --- 3. GESTION DES CREDITS (AVEC CACHE DE DONNÉES) ---
# On cache le résultat pendant 2 minutes pour éviter de requêter à chaque clic
@st.cache_data(ttl=120)
def get_credits(user_id):
    if not user_id: return 0
    client = _get_authenticated_client()
    try:
        data = client.table("user_profiles").select("credits").eq("id", user_id).single().execute()
        return data.data.get('credits', 0)
    except:
        return 0

# --- 4. RÉCUPÉRATION DU NOM (CACHÉ) ---
@st.cache_data(ttl=3600) # Le nom ne change pas souvent, on cache 1h
def get_user_name(user_id, email): # On passe user_id au lieu d'email pr clé de cache fiable
    if not user_id: return email
    client = _get_authenticated_client()
    try:
        # On tente de récupérer le info
        data = client.table("user_profiles").select("nom, prenoms").eq("id", user_id).single().execute()
        res = data.data
        if res:
            return f"{res.get('prenoms', '')} {res.get('nom', '')}".strip() or email
    except:
        pass
    return email

# --- 5. HISTORIQUE (CACHÉ) ---
@st.cache_data(ttl=60) # On rafraîchit toutes les minutes
def get_history(user_id):
    if not user_id: return []
    client = _get_authenticated_client()
    try:
        response = client.table("reconciliation_history").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return []

# --- 5b. PROFIL UTILISATEUR (CACHÉ) ---
@st.cache_data(ttl=60)
def get_user_profile(user_id):
    """Récupère le profil complet de l'utilisateur."""
    if not user_id: return None
    client = _get_authenticated_client()
    try:
        data = client.table("user_profiles").select("*").eq("id", user_id).single().execute()
        return data.data
    except Exception as e:
        return None

def update_user_profile(user_id, nom, prenoms, telephone, entreprise):
    """Met à jour les informations du profil utilisateur."""
    client = _get_authenticated_client()
    if not client: return False, "Erreur client"
    try:
        data = {
            "nom": nom,
            "prenoms": prenoms,
            "telephone": telephone,
            "entreprise": entreprise
        }
        client.table("user_profiles").update(data).eq("id", user_id).execute()
        
        # Invalidation des caches
        get_user_profile.clear()
        get_user_name.clear()
        get_all_users.clear()
        
        return True, "Profil mis à jour avec succès."
    except Exception as e:
        return False, f"Erreur mise à jour : {e}"

# --- 6. ACTIONS (SANS CACHE car elles modifient la DB) ---

def login_user(email, password):
    if not supabase: return False, "Erreur DB"
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state['supabase_session'] = res.session
        st.session_state['user_id'] = res.user.id
        # On vide le cache spécifique pour forcer la recharge des infos du nouvel utilisateur
        get_credits.clear()
        get_user_name.clear()
        get_history.clear()
        is_admin.clear()
        return True, "Connexion réussie."
    except Exception as e:
        msg = str(e)
        if "Invalid login credentials" in msg:
            return False, "Identifiants incorrects."
        return False, f"Erreur de connexion : {msg}"

def register_user(email, password, nom, prenoms, telephone, entreprise):
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
        return True, "Compte créé avec succès ! Veuillez vérifier votre boîte mail."
    except Exception as e:
        return False, f"Erreur d'inscription : {e}"

def decrement_credits(user_id):
    client = _get_authenticated_client()
    try:
        # Lecture directe pour avoir la valeur réelle (hors cache)
        data = client.table("user_profiles").select("credits").eq("id", user_id).single().execute()
        current = data.data.get('credits', 0)
        
        if current > 0:
            client.table("user_profiles").update({"credits": current - 1}).eq("id", user_id).execute()
            # On invalide le cache pour que l'interface affiche la nouvelle valeur
            get_credits.clear()
            return True
    except:
        pass
    return False

def send_password_reset(email):
    """Envoie un email de réinitialisation de mot de passe."""
    if not supabase: return False, "Erreur connexion DB"
    try:
        # On essaie de récupérer l'URL de l'application depuis les secrets (configuration pour la prod)
        # Sinon on fallback sur localhost ou None (laissant Supabase utiliser son Site URL par défaut)
        # On essaie de récupérer l'URL de l'application depuis les secrets ou env
        site_url = get_config("app", "url", "APP_URL")
        
        options = {"redirect_to": site_url} if site_url else {}
        supabase.auth.reset_password_email(email, options=options)
        
        return True, "Email de réinitialisation envoyé ! Vérifiez votre boîte de réception (et les spams)."
    except Exception as e:
        return False, f"Erreur lors de l'envoi : {e}"

def update_password(new_password):
    """Met à jour le mot de passe de l'utilisateur connecté."""
    if not supabase: return False, "Erreur connexion DB"
    try:
        supabase.auth.update_user({"password": new_password})
        return True, "Mot de passe modifié avec succès !"
    except Exception as e:
        return False, f"Erreur modification mot de passe : {e}"

def add_history_remote(user_id, file_info):
    client = _get_authenticated_client()
    try:
        get_history.clear() # Invalidation car on ajoute une ligne
        data = {
            "user_id": user_id,
            "path": file_info.get('url_excel'), 
            "pdf_path": file_info.get('url_pdf'),
            "banque": file_info.get('banque'),
            "date_gen": file_info.get('date_gen')
        }
        client.table("reconciliation_history").insert(data).execute()
    except Exception as e:
        print(f"Erreur historique: {e}")

def upload_to_storage(file_bytes, file_name, content_type="application/pdf"):
    client = _get_authenticated_client()
    user_id = st.session_state.get('user_id')
    if not user_id: return None
    
    try:
        destination_path = f"{user_id}/{file_name}"
        client.storage.from_("reports").upload(
            file=file_bytes,
            path=destination_path,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        return client.storage.from_("reports").get_public_url(destination_path)
    except Exception as e:
        st.error(f"Erreur upload: {e}")
        return None

# --- 7. ADMINISTRATION (SERVICE ROLE REQUIRED) ---

@st.cache_data(ttl=3600)
def is_admin(user_id):
    """Vérifie si l'utilisateur est admin."""
    if not user_id: return False
    # On essaye avec le client admin si dispo, sinon le client auth
    client = _get_admin_client() or _get_authenticated_client() or supabase
    try:
        data = client.table("user_profiles").select("is_admin").eq("id", user_id).single().execute()
        return data.data.get("is_admin", False)
    except:
        return False

@st.cache_data(ttl=60)
def get_all_users():
    """Récupère tous les profils utilisateurs (Admin only)."""
    client = _get_admin_client()
    if not client: return []
    try:
        response = client.table("user_profiles").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return []

def admin_update_credits(target_user_id, amount):
    """Ajoute (ou retire) des crédits (Admin only)."""
    client = _get_admin_client()
    if not client: return False, "Clé Service Role manquante"
    try:
        # Lire
        data = client.table("user_profiles").select("credits").eq("id", target_user_id).single().execute()
        current = data.data.get('credits', 0)
        
        new_total = max(0, current + amount)
        
        # Ecrire
        # Ecrire
        client.table("user_profiles").update({"credits": new_total}).eq("id", target_user_id).execute()
        
        # Optimisation : On ne clear PAS la liste globale (trop lent), on clear juste le crédit unitaire
        # get_all_users.clear() <--- Retiré pour performance
        get_credits.clear()
        return True, f"Crédits mis à jour : {new_total}", new_total
    except Exception as e:
        return False, f"Erreur update: {e}", 0

def admin_delete_user(target_user_id):
    """Supprime un utilisateur via Auth Admin (Admin only)."""
    client = _get_admin_client()
    if not client: return False, "Clé Service Role manquante"
    
    try:
        # 1. Suppression des données liées (Cascading manuel pour sécurité)
        try:
             client.table("reconciliation_history").delete().eq("user_id", target_user_id).execute()
             client.table("user_profiles").delete().eq("id", target_user_id).execute()
        except:
             pass # Si échec, on tente quand même la suppression Auth (le cascade SQL peut prendre le relais)

        # 2. Suppression du compte Auth
        client.auth.admin.delete_user(target_user_id)
        get_all_users.clear()
        return True, "Utilisateur supprimé."
    except Exception as e:
        return False, f"Erreur suppression: {e}"
