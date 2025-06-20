import psycopg2
import pandas as pd
from config import POSTGRES_CONFIG

# Fonction pour établir la connexion PostgreSQL
def get_connection():
    conn = psycopg2.connect(
        host=POSTGRES_CONFIG['host'],
        port=POSTGRES_CONFIG['port'],
        database=POSTGRES_CONFIG['database'],
        user=POSTGRES_CONFIG['user'],
        password=POSTGRES_CONFIG['password']
    )
    return conn

# Fonction pour charger les données selon les filtres
def load_data(filters):
    query = """
        SELECT * FROM real_estate
        WHERE 1=1
    """
    params = []

    if filters['city']:
        query += " AND LOWER(location) LIKE %s"
        params.append(f"%{filters['city'].lower()}%")

    if filters['property_type'] != "Tous":
        query += " AND LOWER(property_type) = %s"
        params.append(filters['property_type'].lower())

    if filters['price_min'] and filters['price_max']:
        query += " AND price BETWEEN %s AND %s"
        params.append(filters['price_min'])
        params.append(filters['price_max'])

    if filters['start_date'] and filters['end_date']:
        query += " AND scraped_at BETWEEN %s AND %s"
        params.append(filters['start_date'])
        params.append(filters['end_date'])

    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    return df
