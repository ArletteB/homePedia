import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration MongoDB
MONGO_CONFIG = {
    'host': os.getenv('MONGO_HOST', 'localhost'),
    'port': int(os.getenv('MONGO_PORT', 27017)),
    'database': os.getenv('MONGO_DB', 'real_estate'),
    'user': os.getenv('MONGO_USER', ''),
    'password': os.getenv('MONGO_PASSWORD', '')
}

# Configuration générale du scraping
SCRAPING_CONFIG = {
    'max_pages': int(os.getenv('MAX_PAGES', 100)),
    'page_size': int(os.getenv('PAGE_SIZE', 25)),
    'download_delay': int(os.getenv('DOWNLOAD_DELAY', 2)),
    'concurrent_requests': int(os.getenv('CONCURRENT_REQUESTS', 1))
}
