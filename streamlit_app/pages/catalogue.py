import streamlit as st
import pandas as pd

from components.sidebar import show_sidebar
from utils.db_connection import load_data

st.set_page_config(page_title="Catalogue", layout="wide")

# Affichage des filtres dans la barre latérale
filters = show_sidebar()

st.title("Catalogue des annonces")

# Tentative de chargement des données depuis PostgreSQL
try:
    df = load_data(filters)
    st.success("Connexion PostgreSQL établie")
except Exception as e:
    st.error(f"Erreur lors de la connexion à PostgreSQL : {e}")
    df = pd.DataFrame()

if not df.empty:
    st.dataframe(df.head(100), use_container_width=True)
else:
    st.info("Aucune donnée à afficher.")
