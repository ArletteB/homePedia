import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from streamlit_app.utils.db_connection import execute_query

st.set_page_config(page_title="Carte des prix par code postal", layout="wide")

# -- UI --
st.title("Prix moyen au m² par code postal")
logement_type = st.selectbox("Type de logement", ["total", "maison", "appartement"], index=0)
min_annonces = st.slider("Filtrer par nombre minimal d'annonces", 0, 10000, 100, step=100)

# -- Chargement des données --
@st.cache_data(show_spinner=False)
def load_data():
    query = """
        SELECT z.zipcode_name,
               z.avg_price,
               z.nb_annonces,
               d."Department",
               d."GroupCitys"
        FROM stats_zipcode z
        LEFT JOIN zipcode d
          ON z.zipcode_name = d."ZipCode"
        WHERE z.logement_type = %s
          AND z.nb_annonces >= %s
    """
    return execute_query(query, [logement_type, min_annonces])

zip_stats = load_data()

if zip_stats.empty:
    st.warning("Aucune donnée à afficher avec les filtres actuels.")
    st.stop()

# -- Carte --
m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles="cartodbpositron")
marker_cluster = MarkerCluster().add_to(m)

# Utilisation simple : décalage aléatoire pour éviter chevauchement si pas de coordonnées
import random
for _, row in zip_stats.iterrows():
    lat = 46.5 + (random.random() - 0.5) * 0.5
    lon = 2.5 + (random.random() - 0.5) * 1.0
    popup = (
        f"<b>Code postal :</b> {row['zipcode_name']}<br>"
        f"<b>Département :</b> {row.get('Department','–')}<br>"
        f"<b>Villes :</b> {row.get('GroupCitys','–')}<br>"
        f"<b>Prix moyen :</b> {int(row['avg_price']):,} €<br>"
        f"<b>Annonces :</b> {int(row['nb_annonces'])}"
    )
    folium.Marker(location=[lat, lon], popup=popup, icon=folium.Icon(color="blue", icon="home")).add_to(marker_cluster)

st_folium(m, width=1100, height=600, returned_objects=[])