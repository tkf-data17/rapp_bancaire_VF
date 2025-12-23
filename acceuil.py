import streamlit as st
import os
import rapp  # Import du module de traitement
import style # Import du fichier de style
import base64
import importlib
importlib.reload(style) # Force le rechargement du style à chaque run

# Configuration de la page
# Configuration de la page
st.set_page_config(page_title="RAPP 5", layout="wide", initial_sidebar_state="expanded")


if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def reset_callback():
    st.session_state.reset_key += 1

st.sidebar.button("Nouvel ER", on_click=reset_callback)

st.markdown(style.css_code, unsafe_allow_html=True)



def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    img_path = os.path.join("src_image", "logo_cropped.png")
    img_base64 = get_img_as_base64(img_path)
    img_tag = f'<img src="data:image/png;base64,{img_base64}" class="logo-img">'
except Exception:
    img_tag = ""

st.markdown(f"""
    <div class="fixed-title">
        {img_tag}
    </div>
""", unsafe_allow_html=True)

# Sélection de la banque
# Sélection de la banque et Date
cols_sel = st.columns(4)
with cols_sel[0]:
    banques = ["Orabank", "BOA", "UTB", "Sunu Bank"]
    choix_banque = st.selectbox("Sélectionnez votre banque", banques, key=f"banque_{st.session_state.reset_key}")

with cols_sel[2]:
    date_arrete = st.date_input("Date de rapprochement", key=f"date_{st.session_state.reset_key}")

st.markdown("---")

# Zone d'inputs alignées horizontalement
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. Relevé Bancaire")
    releve_file = st.file_uploader("Ajoutez votre relevé bancaire original", type=['xlsx', 'xls', 'csv', 'pdf'], key=f"releve_{st.session_state.reset_key}")

with col2:
    st.subheader("2. E R Précédent")
    etat_prec_file = st.file_uploader("Ajoutez votre etat de rapprochement du mois précédent", type=['xlsx', 'xls'], key=f"etat_{st.session_state.reset_key}")

with col3:
    st.subheader("3. Journal Banque")
    journal_file = st.file_uploader("Ajoutez votre journal banque", type=['xlsx', 'xls', 'csv'], key=f"journal_{st.session_state.reset_key}")

st.markdown("---")

import pandas as pd

