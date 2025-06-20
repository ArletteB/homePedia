import streamlit as st
import pandas as pd
import plotly.express as px

# Titre de la page
st.set_page_config(page_title="Analyse Globale", layout="wide")
st.title("📊 Analyse Globale du Marché Immobilier")

# Données mockées (valeurs simulées)
data = {
    "Ville": ["Paris", "Lyon", "Marseille", "Toulouse", "Nice"],
    "Prix moyen €/m²": [12000, 7500, 5000, 4800, 6200],
    "Variation annuelle (%)": [2.3, 1.8, -0.5, 0.7, 1.1],
    "Volume de ventes": [15200, 8900, 10400, 7700, 6900]
}

df = pd.DataFrame(data)

# Affichage des KPIs
st.subheader("Indicateurs Clés")

col1, col2, col3 = st.columns(3)
col1.metric("Prix moyen France (€/m²)", "6 450", "+1.4%")
col2.metric("Ville la plus chère", df.loc[df["Prix moyen €/m²"].idxmax(), "Ville"])
col3.metric("Ville avec plus grand volume", df.loc[df["Volume de ventes"].idxmax(), "Ville"])

st.markdown("---")

# Affichage d’un tableau résumé
st.subheader("Tableau des Prix Moyens par Ville")
st.dataframe(df, use_container_width=True)

# Graphique comparatif
st.subheader("💹 Comparaison des prix par ville")
fig = px.bar(df, x="Ville", y="Prix moyen €/m²", color="Prix moyen €/m²",
             color_continuous_scale="blues", text="Prix moyen €/m²",
             labels={"Prix moyen €/m²": "Prix en €/m²"},
             title="Prix moyen au m² par ville")

fig.update_traces(texttemplate='%{text:.2s} €', textposition='outside')
fig.update_layout(yaxis_title="Prix en €/m²", xaxis_title="Ville", height=500)

st.plotly_chart(fig, use_container_width=True)
