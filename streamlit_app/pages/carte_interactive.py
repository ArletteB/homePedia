import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
from config import DATA_PATH

st.set_page_config(page_title="Carte Interactive", layout="wide")

st.title("🗺️ Carte Interactive du Marché Immobilier")

# Chargement des données géographiques (GeoJSON ou shapefile converti)
@st.cache_data
def load_data():
    gdf = gpd.read_file(f"{DATA_PATH}/departements.geojson")
    df_indicateurs = pd.read_csv(f"{DATA_PATH}/indicateurs_immobilier.csv")
    return gdf, df_indicateurs

gdf, df_indicateurs = load_data()

# Fusion géo + données
gdf = gdf.merge(df_indicateurs, on="code_departement")

# Choix de l’indicateur à afficher
indicateur = st.selectbox("Choisir un indicateur à visualiser", gdf.columns[5:])

# Centrage automatique
centre = gdf.geometry.centroid.unary_union.centroid.coords[0]

# Création de la carte Folium
m = folium.Map(location=[centre[1], centre[0]], zoom_start=6, tiles="cartodbpositron")

# Ajout d’une couche choroplèthe
folium.Choropleth(
    geo_data=gdf,
    name="choropleth",
    data=gdf,
    columns=["code_departement", indicateur],
    key_on="feature.properties.code_departement",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=indicateur,
).add_to(m)

# Ajout des info-bulles
folium.GeoJsonTooltip(
    fields=["nom_departement", indicateur],
    aliases=["Département", indicateur],
).add_to(folium.GeoJson(gdf).add_to(m))

# Affichage dans Streamlit
st_folium(m, width=1200)

