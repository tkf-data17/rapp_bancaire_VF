# Utiliser une image Python légère officielle
FROM python:3.10-slim-bullseye

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Installer les dépendances système nécessaires
# tesseract-ocr : le moteur OCR
# tesseract-ocr-fra : pack de langue française pour Tesseract
# libgl1-mesa-glx : souvent requis pour les bibliothèques d'image
# poppler-utils : outils PDF utiles (ex: pdftoppm) si besoin
RUN apt-get update --fix-missing && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier des dépendances Python
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le reste du code source dans le conteneur
COPY . .

# Exposer le port par défaut de Streamlit
EXPOSE 8501

# Définir la commande de démarrage
# On précise l'adresse 0.0.0.0 pour être accessible depuis l'extérieur du conteneur
CMD ["streamlit", "run", "_01_acceuil.py", "--server.port=8501", "--server.address=0.0.0.0"]
