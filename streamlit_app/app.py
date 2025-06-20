import streamlit as st
from components.sidebar import show_sidebar

st.set_page_config(page_title="HomePedia", layout="wide")

# Affichage de la sidebar personnalisée
show_sidebar()

st.title("Bienvenue sur HomePedia 🏡")
st.markdown("Explorez les dynamiques du marché immobilier français à travers des visualisations interactives.")
