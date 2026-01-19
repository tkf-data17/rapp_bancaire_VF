
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

    /* --- BOUTONS MODERNES --- */
    .stButton > button {
        /* Dégradé: Bleu nuit -> Violet -> Touche de Vert Menthe/Emeraude */
        background: linear-gradient(135deg, #2c3e50 0%, #6c5ce7 70%, #00b894 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 4px 6px rgba(44, 62, 80, 0.3);
        width: auto;
        text-transform: uppercase;
        font-size: 0.9rem;
    }

    .stButton > button:hover {
        /* On éclaircit tout au survol */
        background: linear-gradient(135deg, #34495e 0%, #7d6de3 70%, #55efc4 100%);
        transform: translateY(-2px);
        box-shadow: 0 7px 14px rgba(44, 62, 80, 0.4);
        color: white;
    }

    .stButton > button:active {
        transform: translateY(1px);
        box-shadow: 0 2px 4px rgba(44, 62, 80, 0.3);
    }

    /* Style spécifique pour le bouton secondaire (ex: S'inscrire) si géré via st.form_submit_button sans type='primary' ?
       Streamlit applique par défaut un style simple. On peut cibler button[kind="secondary"] si besoin, 
       mais .stButton > button cible tout le monde. 
       On peut ajouter une bordure blanche fine pour le relief. */
    .stButton > button {
        border: 1px solid rgba(255,255,255,0.1);
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

    /* --- SIDEBAR FIXE (Non redimensionnable, non repliable) --- */
    /* Cache le bouton de fermeture de la sidebar */
    [data-testid="stSidebarCollapsedControl"] {
        display: none;
    }
    
    /* Cache la poignée de redimensionnement */
    /* Ciblage approximatif de la div de resize qui est frère de stSidebar */
    div[data-testid="stSidebarUserContent"] {
        padding-top: 2rem; /* Ajustement esthétique */
    }
    
    /* Pour Streamlit récent, le resize handle peut être ciblé différemment ou difficilement.
       On tente une approche générique sur les éléments de redimensionnement */
    div[data-testid="stSidebar"] + div {
        display: none;
    }

    /* Bouton Logout dans le header */
    .logout-btn-header {
        margin-left: auto; /* Pousse à droite */
        margin-right: 30px;
        background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
        color: white !important;
        padding: 6px 16px;
        border-radius: 20px;
        text-decoration: none;
        font-size: 0.75rem; /* Taille réduite */
        font-weight: 500;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .logout-btn-header:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        opacity: 0.9;
    }

    /* Espacement entre les options du bouton radio (Menu Navigation) */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        margin-bottom: 20px !important;
        background-color: transparent !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:last-child {
        margin-bottom: 0px !important;
    }
</style>
"""
