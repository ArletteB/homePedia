import streamlit as st
import pandas as pd
import plotly.express as px

from utils.db_connection import load_timeseries


st.set_page_config(page_title="Tendance des prix", layout="wide")

st.title("📈 Évolution des prix")

city = st.text_input("Ville", "Paris")

start_date = st.date_input("Date de début")
end_date = st.date_input("Date de fin")

if start_date and end_date and start_date > end_date:
    st.error("La date de début doit précéder la date de fin")
    st.stop()

try:
    with st.spinner("Chargement des données ..."):
        df = load_timeseries(city, start_date or None, end_date or None)
    if df.empty:
        st.info("Aucune donnée disponible")
    else:
        fig = px.line(df, x="month", y="price_m2", title=f"Prix moyen au m² à {city}")
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")