# Bouton de validation
if st.button("Valider"):
    missing_files = []
    # Le champ 2 est optionnel pour le moment
    if not releve_file:
        missing_files.append("Relevé bancaire")
    if not journal_file:
        missing_files.append("Journal banque")
    
    if missing_files:
        st.error(f"Veuillez charger les fichiers manquants : {', '.join(missing_files)}")
    else:
        with st.spinner('Traitement en cours...'):
            try:
                # Création du dossier documents s'il n'existe pas
                upload_dir = "documents"
                os.makedirs(upload_dir, exist_ok=True)

                path_releve = os.path.join(upload_dir, "relevé.xlsx")
                path_journal = os.path.join(upload_dir, "journal_banque.xlsx")

                # Fonction de conversion/sauvegarde
                def save_converted(upload, target):
                    # Détection de l'extension d'origine
                    ext = upload.name.split('.')[-1].lower()
                    
                    if ext == 'csv':
                        # Lecture CSV et sauvegarde Excel
                        df = pd.read_csv(upload)
                        df.to_excel(target, index=False)
                    elif ext in ['xls', 'xlsx']:
                        # Lecture Excel et sauvegarde Excel (standardisation .xlsx)
                        # Pour lire xls, il faut xlrd. Si pas installé, on suppose xlsx ou on handle l'erreur
                        # On essaie de lire tel quel
                        try:
                            df = pd.read_excel(upload)
                            df.to_excel(target, index=False)
                        except Exception as e:
                            # Fallback: écriture directe si c'est déjà un xlsx valide et qu'on veut juste copier
                            # Mais pour garantir le nom .xlsx et le format, mieux vaut passer par pandas si possible
                            # Si échec lecture, on tente l'écriture binaire simple si extension match
                            if ext == 'xlsx':
                                upload.seek(0)
                                with open(target, "wb") as f:
                                    f.write(upload.getbuffer())
                            else:
                                raise e
                    else:
                        raise ValueError(f"Format non supporté: {ext}")

                # Sauvegarde Convertie
                save_converted(releve_file, path_releve)
                             
                # Sauvegarde directe du journal (toujours Excel)
                with open(path_journal, "wb") as f:
                    f.write(journal_file.getbuffer())

                path_etat = None
                # Si etat_prec_file est fourni
                if etat_prec_file:
                    path_etat = os.path.join(upload_dir, "Etat_prec.xlsx")
                    with open(path_etat, "wb") as f:
                        f.write(etat_prec_file.getbuffer())

                # Définition du nom de fichier de sortie dynamique
                nom_fichier_sortie = f"Etat_Rapprochement_{choix_banque}.xlsx"
                output_path = os.path.join("documents", nom_fichier_sortie)

                # Exécution du rapprochement
                rapp.executer_rapprochement(path_releve, path_journal, path_etat, output_path, date_rapprochement=date_arrete)
                
                st.success(f"Rapprochement terminé pour {choix_banque} !")
                
                # Zone Output
                st.markdown("### Résultat")
                
                if os.path.exists(output_path):
                    with open(output_path, "rb") as file:
                        btn = st.download_button(
                            label="télécharger ER",
                            data=file,
                            file_name=nom_fichier_sortie,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    st.markdown("### Aperçu des résultats")
                    
                    try:
                        # Lecture des différentes feuilles pour affichage
                        # On lit en 'object' pour garder tel quel, puis on nettoie
                        df_rapp = pd.read_excel(output_path, sheet_name='RAPPROCHEMENT', header=None)
                        df_rapp = df_rapp.fillna("")
                        
                        # --- LOGIQUE DE RECALCUL DES TOTAUX POUR L'AFFICHAGE ---
                        # Excel généré par openpyxl contient des formules, pandas lit les formules ou NaN (pas les valeurs calculées).
                        # Il faut donc recalculer les totaux en Python pour l'affichage Streamlit.
                        
                        # 1. Trouver la ligne "Totaux"
                        # La colonne B est l'index 1
                        mask_totaux = df_rapp[1].astype(str).str.contains("Totaux", case=False, na=False)
                        if mask_totaux.any():
                            idx_totaux = df_rapp[mask_totaux].index[0]
                            
                            # Conversion des données numériques (Ligne 2 jusqu'à Totaux exclus)
                            # Cols C(2), D(3), E(4), F(5)
                            cols_nums = [2, 3, 4, 5]
                            
                            # On convertit en numérique, en forçant les erreurs en NaN (puis 0)
                            subset = df_rapp.iloc[2:idx_totaux, cols_nums].apply(pd.to_numeric, errors='coerce').fillna(0)
                            
                            # Calcul des Totaux
                            totaux = subset.sum()
                            
                            # Mise à jour de la ligne "Totaux" dans le DF d'affichage
                            for col_idx in cols_nums:
                                df_rapp.iat[idx_totaux, col_idx] = totaux[col_idx]
                            
                            # --- CALCUL DU SOLDE RECTIFIE (Ligne suivante) ---
                            idx_rectif = idx_totaux + 1
                            if idx_rectif < len(df_rapp):
                                # Rappel Logique rapp.py :
                                # C (Débit) = Si Credit(D) > Debit(C) alors Credit - Debit
                                # D (Crédit) = Si Debit(C) > Credit(D) alors Debit - Credit
                                
                                tot_c = totaux[2] # Débit CC
                                tot_d = totaux[3] # Crédit CC
                                tot_e = totaux[4] # Débit Relevé
                                tot_f = totaux[5] # Crédit Relevé
                                
                                rect_c = (tot_d - tot_c) if (tot_d - tot_c) > 0 else 0
                                rect_d = (tot_c - tot_d) if (tot_c - tot_d) > 0 else 0
                                
                                rect_e = (tot_f - tot_e) if (tot_f - tot_e) > 0 else 0
                                rect_f = (tot_e - tot_f) if (tot_e - tot_f) > 0 else 0
                                
                                # Mise à jour DF
                                df_rapp.iat[idx_rectif, 2] = rect_c if rect_c != 0 else ""
                                df_rapp.iat[idx_rectif, 3] = rect_d if rect_d != 0 else ""
                                df_rapp.iat[idx_rectif, 4] = rect_e if rect_e != 0 else ""
                                df_rapp.iat[idx_rectif, 5] = rect_f if rect_f != 0 else ""
                                
                                # --- CALCUL TOTAUX GENERAUX (Ligne encore suivante) ---
                                idx_gen = idx_rectif + 1
                                if idx_gen < len(df_rapp):
                                    # Somme Totaux + Rectif
                                    gen_c = tot_c + rect_c
                                    gen_d = tot_d + rect_d
                                    gen_e = tot_e + rect_e
                                    gen_f = tot_f + rect_f
                                    
                                    df_rapp.iat[idx_gen, 2] = gen_c
                                    df_rapp.iat[idx_gen, 3] = gen_d
                                    df_rapp.iat[idx_gen, 4] = gen_e
                                    df_rapp.iat[idx_gen, 5] = gen_f

                        # Formatage Final pour l'affichage (milliers séparés, pas de décimales inutiles)
                        # On applique ça sur les colonnes 2,3,4,5 à partir de la ligne 2
                        def format_num(x):
                            if isinstance(x, (int, float)):
                                if x == 0: return "" # On masque les zéros pour la clarté ? Ou on met "0" -> User prefer "0" usually or empty if calculated formula gave empty.
                                # Dans le calcul rectif j'ai mis "" si 0.
                                return f"{x:,.0f}".replace(",", " ")
                            return x

                        col_indices = [2, 3, 4, 5]
                        for i in col_indices:
                             # On applique le formatage ligne par ligne pour éviter de casser les headers headers
                             df_rapp.iloc[2:, i] = df_rapp.iloc[2:, i].apply(format_num)

                        st.subheader("Tableau de Rapprochement")
                        st.dataframe(df_rapp, use_container_width=True, hide_index=True)
                        
                        # Optionnel : Afficher aussi les suspens
                        with st.expander("Voir les détails des suspens"):
                            st.write("#### Opérations Non Pointées - Journal")
                            df_jn = pd.read_excel(output_path, sheet_name='JOURNAL_NON_POINTEE', dtype=str).fillna("")
                            st.dataframe(df_jn, use_container_width=True)

                            st.write("#### Opérations Non Pointées - Relevé")
                            df_rn = pd.read_excel(output_path, sheet_name='RELEVE_NON_POINTEE', dtype=str).fillna("")
                            st.dataframe(df_rn, use_container_width=True)
                            
                    except Exception as e:
                        st.warning(f"Impossible d'afficher l'aperçu complet (tentative de recalcul): {e}")

                else:
                    st.error("Erreur : Le fichier de résultat n'a pas été généré.")

            except Exception as e:
                st.error(f"Une erreur est survenue lors du traitement : {e}")
