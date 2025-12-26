# RAPP 30 - Outil de Rapprochement Bancaire Automatisé

## 📋 Description

**RAPP 30** est une application web professionnelle développée en Python (Streamlit) conçue pour simplifier et automatiser l'état de rapprochement bancaire. L'outil permet aux experts-comptables et responsables financiers de valider la concordance entre leur journal de banque et le relevé bancaire PDF en quelques secondes.

L'application gère l'extraction intelligente de données depuis des documents PDF, propose une interface utilisateur intuitive et fournit des rapports de rapprochement clés en main (Excel et PDF).

## ✨ Fonctionnalités Clés

*   **Extraction PDF Intelligente** : Conversion automatique des relevés bancaires PDF en données structurées exploitables, y compris la gestion des documents scannés via OCR (Tesseract).
*   **Rapprochement Automatisé** : Algorithme puissant comparant les écritures comptables et bancaires pour identifier automatiquement les correspondances (montants, dates).
*   **Gestion des Suspens** :
    *   Prise en compte de l'état de rapprochement du mois précédent.
    *   Identification claire des écritures non pointées (suspendus banque et compta).
*   **Rapports Professionnels** :
    *   Génération d'un fichier Excel complet incluant le tableau de rapprochement et le détail des suspens.
    *   Génération d'un rapport PDF prêt à imprimer.
*   **Espace Utilisateur Sécurisé** :
    *   Authentification (Login/Inscription) gérée via Supabase.
    *   Gestion de profil utilisateur avec crédits d'utilisation.
    *   Historique des rapprochements effectués avec liens de téléchargement cloud.
*   **Ressources (Maquette)** : Mise à disposition de modèles de fichiers pour standardiser les imports.

## 🏗️ Architecture Technique

Le projet repose sur une stack moderne et robuste :

*   **Backend / Frontend** : Python avec [Streamlit](https://streamlit.io/) pour une interface réactive et rapide.
*   **Traitement de Données** :
    *   `pandas` et `numpy` pour la manipulation et l'analyse des flux financiers.
    *   `openpyxl` et `xlrd` pour la lecture et l'écriture de fichiers Excel.
*   **Traitement de Documents** :
    *   `PyMuPDF` (fitz) et `pdfplumber` pour l'extraction de texte.
    *   `pytesseract` pour l'OCR des documents non natifs.
*   **Base de Données & Auth** : [Supabase](https://supabase.com/) (PostgreSQL) pour la gestion des utilisateurs, l'authentification et le stockage des fichiers (Buckets).

## 🚀 Installation et Configuration

### Prérequis

*   Python 3.9+
*   [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installé et accessible dans le PATH système.
*   Un compte Supabase avec un projet configuré (Authentification + Storage).

### Installation

1.  **Cloner le dépôt** :
    ```bash
    git clone https://github.com/votre-repo/rapp-bancaire.git
    cd rapp-bancaire
    ```

2.  **Créer un environnement virtuel** (recommandé) :
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration des variables d'environnement** :
    Créez un dossier `.streamlit` à la racine et ajoutez un fichier `secrets.toml` avec vos clés Supabase :

    ```toml
    [supabase]
    url = "VOTRE_SUPABASE_URL"
    key = "VOTRE_SUPABASE_ANON_KEY"
    ```
    *(Alternativement, utilisez un fichier `.env` si vous adaptez le chargeur de configuration)*

### Lancement de l'application

Pour démarrer l'application en local :

```bash
streamlit run _01_acceuil.py
```

L'application sera accessible par défaut sur `http://localhost:8501`.

## 📖 Guide d'Utilisation

1.  **Inscription/Connexion** : Créez un compte ou connectez-vous pour accéder à l'interface.
2.  **Accueil** :
    *   Sélectionnez l'établissement bancaire et la date de rapprochement.
    *   **Import 1** : Chargez votre relevé bancaire (PDF).
    *   **Import 2** : (Optionnel) Chargez l'état de rapprochement du mois précédent (Excel).
    *   **Import 3** : Chargez votre journal de banque (Excel).
3.  **Traitement** : Cliquez sur "Valider". L'outil extrait les données, effectue le pointage et calcule les soldes rectifiés.
4.  **Résultats** : Téléchargez immédiatement votre État de Rapprochement finalisé (Excel & PDF).
5.  **Historique** : Retrouvez tous vos précédents rapports dans l'onglet "Mes rapprochements".
6.  **Maquettes** : Téléchargez les gabarits Excel via l'onglet dédié pour vous assurer un format compatible.

## 📂 Structure du Projet

*   `_01_acceuil.py` : Point d'entrée de l'application (Interface Utilisateur).
*   `_02_rapp.py` : Moteur de calcul du rapprochement bancaire.
*   `_03_auth_manager.py` : Gestion de l'authentification et des interactions base de données.
*   `_04_pdf_utils.py` : Utilitaires pour la génération des rapports PDF.
*   `_05_style.py` : Définitions CSS pour le styling de l'interface.
*   `main.py` : Pipeline d'extraction des données PDF (Orchestrateur).
*   `extract_table.py` : Scripts d'analyse et d'extraction tabulaire.
*   `split_pdf.py` : Module de découpage et de préparation OCR des PDF.
*   `config.py` : Fichier de configuration globale.
*   `maquette/` : Dossier contenant les modèles de fichiers pour les utilisateurs.

## 👥 Auteur

Projet développé par **[TAYI Koku Fiam/ DSI 2025]**.

---
*Dernière mise à jour : Décembre 2025*
