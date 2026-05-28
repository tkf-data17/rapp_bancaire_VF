"""
_00_logger.py
=============
Module de logging centralisé pour RAPP 30.
Chaque appel à `log(...)` écrit une entrée dans `debug_log.json`
avec horodatage, niveau, module et message.

Utilisation dans n'importe quel module :
    from _00_logger import log
    log("INFO",  "main",        "Pipeline démarré", {"pdf": "..."})
    log("ERROR", "rapp",        "Erreur pointage",  exc=e)
    log("WARN",  "auth",        "Crédits insuffisants")
"""

import json
import os
import traceback
import threading
from datetime import datetime, timezone

# ── Configuration ────────────────────────────────────────────────────────────
LOG_FILE   = os.path.join(os.path.dirname(__file__), "debug_log.json")
MAX_ENTRIES = 500          # Nombre maximum d'entrées conservées (rotation FIFO)
_lock = threading.Lock()   # Protection thread-safe (Streamlit peut être multi-thread)

LEVELS = {"DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"}

# ── Fonctions internes ───────────────────────────────────────────────────────

def _read_log() -> list:
    """Lit le fichier de log et retourne la liste des entrées."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, OSError):
        # Si le fichier est corrompu, on repart de zéro
        return []


def _write_log(entries: list) -> None:
    """Écrit la liste des entrées dans le fichier de log."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


# ── API publique ─────────────────────────────────────────────────────────────

def log(level: str, module: str, message: str, context: dict = None, exc: Exception = None) -> None:
    """
    Enregistre un message de debug dans debug_log.json.

    Args:
        level   : "DEBUG" | "INFO" | "WARN" | "ERROR" | "CRITICAL"
        module  : Nom du fichier/fonction source (ex: "main", "rapp", "auth")
        message : Description lisible de l'événement
        context : Données supplémentaires (dict optionnel)
        exc     : Exception Python (ajoute le traceback automatiquement)
    """
    level = level.upper()
    if level not in LEVELS:
        level = "INFO"

    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "level":     level,
        "module":    module,
        "message":   message,
    }

    if context:
        # Sérialisation sécurisée : on convertit les types non-JSON en str
        safe_ctx = {}
        for k, v in context.items():
            try:
                json.dumps(v)
                safe_ctx[k] = v
            except (TypeError, ValueError):
                safe_ctx[k] = str(v)
        entry["context"] = safe_ctx

    if exc is not None:
        entry["exception"] = {
            "type":      type(exc).__name__,
            "message":   str(exc),
            "traceback": traceback.format_exc()
        }

    with _lock:
        entries = _read_log()
        entries.append(entry)
        # Rotation FIFO : on garde les MAX_ENTRIES entrées les plus récentes
        if len(entries) > MAX_ENTRIES:
            entries = entries[-MAX_ENTRIES:]
        _write_log(entries)


def clear_log() -> None:
    """Vide complètement le fichier de log (utile en début de session)."""
    with _lock:
        _write_log([])


def get_log(level_filter: str = None, module_filter: str = None, last_n: int = None) -> list:
    """
    Retourne les entrées du log avec filtres optionnels.

    Args:
        level_filter  : Filtre par niveau ("ERROR", "WARN", ...)
        module_filter : Filtre par module ("rapp", "main", ...)
        last_n        : Retourne uniquement les N dernières entrées

    Returns:
        Liste de dicts
    """
    with _lock:
        entries = _read_log()

    if level_filter:
        entries = [e for e in entries if e.get("level") == level_filter.upper()]
    if module_filter:
        entries = [e for e in entries if module_filter.lower() in e.get("module", "").lower()]
    if last_n:
        entries = entries[-last_n:]

    return entries
