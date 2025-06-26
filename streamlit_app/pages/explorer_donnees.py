import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_app.utils.db_connection import (
    get_all_zipcode_stats,
    get_all_departments,
    get_all_zipcodes
)

st.set_page_config(page_title="Exploration des données", layout="wide")
st.title("Exploration des données agrégées")

# Sidebar – Filtres principaux
with st.sidebar:
    st.header("Filtres")
    niveau = st.selectbox("Niveau d'analyse", ["Code postal", "Département"])
    logement_type = st.selectbox("Type de logement", ["total", "maison", "appartement"], index=0)

# Chargement des données
if niveau == "Département":
    df = get_all_departments()
else:
    stats = get_all_zipcode_stats(logement_type)
    zip_info = get_all_zipcodes()
    df = stats.merge(zip_info, left_on="zipcode_name", right_on="ZipCode", how="left")

    if not df.empty:
        with st.sidebar:
            prix_min, prix_max = int(df["avg_price"].min()), int(df["avg_price"].max())
            surface_min, surface_max = int(df["avg_m2"].min()), int(df["avg_m2"].max())
            pieces_min, pieces_max = int(df["avg_rooms"].min()), int(df["avg_rooms"].max())
            annonces_min, annonces_max = int(df["nb_annonces"].min()), int(df["nb_annonces"].max())

            prix_range = st.slider("Prix moyen (€)", prix_min, prix_max, (prix_min, prix_max), step=100)
            surface_range = st.slider("Surface moyenne (m²)", surface_min, surface_max, (surface_min, surface_max), step=5)
            pieces_range = st.slider("Nombre moyen de pièces", pieces_min, pieces_max, (pieces_min, pieces_max), step=1)
            annonces_min_sel = st.slider("Nombre minimal d'annonces", annonces_min, annonces_max, 50, step=10)

            departements = df["Department"].dropna().unique()
            selected_depts = st.multiselect("Départements", sorted(departements))

        df = df[
            (df["avg_price"].between(*prix_range)) &
            (df["avg_m2"].between(*surface_range)) &
            (df["avg_rooms"].between(*pieces_range)) &
            (df["nb_annonces"] >= annonces_min_sel)
        ]
        if selected_depts:
            df = df[df["Department"].isin(selected_depts)]

# Affichage des données
st.dataframe(df)

# Carte géographique si applicable
if niveau == "Code postal" and not df.empty and "lat" in df.columns and "lon" in df.columns:
    st.subheader("Carte des prix moyens")
    fig = px.scatter_mapbox(
        df.dropna(subset=["lat", "lon"]),
        lat="lat",
        lon="lon",
        size="avg_price",
        color="avg_price",
        hover_name="zipcode_name",
        hover_data=["Department", "avg_price", "nb_annonces"],
        color_continuous_scale="Viridis",
        size_max=15,
        zoom=4,
        height=600
    )
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)
