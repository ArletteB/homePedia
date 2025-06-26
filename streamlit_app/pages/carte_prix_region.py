import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
from streamlit_app.utils.db_connection import execute_query, get_all_regions

st.set_page_config(page_title="Carte des prix par région", layout="wide")

st.title("Prix moyen au m² par région")
logement_type = st.selectbox("Type de logement", ["total", "maison", "appartement"], index=0)
min_annonces = st.slider("Filtrer sur un nombre minimal d'annonces / région", 0, 100000, 1000, 5000)

@st.cache_data(show_spinner=False)
def load_stats(logement: str, seuil: int) -> pd.DataFrame:
    query = """
        SELECT region_name, avg_price, nb_annonces
        FROM stats_regions
        WHERE logement_type = %s AND nb_annonces >= %s
    """
    return execute_query(query, [logement, seuil])

@st.cache_data(show_spinner=False)
def load_regions_geojson() -> gpd.GeoDataFrame:
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-version-simplifiee.geojson"
    return gpd.read_file(url)

stats = load_stats(logement_type, min_annonces)
geo = load_regions_geojson()

# Uniformiser les noms
geo["nom"] = geo["nom"].str.lower()
stats["region_name"] = stats["region_name"].str.lower()

gdf = geo.merge(stats, left_on="nom", right_on="region_name", how="inner")

if gdf.empty:
    st.warning("Aucune donnée à afficher avec les filtres actuels.")
    st.dataframe(stats)
    st.dataframe(geo[["nom", "geometry"]])
    st.stop()

m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles="cartodbpositron")

choropleth = folium.Choropleth(
    geo_data=gdf.__geo_interface__,
    name="Prix moyen (€) / m²",
    data=gdf,
    columns=["nom", "avg_price"],
    key_on="feature.properties.nom",
    fill_color="YlGnBu",
    fill_opacity=0.7,
    line_opacity=0.3,
    nan_fill_color="#f0f0f0",
    legend_name="Prix moyen (€)",
).add_to(m)

GeoJsonTooltip(
    fields=["nom", "avg_price", "nb_annonces"],
    aliases=["Région :", "Prix moyen € :", "Nombre d'annonces :"],
    localize=True,
    sticky=True,
    labels=True,
    style=("background-color: white; color: #333; font-family: arial; font-size: 12px;"),
).add_to(choropleth.geojson)

folium.LayerControl().add_to(m)

st_folium(m, width=1100, height=600, returned_objects=[])
