import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
from streamlit_app.utils.db_connection import execute_query, get_all_departments

st.set_page_config(page_title="Carte des prix par département", layout="wide")

# ---------------------------- PARAMÈTRES UI ----------------------------
st.title("Prix moyen au m² par département")
logement_type = st.selectbox("Type de logement", ["total", "maison", "appartement"], index=0)
min_annonces = st.slider(
    "Filtrer sur un nombre minimal d'annonces / département",
    min_value=0, max_value=50000, step=5000, value=5000,
)

# ------------------------------ FONCTIONS ------------------------------
@st.cache_data(show_spinner=False)
def load_stats(l_type: str, seuil: int) -> pd.DataFrame:
    query = """
        SELECT department_id, department_name, avg_price, nb_annonces
        FROM stats_department
        WHERE logement_type = %s AND nb_annonces >= %s
    """
    df = execute_query(query, [l_type, seuil])
    df["department_id"] = df["department_id"].astype(str).str.zfill(2)
    df["department_id"] = df["department_id"].replace({"20": "2A", "201": "2A", "202": "2B"})
    return df

@st.cache_data(show_spinner=False)
def load_departments_geojson() -> gpd.GeoDataFrame:
    url = (
        "https://raw.githubusercontent.com/"
        "gregoiredavid/france-geojson/master/"
        "departements-version-simplifiee.geojson"
    )
    gdf = gpd.read_file(url)
    gdf["code"] = gdf["code"].astype(str).str.zfill(2)
    return gdf

@st.cache_data(show_spinner=False)
def load_departments() -> pd.DataFrame:
    df = get_all_departments()
    df["ID"] = df["ID"].astype(str).str.zfill(2)
    return df

# ------------------------------ CHARGEMENT ------------------------------
stats = load_stats(logement_type, min_annonces)
departments = load_departments()
stats = stats.merge(departments, left_on="department_id", right_on="ID", how="left")
stats["department_label"] = stats["department_name"] + " - " + stats["Region"]

geo = load_departments_geojson()

# ------------------------------ MERGE GEO ------------------------------
gdf = geo.merge(stats, left_on="code", right_on="department_id", how="inner")

if gdf.empty:
    st.warning("Aucune donnée à afficher après la fusion GeoJSON + SQL.")
    st.dataframe(stats)
    st.dataframe(geo[["code", "nom"]])
    st.stop()

# Debug : aperçu sans géométrie
st.write("Extrait de la table fusionnée :", gdf.drop(columns=["geometry"]).head())

# --------------------------- CRÉATION FOLIUM ---------------------------
CENTRE_FRANCE = [46.5, 2.5]
m = folium.Map(location=CENTRE_FRANCE, zoom_start=6, tiles="cartodbpositron")

choropleth = folium.Choropleth(
    geo_data=gdf.__geo_interface__,
    name="Prix moyen (€) / m²",
    data=gdf,
    columns=["code", "avg_price"],
    key_on="feature.properties.code",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.3,
    nan_fill_color="#f0f0f0",
    legend_name="Prix moyen (€)",
).add_to(m)

GeoJsonTooltip(
    fields=["department_label", "avg_price", "nb_annonces"],
    aliases=["Département :", "Prix moyen € :", "Nombre d'annonces :"],
    localize=True,
    sticky=True,
    labels=True,
    style=("background-color: white; color: #333; font-family: arial; font-size: 12px;"),
).add_to(choropleth.geojson)

folium.LayerControl().add_to(m)

# ---------------------------- RENDU STREAMLIT --------------------------
st_folium(m, width=1100, height=600, returned_objects=[])
