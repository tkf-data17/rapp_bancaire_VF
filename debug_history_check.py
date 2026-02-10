
import os
from supabase import create_client

# Hardcoded keys
URL = "https://kccdguiozegmdkveewkk.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjY2RndWlvemVnbWRrdmVld2trIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjY2MzAwNiwiZXhwIjoyMDgyMjM5MDA2fQ.9nrY8xtnomq-R0GBARW8ewLJek4xNJHxUz2E6MVvr-M"

def get_admin_client():
    return create_client(URL, SERVICE_ROLE_KEY)

client = get_admin_client()

print("--- AUDIT DE LA TABLE HISTORIQUE ---")

try:
    # 1. Récupérer les 10 dernières entrées de l'historique (tout utilisateur confondu)
    print("Récupération des 10 dernières entrées...")
    res = client.table("reconciliation_history").select("*").order("created_at", desc=True).limit(10).execute()
    
    entries = res.data
    print(f"Nombre d'entrées trouvées : {len(entries)}")
    
    if entries:
        print("\nDétails des dernières entrées :")
        for entry in entries:
            print(f"- ID: {entry.get('id')}")
            print(f"  User ID: {entry.get('user_id')}")
            print(f"  Banque: {entry.get('banque')}")
            print(f"  Date Gen: {entry.get('date_gen')}")
            print(f"  Mois: {entry.get('mois')}") # Vérifie si la colonne existe et est remplie
            print(f"  Created At: {entry.get('created_at')}")
            print("---")
            
        # 2. Vérifier les utilisateurs pour voir si l'ID correspond à un user existant
        user_ids = list(set([e['user_id'] for e in entries]))
        print(f"\nVérification des Users IDs trouvés : {user_ids}")
        
        for uid in user_ids:
            try:
                user_res = client.table("user_profiles").select("email, nom").eq("id", uid).single().execute()
                print(f"  User {uid}: Found - Email: {user_res.data.get('email')}")
            except Exception as e:
                print(f"  User {uid}: ERROR retrieving profile - {e}")

    else:
        print("AUCUNE DONNÉE TROUVÉE DANS LA TABLE.")

except Exception as e:
    print(f"ERREUR GENERALE: {e}")
    if "PGRST204" in str(e):
        print("-> Problème de cache schéma confirmé (colonne manquante pour l'API).")

print("--- FIN AUDIT ---")
