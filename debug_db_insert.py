
import os
import streamlit as st
from supabase import create_client, Client

# Hardcoded keys from secrets.toml for this standalone script
URL = "https://kccdguiozegmdkveewkk.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjY2RndWlvemVnbWRrdmVld2trIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjY2MzAwNiwiZXhwIjoyMDgyMjM5MDA2fQ.9nrY8xtnomq-R0GBARW8ewLJek4xNJHxUz2E6MVvr-M"

def get_admin_client() -> Client:
    return create_client(URL, SERVICE_ROLE_KEY)

client = get_admin_client()

print("--- DIAGNOSTIC SUPABASE ---")

# 1. Vérification de la table user_profiles
try:
    print("Verification 'user_profiles'...")
    res = client.table("user_profiles").select("*").limit(1).execute()
    print("  OK. Result:", res.data)
except Exception as e:
    print("  ERREUR user_profiles:", e)

# 2. Vérification de la table reconciliation_history
try:
    print("Verification 'reconciliation_history'...")
    res = client.table("reconciliation_history").select("*").limit(1).execute()
    print("  OK. Result:", res.data)
except Exception as e:
    print("  ERREUR reconciliation_history (Table manquante ?):", e)

# 3. Vérification de la colonne 'mois'
try:
    print("Verification colonne 'mois' dans 'reconciliation_history'...")
    res = client.table("reconciliation_history").select("mois").limit(1).execute()
    print("  OK. Result:", res.data)
except Exception as e:
    print("  ERREUR colonne 'mois' (Colonne manquante ?):", e)
    if "PGRST204" in str(e):
        print("    -> C'est l'erreur de cache !")

# 4. Tentative d'insertion (Admin Bypass RLS)
# On va insérer une ligne dummy associée au premier user trouvé
try:
    users = client.table("user_profiles").select("id").limit(1).execute()
    if users.data:
        uid = users.data[0]['id']
        print(f"Tentative insertion test pour user {uid}...")
        
        data_insert = {
            "user_id": uid,
            "banque": "TEST_AUTO",
            "date_gen": "TEST",
            "mois": "Janvier Test"
        }
        res = client.table("reconciliation_history").insert(data_insert).execute()
        print("  INSERTION REUSSIE avec colonne mois !")
        
        # Nettoyage
        row_id = res.data[0]['id']
        client.table("reconciliation_history").delete().eq("id", row_id).execute()
        print("  Nettoyage ligne test OK.")
    else:
        print("  Pas d'utilisateurs trouvés pour tester l'insertion.")
except Exception as e:
    print("  ECHEC INSERTION:", e)
    # Retry sans mois par acquis de conscience
    if users.data:
        try:
            print("  Retrying without 'mois'...")
            del data_insert['mois']
            res = client.table("reconciliation_history").insert(data_insert).execute()
            print("  INSERTION REUSSIE SANS colonne mois.")
             # Nettoyage
            row_id = res.data[0]['id']
            client.table("reconciliation_history").delete().eq("id", row_id).execute()
        except Exception as e2:
            print("  ECHEC INSERTION SANS MOIS:", e2)

print("--- FIN DIAGNOSTIC ---")
