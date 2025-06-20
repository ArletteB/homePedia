import streamlit as st
import pandas as pd
import plotly.express as px

# Exemple synthétique
df = pd.DataFrame({
    'date': pd.date_range(start='2020-01-01', periods=12, freq='M'),
    'prix_m2': [3200 + i*100 for i in range(12)],
    'ville': ['Paris']*12
})

fig = px.line(df, x='date', y='prix_m2', title="Évolution des prix à Paris")
st.plotly_chart(fig, use_container_width=True)
