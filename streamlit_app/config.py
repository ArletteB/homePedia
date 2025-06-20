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
MAPBOX_TOKEN = "your-mapbox-token"
DATA_PATH = "data/"
