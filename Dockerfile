FROM python:3.10-slim-bullseye

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
# On force l'installation dans l'espace global
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Configuration du port dynamique pour Koyeb
ENV PORT=8000

# Utilisation du chemin complet vers Python pour garantir l'exécution
CMD ["sh", "-c", "/usr/local/bin/python -m streamlit run _01_acceuil.py --server.port ${PORT} --server.address 0.0.0.0"]