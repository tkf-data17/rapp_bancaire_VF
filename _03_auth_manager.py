import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. INITIALISATION AVEC CACHE ---
# On utilise cache_resource pour que le client soit créé UNE SEULE FOIS pour toute la session
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        # Fix warning: Storage endpoint URL should have a trailing slash
        if url and not url.endswith("/"):
             url += "/"
             
        key = st.secrets["supabase"]["key"]
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
        url = st.secrets["supabase"]["url"]
        if url and not url.endswith("/"):
             url += "/"
             
        key = st.secrets["supabase"].get("service_role")
        if not key:
            print("DEBUG: 'service_role' key NOT FOUND in secrets!")
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
        client.table("user_profiles").update({"credits": new_total}).eq("id", target_user_id).execute()
        # Invalider le cache pour que tout le monde voit la maj
        get_all_users.clear()
        get_credits.clear()
        return True, f"Crédits mis à jour : {new_total}"
    except Exception as e:
        return False, f"Erreur update: {e}"

def admin_delete_user(target_user_id):
    """Supprime un utilisateur via Auth Admin (Admin only)."""
    client = _get_admin_client()
    if not client: return False, "Clé Service Role manquante"
    
    try:
        client.auth.admin.delete_user(target_user_id)
        get_all_users.clear()
        return True, "Utilisateur supprimé."
    except Exception as e:
        return False, f"Erreur suppression: {e}"
