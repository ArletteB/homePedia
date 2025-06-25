import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration de la base de données PostgreSQL
POSTGRES_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# config.py
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY")
# Path to local data used by Streamlit pages
# Defaults to the `data` directory located inside the `streamlit_app` package
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
DATA_PATH = os.getenv("DATA_PATH", DEFAULT_DATA_PATH)

REQUIRED_VARS = ["host", "database", "user", "password"]
missing = [v for v in REQUIRED_VARS if not POSTGRES_CONFIG.get(v)]
if missing:
    missing_str = ", ".join(missing)
    raise ValueError(f"Missing PostgreSQL configuration variables: {missing_str}")

if not MAPBOX_API_KEY:
    raise ValueError("MAPBOX_API_KEY environment variable is not set")

