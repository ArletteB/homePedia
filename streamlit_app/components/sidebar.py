import os
import streamlit as st
import datetime

def show_sidebar():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/8205/8205392.png", width=60)
    st.sidebar.title("🧭 Filtres")

    # Filtres de base
    default_city = os.getenv("DEFAULT_CITY", "Paris")
    city = st.sidebar.text_input("🏙️ Ville", default_city)
    property_type = st.sidebar.selectbox("🏡 Type de bien", ["Tous", "Appartement", "Maison", "Studio", "Villa", "Loft"])

    # Plage de prix
    price_range = st.sidebar.slider("💶 Prix (en €)", 50000, 2000000, (100000, 800000), step=50000)

    # Période dynamique sur 1 an
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=365)
    start_date = st.sidebar.date_input("📅 Début", default_start)
    end_date = st.sidebar.date_input("📅 Fin", today)

    if start_date > end_date:
        st.sidebar.error("La date de début doit être antérieure à la date de fin")

    st.sidebar.markdown("---")
    st.sidebar.info("Modifiez les filtres pour mettre à jour les visualisations")

    return {
        "city": city,
        "property_type": property_type,
        "price_min": price_range[0],
        "price_max": price_range[1],
        "start_date": start_date,
        "end_date": end_date
    }
