import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import pandas as pd
import streamlit as st
from config import POSTGRES_CONFIG

# Pool de connexions initialisé au premier appel
_POOL = None


def _init_pool():
    """Initialise le pool de connexions si nécessaire."""
    global _POOL
    if _POOL is None:
        try:
            _POOL = SimpleConnectionPool(
                1,
                int(os.getenv("DB_POOL_SIZE", 5)),
                host=POSTGRES_CONFIG["host"],
                port=POSTGRES_CONFIG["port"],
                database=POSTGRES_CONFIG["database"],
                user=POSTGRES_CONFIG["user"],
                password=POSTGRES_CONFIG["password"],
            )
        except Exception as exc:
            raise ConnectionError(f"Database connection failed: {exc}")


def get_connection():
    _init_pool()
    try:
        return _POOL.getconn()
    except Exception as exc:
        raise ConnectionError(f"Unable to obtain DB connection: {exc}")


def release_connection(conn):
    if conn is not None and _POOL:
        _POOL.putconn(conn)

# Fonction pour charger les données selon les filtres
def build_query(filters):
    """Construit la requête SQL en fonction des filtres."""
    query = """
        SELECT * FROM real_estate
        WHERE 1=1
    """
    params = []

    if filters.get("city"):
        query += " AND LOWER(location) LIKE %s"
        params.append(f"%{filters['city'].lower()}%")

    if filters.get("property_type") and filters["property_type"] != "Tous":
        query += " AND LOWER(property_type) = %s"
        params.append(filters["property_type"].lower())

    if filters.get("price_min") and filters.get("price_max"):
        query += " AND price BETWEEN %s AND %s"
        params.append(filters["price_min"])
        params.append(filters["price_max"])

    if filters.get("start_date") and filters.get("end_date"):
        query += " AND scraped_at BETWEEN %s AND %s"
        params.append(filters["start_date"])
        params.append(filters["end_date"])

    query += " LIMIT 1000"
    return query, params


@st.cache_data(show_spinner=False)
def load_data(filters):
    query, params = build_query(filters)
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        release_connection(conn)

    return df


def load_timeseries(city, start_date=None, end_date=None):
    """Load average price per m2 by month for a city."""
    query = """
        SELECT DATE_TRUNC('month', "Date") AS month,
               AVG("Price" / NULLIF("M2", 0)) AS price_m2
        FROM real_estate
        WHERE LOWER("City") = LOWER(%s)
    """
    params = [city]

    if start_date and end_date:
        query += " AND \"Date\" BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    query += " GROUP BY month ORDER BY month"

    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        release_connection(conn)

    return df
