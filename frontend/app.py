import streamlit as st
import pandas as pd
import pltly.express as px
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import matplotlib.pyplot as plt
import os

#Là nous sommes sur la configuration
st.set_page_config(page_title="DataMarché - Interne", layout="wide")

st.markdown("""
<style>
body {background-color: #f0f2f6;}
h1 {color: #0A3D62; text-align:center;}
.stButton>button {background-color:#0A3D62;color:white;border-radius:8px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 DataMarché – Analyse interne des marchés")
st.markdown("**Importez vos données, analysez, comparez et exportez**")

st.info(
    "ℹ️ Les analyses se recalculent automatiquement à chaque import de fichier Excel. "
    "Plus besoin de refaire le reporting manuellement."
)

#Pour parvenir à faire un import de csv depuis votre pc
st.header("📥 Import des données")

col1, col2 = st.columns(2)
with col1:
    fichier_actuel = st.file_uploader("📄 Dataset semaine actuelle", type=["csv", "xlsx"])
with col2:
    fichier_prec = st.file_uploader("📄 Dataset semaine précédente", type=["csv", "xlsx"])

def load_file(f):
    if f.name.endswith(".csv"):
        return pd.read_csv(f)
    return pd.read_excel(f)

if fichier_actuel:
    df = load_file(fichier_actuel)

    # Là nous nettoyons les données du dataset(fichier  que allez importer)
    #du coup plus besoin de les nettoyer de puis excel
    df = df.dropna(how="all")
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = pd.to_numeric(df[c], errors="ignore")

    st.subheader("Aperçu des données")
    st.dataframe(df.head(), use_container_width=True)

    # ce bloc est pour le mapping donc vous aurez possibilité de choisir les données 
    #que vous voulez croiser pour pour la visualisation 
    st.header(" Paramétrage de l’analyse")

    colonnes = df.columns.tolist()
    col_cat = st.selectbox("Colonne marché / catégorie", colonnes)
    col_val = st.selectbox("Colonne valeur (chiffres)", colonnes)
    col_statut = st.selectbox("Colonne statut (Actif/Inactif)", [None] + colonnes)

    df_plot = df.copy()

    if col_statut:
        statuts = df[col_statut].astype(str).unique().tolist()
        statut_sel = st.multiselect("Filtrer par statut", statuts, default=statuts)
        df_plot = df[df[col_statut].astype(str).isin(statut_sel)]

    # Les types de graphes disponible (Possibilités de rajouter des histogrammes de fréquences bref des diagrammes de votre choix)
    st.header(" Visualisation")

    chart_type = st.radio("Type de graphique", ["Barre", "Ligne", "Camembert"], horizontal=True)

    if chart_type == "Barre":
        fig = px.bar(df_plot, x=col_cat, y=col_val)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Ligne":
        fig = px.line(df_plot, x=col_cat, y=col_val)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Camembert":
        if not pd.api.types.is_numeric_dtype(df_plot[col_val]):
            st.error("Le camembert nécessite une colonne numérique.")
        else:
            df_pie = df_plot.groupby(col_cat)[col_val].sum().reset_index()
            fig = px.pie(df_pie, names=col_cat, values=col_val, hole=0.4)
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

    # Je définis mes KPI() ou du moins les metriques
    st.header(" Indicateurs clés")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nombre de lignes", len(df_plot))

    if pd.api.types.is_numeric_dtype(df_plot[col_val]):
        c2.metric("Total", f"{df_plot[col_val].sum():,.0f}")
        c3.metric("Moyenne", f"{df_plot[col_val].mean():,.2f}")
        c4.metric("Marchés uniques", df_plot[col_cat].nunique())

    # Alors ce bloc est OPTIONNEL il permet tout simplement 
    #De faire la comparaison entre cette semaine et la précédante
    if fichier_prec:
        df_prev = load_file(fichier_prec).dropna(how="all")

        if col_val in df_prev.columns:
            total_actuel = df_plot[col_val].sum()
            total_prec = df_prev[col_val].sum()
            diff = total_actuel - total_prec
            pct = (diff / total_prec) * 100 if total_prec != 0 else 0

            st.header("🧾 Comparaison avec la semaine précédente")
            st.metric("Évolution", f"{total_actuel:,.0f}", f"{pct:+.2f} %")

    #Le Scoring
    st.header(" Scoring automatique des marchés")

    df_score = df_plot.groupby(col_cat)[col_val].sum().reset_index()
    max_val = df_score[col_val].max()
    df_score["Score"] = (df_score[col_val] / max_val * 100).round(1)

    def label_score(s):
        if s >= 70:
            return " Fort"
        elif s >= 40:
            return " Moyen"
        return " Faible"

    df_score["Niveau"] = df_score["Score"].apply(label_score)

    st.dataframe(df_score, use_container_width=True)

    fig_score = px.bar(df_score, x=col_cat, y="Score", color="Niveau", text="Score")
    fig_score.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig_score, use_container_width=True)

    # Quelque recommandation ou simmulation de recommandation par défaut
    st.header(" Recommandations automatiques")

    if (df_score["Score"] >= 70).any():
        st.info(" Renforcer l’investissement sur les marchés performants.")
    if ((df_score["Score"] >= 40) & (df_score["Score"] < 70)).any():
        st.info(" Optimiser les marchés intermédiaires.")
    if (df_score["Score"] < 40).any():
        st.info(" Réévaluer les marchés à faible performance.")

    #   Pour télécharger en excel le tout 
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df_plot.to_excel(w, index=False)

    st.download_button(
        " Télécharger Excel",
        out.getvalue(),
        file_name="Analyse_DataMarche.xlsx"
    )

    # OU LE PDF
    def gen_pdf(df_plot):
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("<b>DataMarché – Rapport interne</b>", styles["Title"]))
        elements.append(Spacer(1, 12))

        plt.figure(figsize=(6, 3))
        df_plot.groupby(col_cat)[col_val].sum().plot(kind="bar")
        plt.tight_layout()
        img_path = "chart.png"
        plt.savefig(img_path)
        plt.close()

        elements.append(Image(img_path, width=400, height=200))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Signature : Aicha Diop", styles["Italic"]))
        elements.append(Paragraph("Usage interne – Confidentiel", styles["Italic"]))

        doc.build(elements)
        buf.seek(0)

        os.remove(img_path)
        return buf

    pdf = gen_pdf(df_plot)
    st.download_button(
        " Télécharger PDF",
        pdf,
        file_name="Rapport_DataMarche.pdf"
    )
  #   Voili voilou....
