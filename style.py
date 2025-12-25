
css_code = """
<style>
    /* Importation d'une police Google Font propre et moderne */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;700&family=Roboto:wght@300;400;500;700&display=swap');

    /* Configuration globale */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: #333333;
    }

    /* Arrière-plan de l'application */
    .stApp {
        background-color: #f4f7f6; /* Gris/bleu très clair, très doux */
    }
    
    /* Cacher le header (hamburger menu, "Running") et le footer de Streamlit */
    header[data-testid="stHeader"] {
        display: none;
    }
    footer {
        display: none;
    }

    /* Ajustement du conteneur principal */
    .block-container {
        padding-top: 80px !important; 
    }

    /* Styles pour le titre fixé en haut */
    .fixed-title {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(90deg, #ffffff, #e6e9f0); /* Dégradé subtil */
        z-index: 99999;
        padding: 10px 0 10px 370px; /* Décalage réduit pour sidebar (~340px) + 10px */
        display: flex;
        align-items: center; /* Centrage vertical */
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 1px solid #ddd;
    }

    .logo-img {
        height: 68px; /* Taille réduite de 25% (90px -> 68px) */
        margin-right: 20px;
        /* border-radius: 50%; Enlevé si le logo est rectangulaire après crop */
    }

    .fixed-title h1 {
        font-family: 'Poppins', sans-serif;
        color: #2c3e50;
        font-weight: 500;
        letter-spacing: 1px;
        margin: 0;
        font-size: 2.5rem;
    }

    /* Marge pour le contenu principal afin qu'il ne soit pas caché par le titre */
    .main-content {
        margin-top: 100px;
        padding: 20px;
    }

    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {
        background-color: #f4f7f6; /* Uniformisé avec le body */
        border-right: 1px solid #e0e0e0;
    }

    /* --- BOUTONS --- */
    .stButton > button {
        background-color: #6c5ce7; /* Violet doux mais dynamique */
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    .stButton > button:hover {
        background-color: #a29bfe; /* Version plus claire au survol */
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        color: white;
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* --- INPUTS (Selectbox, DateInput, FileUploader) --- */
    /* Zone de saisie texte générique et selectbox */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #ced6e0;
    }
    
    /* --- REGLAGES FINS --- */



    /* Labels en GRAS : Ciblage simplifié mais spécifique */
    .stSelectbox label, 
    .stDateInput label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label {
        color: #000000 !important;
        font-weight: 800 !important; /* Gras */
        font-size: 16px !important;
    }

    /* Sassurer que le texte à lintérieur du label hérite du gras */
    .stSelectbox label p, 
    .stDateInput label p,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stDateInput"] label p {
        font-weight: 800 !important;
    }

    /* Explicitement normal pour les autres */
    .stFileUploader label,
    .stFileUploader label p {
        font-weight: normal !important;
        color: #333333 !important;
    }

    /* Mise en forme de la zone drag & drop du file uploader */
    /* Mise en forme de la zone drag & drop du file uploader */
    [data-testid="stFileUploader"] {
        background-color: #fafafa;
        padding: 10px;
        border-radius: 8px;
        border: 1px dashed #b2bec3;
        text-align: center;
    }

    /* Cache le texte 'Limit 200MB per file' */
    [data-testid="stFileUploader"] small {
        display: none !important;
    }

    [data-testid="stFileUploader"] > div {
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }

    /* Style du bouton 'Browse files' à l'intérieur pour qu'il soit plus discret ou cohérent */
    section[data-testid="stFileUploader"] button {
        background-color: transparent !important;
        color: #6c5ce7 !important;
        border: 1px solid #6c5ce7 !important;
        padding: 4px 12px !important;
        font-size: 14px !important;
        line-height: 1.2 !important;
    }
    
    section[data-testid="stFileUploader"] button:hover {
        background-color: #6c5ce7 !important;
        color: white !important;
    }

    /* --- TABLES / DATAFRAMES --- */
    div[data-testid="stDataFrame"] {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    /* --- ALERTES (Info, Success, Error, Warning) --- */
    div[data-testid="stNotification"], div[data-baseweb="notification"] {
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Succès */
    .stSuccess {
        background-color: #dff9fb;
        border-left: 5px solid #6c5ce7;
    }

    /* Headers globaux */
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Lignes de séparation */
    hr {
        border-color: #dfe6e9;
    }
    /* --- LOGO TEXTUEL --- */
    .logo-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .logo-main {
        font-family: 'Poppins', sans-serif;
        color: #2c3e50;
        font-weight: 700;
        font-size: 2.5rem;
        line-height: 1.1;
        margin: 0;
    }
    .logo-sub {
        font-family: 'Roboto', sans-serif;
        color: #6c5ce7;
        font-size: 0.85rem;
        margin-top: -2px;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
</style>
"""
