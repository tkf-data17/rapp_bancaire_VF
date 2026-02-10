
import os
import json
from supabase import create_client, Client

# Hardcoded keys
URL = "https://kccdguiozegmdkveewkk.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjY2RndWlvemVnbWRrdmVld2trIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjY2MzAwNiwiZXhwIjoyMDgyMjM5MDA2fQ.9nrY8xtnomq-R0GBARW8ewLJek4xNJHxUz2E6MVvr-M"

def get_admin_client() -> Client:
    return create_client(URL, SERVICE_ROLE_KEY)

client = get_admin_client()

output = []
output.append("--- AUDIT START ---")

try:
    # 1. Récupérer les 10 dernières entrées de l'historique
    res = client.table("reconciliation_history").select("*").order("created_at", desc=True).limit(10).execute()
    entries = res.data
    
    if entries:
        output.append(f"Found {len(entries)} entries.")
        for entry in entries:
            output.append(f"Entry ID: {entry.get('id')}")
            output.append(f"  User ID: {entry.get('user_id')}")
            output.append(f"  Mois: {entry.get('mois')}")
            output.append(f"  Date Gen: {entry.get('date_gen')}")
            output.append(f"  Created At: {entry.get('created_at')}")
    else:
        output.append("NO ENTRIES FOUND.")

except Exception as e:
    output.append(f"ERROR: {e}")

output.append("--- AUDIT END ---")

with open("audit_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Audit finished. Check audit_result.txt")
