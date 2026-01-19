
import os

secrets_content = """[supabase]
url = "https://kccdguiozegmdkveewkk.supabase.co"

# Clés publiques
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjY2RndWlvemVnbWRrdmVld2trIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY2NjMwMDYsImV4cCI6MjA4MjIzOTAwNn0.KyJypgOXEocYJd7IUxvG1C4tUCAMagKKh39-u_sUWqc"
anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjY2RndWlvemVnbWRrdmVld2trIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY2NjMwMDYsImV4cCI6MjA4MjIzOTAwNn0.KyJypgOXEocYJd7IUxvG1C4tUCAMagKKh39-u_sUWqc"

# Clés privées (Admin)
service_role = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjY2RndWlvemVnbWRrdmVld2trIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjY2MzAwNiwiZXhwIjoyMDgyMjM5MDA2fQ.9nrY8xtnomq-R0GBARW8ewLJek4xNJHxUz2E6MVvr-M"
service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjY2RndWlvemVnbWRrdmVld2trIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjY2MzAwNiwiZXhwIjoyMDgyMjM5MDA2fQ.9nrY8xtnomq-R0GBARW8ewLJek4xNJHxUz2E6MVvr-M"

[app]
url = "http://localhost:8501"
"""

target_path = os.path.join(".streamlit", "secrets.toml")
with open(target_path, "w") as f:
    f.write(secrets_content)

print(f"✅ Secrets written to {target_path}")
