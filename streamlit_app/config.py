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

# Configuration optionnelle MongoDB si nécessaire (future évolution)
MONGO_CONFIG = {
    "host": os.getenv("MONGO_HOST"),
    "port": int(os.getenv("MONGO_PORT", 27017)),
    "database": os.getenv("MONGO_DB"),
    "user": os.getenv("MONGO_USER"),
    "password": os.getenv("MONGO_PASSWORD"),
}
# config.py
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
# Path to local data used by Streamlit pages
# Defaults to the `data` directory located inside the `streamlit_app` package
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
DATA_PATH = os.getenv("DATA_PATH", DEFAULT_DATA_PATH)

REQUIRED_VARS = ["host", "database", "user", "password"]
missing = [v for v in REQUIRED_VARS if not POSTGRES_CONFIG.get(v)]
if missing:
    missing_str = ", ".join(missing)
    raise ValueError(f"Missing PostgreSQL configuration variables: {missing_str}")

if not MAPBOX_TOKEN:
    raise ValueError("MAPBOX_TOKEN environment variable is not set")
