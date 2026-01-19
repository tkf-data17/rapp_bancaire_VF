FROM python:3.10-slim-bullseye

# 1. Création d'un utilisateur non-root (obligatoire pour Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /app

# 2. Installation des dépendances (en tant que root)
USER root
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Installation des dépendances Python
COPY --chown=user:user requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir --user -r requirements.txt

# 4. Copie du code avec les bons droits
COPY --chown=user:user . .

# 5. Configuration du port pour Hugging Face
ENV PORT=7860

# Retour à l'utilisateur non-root pour l'exécution
USER user

# 6. Commande de lancement (L'adresse 0.0.0.0 est cruciale)
CMD ["sh", "-c", "streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0"]


# FROM python:3.10-slim-bullseye

# WORKDIR /app

# # Installation des dépendances système
# RUN apt-get update && apt-get install -y \
#     tesseract-ocr \
#     tesseract-ocr-fra \
#     libtesseract-dev \
#     libgl1-mesa-glx \
#     libglib2.0-0 \
#     gcc \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Installation des dépendances Python
# COPY requirements.txt .
# # On force l'installation dans l'espace global
# RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# COPY . .

# # Configuration du port dynamique pour Koyeb
# ENV PORT=8000

# # Utilisation du chemin complet vers Python pour garantir l'exécution
# CMD ["sh", "-c", "/usr/local/bin/python -m streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0"]