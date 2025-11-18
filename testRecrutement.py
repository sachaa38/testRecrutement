import streamlit as st
from openai import OpenAI
import os
import tempfile
from PyPDF2 import PdfReader
import pandas as pd
from docx import Document
from datetime import datetime

# ===== Configuration OpenAI =====
st.sidebar.title("Configuration OpenAI")
api_key = st.sidebar.text_input("Clé API OpenAI :", type="password")

# Récupère la clé automatiquement depuis Streamlit Cloud
api_key = st.secrets["openai"]["api_key"]  # <-- sécurisée

client = OpenAI(api_key=api_key)

# ===== Dossier temporaire =====
UPLOAD_FOLDER = "cv_uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ===== Fonctions utilitaires =====
def extraire_texte_pdf(fichier_pdf):
    try:
        pdf_reader = PdfReader(fichier_pdf)
        texte = ""
        for page in pdf_reader.pages:
            texte += page.extract_text() + "\n"
        return texte
    except Exception as e:
        return f"Erreur lors de l'extraction PDF : {str(e)}"

def extraire_texte_docx(fichier_docx):
    try:
        doc = Document(fichier_docx)
        texte = ""
        for paragraph in doc.paragraphs:
            texte += paragraph.text + "\n"
        return texte
    except Exception as e:
        return f"Erreur lors de l'extraction DOCX : {str(e)}"

def lire_fichier_texte(chemin_fichier):
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Erreur lecture fichier texte : {str(e)}"

def analyser_fichier_cv(chemin_fichier):
    extension = os.path.splitext(chemin_fichier)[1].lower()
    if extension == '.pdf':
        with open(chemin_fichier, 'rb') as f:
            return extraire_texte_pdf(f)
    elif extension == '.docx':
        return extraire_texte_docx(chemin_fichier)
    elif extension in ['.txt', '.doc']:
        return lire_fichier_texte(chemin_fichier)
    else:
        return f"Format non supporté : {extension}"

# ===== Nouvelle fonction d'appel modèle =====
def getCompletion(prompt, system_prompt="", messages=[]):
    if not client:
        return "Erreur : clé API non configurée."
    
    if system_prompt != "" and len(messages) == 0:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        text = response.choices[0].message.content
        messages.append({"role": "assistant", "content": text})
        return text
    except Exception as e:
        return f"Erreur API OpenAI : {str(e)}"

# ===== Évaluation des CVs =====
def evaluer_cv(contenu_cv, description_poste, nom_fichier):
    prompt = f"""
Tu es un chargé de recrutement expérimenté, spécialisé dans le poste de {description_poste}.

DESCRIPTION DU POSTE :
{description_poste}

CV À ANALYSER (fichier: {nom_fichier}) :
{contenu_cv}


    

    Analyse le CV ci-dessous selon les critères suivants :
    1 Compétences techniques (maîtrise des technologies requises pour {description_poste}) — /10
    2 Expérience professionnelle pertinente pour {description_poste} — /6
    3 Formation ou certifications pertinentes en lien avec {description_poste} — /2

    Fais la somme des points pour donner une note totale sur 20.

    Donne ta réponse uniquement sous ce format strict :
    Nom : [nom du candidat]
    Expérience : [nombre d'années d'expérience]
    Compétences : [liste des compétences présentes dans le CV, séparées par des /]
    Compatibilité : [note finale sur 20 : "/20"]

    Ne donne aucun commentaire, ne reformule rien d’autre."""

    evaluation = getCompletion(prompt)
    if evaluation.startswith("Erreur"):
        return evaluation, 0

    # Extraction simple du score
    score = 0
    for line in evaluation.split('\n'):
        if "/20" in line:
            try:
                score = int(line.split('/20')[0].split()[-1])
            except:
                pass
            break
    return evaluation, score

# ===== Interface principale =====
def main():
    st.title("🤖 Assistant d'Évaluation de CVs")
    st.markdown("Cette application évalue automatiquement la pertinence des CVs pour un poste donné.")

    # 1️⃣ Upload de l’offre d’emploi
    st.header("1. 📄 Offre d'emploi")
    offre_upload = st.file_uploader("Déposez l'offre d'emploi (PDF)", type=['pdf'])
    description_poste = ""
    if offre_upload:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(offre_upload.getvalue())
            texte_offre = extraire_texte_pdf(tmp_file.name)
        if not texte_offre.startswith("Erreur"):
            description_poste = texte_offre
            st.success("✅ Offre d'emploi chargée avec succès !")
            with st.expander("Voir le contenu extrait de l'offre"):
                st.text_area("Contenu de l'offre", texte_offre, height=200)
        else:
            st.error(texte_offre)

    # 2️⃣ Upload des CVs
    st.header("2. 📁 CVs à analyser")
    uploaded_files = st.file_uploader("Sélectionnez les CVs", type=['pdf', 'docx', 'txt', 'doc'], accept_multiple_files=True)

    # 3️⃣ Lancer l’analyse
    st.header("3. 🚀 Analyse des CVs")
    if st.button("🔍 Lancer l'analyse"):
        if not description_poste:
            st.error("Veuillez d'abord uploader l'offre d'emploi.")
            return
        if not uploaded_files:
            st.error("Veuillez sélectionner au moins un CV.")
            return
        if not client:
            st.error("Veuillez entrer votre clé API OpenAI dans la barre latérale.")
            return

        progress_bar = st.progress(0)
        results = []
        for i, uploaded_file in enumerate(uploaded_files):
            nom_fichier = uploaded_file.name
            file_path = os.path.join(UPLOAD_FOLDER, nom_fichier)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            contenu_cv = analyser_fichier_cv(file_path)
            if contenu_cv.startswith("Erreur"):
                st.error(contenu_cv)
                results.append({'Fichier': nom_fichier, 'Score': 0, 'Statut': 'Erreur', 'Évaluation': contenu_cv})
            else:
                with st.spinner(f"Analyse de {nom_fichier}..."):
                    evaluation, score = evaluer_cv(contenu_cv, description_poste, nom_fichier)
                if evaluation.startswith("Erreur"):
                    st.error(evaluation)
                else:
                    with st.expander(f"{nom_fichier} — Score {score}/20"):
                        st.markdown(evaluation)
                    st.success(f"✅ Analyse terminée pour {nom_fichier}")
                    results.append({'Fichier': nom_fichier, 'Score': score, 'Statut': 'OK', 'Évaluation': evaluation})

            progress_bar.progress((i + 1) / len(uploaded_files))

        # 4️⃣ Résultats
        st.header("4. 📊 Résultats")
        if results:
            df = pd.DataFrame(results).sort_values('Score', ascending=False)
            st.dataframe(df[['Fichier', 'Score', 'Statut']])
            st.bar_chart(df.set_index('Fichier')['Score'])
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("Télécharger les résultats (CSV)", csv, "resultats_cvs.csv", "text/csv")

if __name__ == "__main__":
    main()
