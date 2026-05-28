# RAPP 30 - Outil de Rapprochement Bancaire Automatisé

## Description

**RAPP 30** est une application web professionnelle développée en Python (Streamlit) conçue pour simplifier et automatiser l'état de rapprochement bancaire. L'outil permet aux experts-comptables et responsables financiers de valider la concordance entre leur journal de banque et le relevé bancaire PDF (natif) en quelques secondes.

L'application gère l'extraction intelligente de données depuis des documents PDF natifs, propose une interface utilisateur intuitive et fournit des rapports de rapprochement clés en main (Excel et PDF).

## Fonctionnalités Clés

- **Extraction PDF multi-banques** : Architecture extensible permettant d'ajouter une nouvelle banque sans modifier le reste du code. Banques actuellement supportées : **Orabank**, **Trésor (DGTCP)**.
- **Rapprochement Automatisé** : Algorithme de pointage croisé (débit banque ↔ crédit compta, crédit banque ↔ débit compta) avec tolérance sur les arrondis flottants.
- **Détection des opérations annulées** : Identification automatique des paires débit/crédit de même montant avec libellé similaire sur le relevé.
- **Gestion des Suspens** :
    - Prise en compte de l'état de rapprochement du mois précédent.
    - Identification claire des écritures non pointées (suspens banque et compta).
- **Rapports Professionnels** :
    - Fichier Excel complet avec mise en forme (bordures, en-têtes, format comptable) sur toutes les feuilles.
    - Rapport PDF prêt à imprimer.
- **Espace Utilisateur Sécurisé** :
    - Authentification (Login/Inscription) gérée via Supabase.
    - Gestion de profil utilisateur avec crédits d'utilisation.
    - Historique des rapprochements effectués avec liens de téléchargement cloud.
- **Ressources (Maquette)** : Mise à disposition de modèles de fichiers pour standardiser les imports.

## Architecture Technique

Le projet repose sur une stack moderne et robuste :

- **Backend / Frontend** : Python avec [Streamlit](https://streamlit.io/) pour une interface réactive et rapide.
- **Traitement de Données** :
    - `pandas` et `numpy` pour la manipulation et l'analyse des flux financiers.
    - `openpyxl` et `xlrd` pour la lecture et l'écriture de fichiers Excel.
- **Traitement de Documents** :
    - `PyMuPDF` (fitz) pour le découpage et l'extraction de texte haute fidélité par analyse de coordonnées de layout.
- **Base de Données & Auth** : [Supabase](https://supabase.com/) (PostgreSQL) pour la gestion des utilisateurs, l'authentification et le stockage des fichiers (Buckets).

## Installation et Configuration

### Prérequis

- Python 3.9+
- Un compte Supabase avec un projet configuré (Authentification + Storage).

### Installation

1. **Cloner le dépôt** :
    ```bash
    git clone https://github.com/votre-repo/rapp-bancaire.git
    cd rapp-bancaire
    ```

2. **Créer un environnement virtuel** (recommandé) :
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3. **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

4. **Configuration des variables d'environnement** :
    Créez un dossier `.streamlit` à la racine et ajoutez un fichier `secrets.toml` avec vos clés Supabase :

    ```toml
    [supabase]
    url = "VOTRE_SUPABASE_URL"
    key = "VOTRE_SUPABASE_ANON_KEY"
    ```

### Lancement de l'application

```bash
streamlit run app.py
```

L'application sera accessible par défaut sur `http://localhost:8501`.

## Guide d'Utilisation

1. **Inscription/Connexion** : Créez un compte ou connectez-vous pour accéder à l'interface.
2. **Accueil** :
    - Sélectionnez l'établissement bancaire (Orabank, Trésor…) et la date de rapprochement.
    - **Import 1** : Chargez votre relevé bancaire (PDF natif).
    - **Import 2** : (Optionnel) Chargez l'état de rapprochement du mois précédent (Excel).
    - **Import 3** : Chargez votre journal de banque (Excel).
3. **Traitement** : Cliquez sur "Valider". L'outil extrait les données, effectue le pointage et calcule les soldes rectifiés.
4. **Résultats** : Téléchargez immédiatement votre État de Rapprochement finalisé (Excel & PDF).
5. **Historique** : Retrouvez tous vos précédents rapports dans l'onglet "Mes rapprochements".
6. **Maquettes** : Téléchargez les gabarits Excel via l'onglet dédié pour vous assurer un format compatible.

## Structure du Projet

```
rapp_bancaire/
│
├── app.py                  # Point d'entrée de l'application (Interface Utilisateur)
├── main.py                 # Pipeline d'extraction PDF (Orchestrateur)
├── extract_table.py        # Utilitaires partagés d'extraction et de nettoyage
├── split_pdf.py            # Module de découpage des PDF multi-pages
├── config.py               # Configuration globale (chemins, paramètres)
│
├── extractors/             # Architecture multi-banques (Factory Pattern)
│   ├── __init__.py         # BankExtractorFactory : sélection automatique de l'extracteur
│   ├── base.py             # Classe abstraite BaseExtractor (contrat commun)
│   ├── orabank.py          # Extracteur Orabank (coordonnées de colonnes spécifiques)
│   └── tresor.py           # Extracteur Trésor/DGTCP (coordonnées de colonnes spécifiques)
│
├── _02_rapp.py             # Moteur de calcul du rapprochement bancaire
├── _03_auth_manager.py     # Gestion de l'authentification et des interactions Supabase
├── _04_pdf_utils.py        # Génération des rapports PDF
├── _00_logger.py           # Système de logs structuré
│
├── maquette/               # Modèles de fichiers pour les utilisateurs
└── .streamlit/
    └── secrets.toml        # Clés Supabase (non versionné)
```

## Ajouter une nouvelle banque

L'architecture repose sur un **Factory Pattern**. Pour ajouter une banque :

1. Créer `extractors/ma_banque.py` héritant de `BaseExtractor` :
    ```python
    from .base import BaseExtractor

    class MaBanqueExtractor(BaseExtractor):
        def extract_transactions(self, pdf_path):
            # Logique d'extraction spécifique à la banque
            ...
        def get_solde_precedent(self, pdf_path):
            ...
    ```

2. L'enregistrer dans `extractors/__init__.py` :
    ```python
    _registry = {
        "orabank"   : OrabankExtractor,
        "trésor"    : TresorExtractor,
        "ma_banque" : MaBanqueExtractor,  # ← cette ligne seulement
    }
    ```

3. L'ajouter dans la liste des banques de `app.py` :
    ```python
    banques = ["Orabank", "Trésor", "Ma Banque", ...]
    ```

Aucun autre fichier ne change.

## Auteur

Projet développé par **TAYI Koku Fiam / DSI 2025**.

---
*Dernière mise à jour : Mai 2026*
