import streamlit as st
import pandas as pd
import altair as alt
from streamlit_app.utils.db_connection import (
    get_all_department_stats,
    get_all_region_stats,
    get_all_zipcode_stats,
)

st.set_page_config(page_title="Influence des critères", layout="wide")

st.title("Quels critères influencent le plus les prix ?")

level = st.selectbox("Niveau d'analyse", ["Département", "Région", "Code postal"])
logement_type = st.selectbox("Type de logement", ["total", "maison", "appartement"], index=0)

@st.cache_data(show_spinner=False)
def load_data():
    if level == "Département":
        return get_all_department_stats(logement_type)
    if level == "Région":
        return get_all_region_stats(logement_type)
    return get_all_zipcode_stats(logement_type)

df = load_data()

if df.empty:
    st.warning("Aucune donnée disponible pour les paramètres sélectionnés.")
    st.stop()

features = ["nb_annonces", "avg_m2", "avg_rooms"]
cols = features + ["avg_price"]

corr = df[cols].corr()["avg_price"].drop("avg_price").abs().reset_index()
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
