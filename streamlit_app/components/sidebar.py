import streamlit as st
import datetime

def show_sidebar():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/8205/8205392.png", width=60)
    st.sidebar.title("🧭 Filtres")

    # Filtres de base
    city = st.sidebar.text_input("🏙️ Ville", "Paris")
    property_type = st.sidebar.selectbox("🏡 Type de bien", ["Tous", "Appartement", "Maison", "Studio", "Villa", "Loft"])

    # Plage de prix
    price_range = st.sidebar.slider("💶 Prix (en €)", 50000, 2000000, (100000, 800000), step=50000)

    # Période
    start_date = st.sidebar.date_input("📅 Début", datetime.date(2024, 1, 1))
    end_date = st.sidebar.date_input("📅 Fin", datetime.date.today())

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
