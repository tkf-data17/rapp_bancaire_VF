
# auth_manager.py - Version simplifiée sans base de données

# Identifiants par défaut
DEFAULT_USER = "admin"
DEFAULT_PASS = "654321"

def login_user(email, password):
    """
    Vérifie les identifiants par rapport aux valeurs par défaut.
    """
    if email == DEFAULT_USER and password == DEFAULT_PASS:
        return True, "Connexion réussie."
    else:
        return False, "Identifiants incorrects."

def register_user(email, password):
    """
    L'inscription est désactivée dans ce mode simplifié.
    """
    return False, f"Inscription désactivée. Veuillez utiliser l'identifiant '{DEFAULT_USER}' et le mot de passe '{DEFAULT_PASS}'."
