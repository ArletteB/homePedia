import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="Évolution des prix", layout="wide")
st.title("Évolution des prix dans le temps")


# Message informatif version V2
st.info("""
📊 Cette fonctionnalité sera disponible dans une prochaine version.

Actuellement, les données disponibles ne permettent pas une analyse temporelle des prix.
Nous prévoyons d'intégrer cette fonctionnalité dans une future mise à jour dès que les historiques mensuels seront disponibles.
""")
# Exemple synthétique
df = pd.DataFrame({
    'date': pd.date_range(start='2020-01-01', periods=12, freq='M'),
    'prix_m2': [3200 + i*100 for i in range(12)],
    'ville': ['Bordeaux']*12
})

fig = px.line(df, x='date', y='prix_m2', title="Évolution des prix à Bordeaux")
st.plotly_chart(fig, use_container_width=True)

# Carte interactive globe MapBox
st.markdown("### Carte interactive (globe MapBox)")

mapbox_token = st.secrets["mapbox"]["token"]

if mapbox_token:
    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
        <link href="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.css" rel="stylesheet">
        <script src="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.js"></script>
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; }}
            #map {{ position: absolute; top: 0; bottom: 0; width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
    <div id='map'></div>
    <script>
        mapboxgl.accessToken = '{mapbox_token}';
        const map = new mapboxgl.Map({{
            container: 'map',
            style: 'mapbox://styles/mapbox/streets-v9',
            projection: 'globe',
            zoom: 1,
            center: [2.5, 46.5]
        }});

        map.addControl(new mapboxgl.NavigationControl());
        map.scrollZoom.disable();
        map.on('style.load', () => {{
            map.setFog({{}});
        }});

        const secondsPerRevolution = 240;
        const maxSpinZoom = 5;
        const slowSpinZoom = 3;
        let userInteracting = false;
        const spinEnabled = true;

        function spinGlobe() {{
            const zoom = map.getZoom();
            if (spinEnabled && !userInteracting && zoom < maxSpinZoom) {{
                let distancePerSecond = 360 / secondsPerRevolution;
                if (zoom > slowSpinZoom) {{
                    const zoomDif = (maxSpinZoom - zoom) / (maxSpinZoom - slowSpinZoom);
                    distancePerSecond *= zoomDif;
                }}
                const center = map.getCenter();
                center.lng -= distancePerSecond;
                map.easeTo({{ center, duration: 1000, easing: n => n }});
            }}
        }}

        map.on('mousedown', () => {{ userInteracting = true; }});
        map.on('dragstart', () => {{ userInteracting = true; }});
        map.on('moveend', () => {{ spinGlobe(); }});
        spinGlobe();
    </script>
    </body>
    </html>
    """, height=600)
else:
    st.error("🔐 Le token MapBox est manquant dans `.streamlit/secrets.toml`.")
