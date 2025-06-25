import streamlit as st
from components.sidebar import show_sidebar
from utils.db_connection import get_connection
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


st.set_page_config(page_title="HomePedia", layout="wide")

# Affichage de la sidebar personnalisée
show_sidebar()

# Tentative de connexion à la base PostgreSQL au démarrage de l'application
try:
    conn = get_connection()
    conn.close()
    st.sidebar.success("Connexion PostgreSQL établie")
except Exception as e:
    st.sidebar.error(f"Connexion PostgreSQL impossible : {e}")

st.title("Bienvenue sur HomePedia 🏡")
st.markdown("Explorez les dynamiques du marché immobilier français à travers des visualisations interactives.")
