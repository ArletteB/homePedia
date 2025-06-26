import streamlit as st
import pandas as pd
import altair as alt
from streamlit_app.utils.db_connection import (
    get_all_department_stats,
    get_all_region_stats,
    get_all_zipcode_stats
)

st.set_page_config(page_title="Influence des critères", layout="wide")

st.title("Quels critères influencent le plus les prix ?")

level = st.selectbox("Niveau d'analyse", ["Département", "Région", "Code postal"])
logement_type = st.selectbox("Type de logement", ["total", "maison", "appartement"], index=0)

# Chargement des données brutes
def load_data(level, logement_type):
    if level == "Département":
        return get_all_department_stats(logement_type)
    elif level == "Région":
        return get_all_region_stats(logement_type)
    else:
        return get_all_zipcode_stats(logement_type)

df = load_data(level, logement_type)

if df.empty:
    st.warning("Aucune donnée disponible pour les paramètres sélectionnés.")
    st.stop()

# Filtres dynamiques
st.sidebar.header("Filtres avancés")
min_price = st.sidebar.slider("Prix moyen minimum", 0, int(df["avg_price"].max()), 0, 1000)
max_price = st.sidebar.slider("Prix moyen maximum", 0, int(df["avg_price"].max()), int(df["avg_price"].max()), 1000)
min_annonces = st.sidebar.slider("Nombre d'annonces minimum", 0, int(df["nb_annonces"].max()), 0, 10)

# Application des filtres dynamiques
filtered_df = df[(df["avg_price"] >= min_price) & (df["avg_price"] <= max_price) & (df["nb_annonces"] >= min_annonces)]

if filtered_df.empty:
    st.warning("Aucune donnée après filtrage.")
    st.stop()

features = ["nb_annonces", "avg_m2", "avg_rooms"]
cols = features + ["avg_price"]

# Corrélation dynamique
valid_cols = [col for col in cols if col in filtered_df.columns]
if "avg_price" not in valid_cols or len(valid_cols) < 2:
    st.warning("Colonnes insuffisantes pour calculer les corrélations.")
    st.stop()

corr = filtered_df[valid_cols].corr()["avg_price"].drop("avg_price").abs().reset_index()
corr.columns = ["Critère", "Corrélation"]
corr.sort_values("Corrélation", ascending=False, inplace=True)

chart = (
    alt.Chart(corr)
    .mark_bar()
    .encode(
        x=alt.X("Corrélation", title="|Corrélation avec le prix|", scale=alt.Scale(domain=[0, corr["Corrélation"].max() + 0.05])),
        y=alt.Y("Critère", sort="-x"),
        tooltip=["Corrélation"]
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)
