import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import pandas as pd
import streamlit as st
from streamlit_app.config import POSTGRES_CONFIG
from typing import Dict, Any, Tuple, List, Optional
import logging

# Logger configuré pour les erreurs de DB
logger = logging.getLogger(__name__)

# Pool de connexions initialisé une fois
_POOL: Optional[SimpleConnectionPool] = None

def _init_pool() -> None:
    """Initialise le pool de connexions si nécessaire."""
    global _POOL
    if _POOL is None:
        try:
            _POOL = SimpleConnectionPool(
                minconn=1,
                maxconn=int(os.getenv("DB_POOL_SIZE", 5)),
                host=POSTGRES_CONFIG["host"],
                port=POSTGRES_CONFIG["port"],
                database=POSTGRES_CONFIG["database"],
                user=POSTGRES_CONFIG["user"],
                password=POSTGRES_CONFIG["password"],
            )
        except Exception as exc:
            logger.error(f"Échec de l'initialisation du pool de connexions : {exc}")
            raise ConnectionError(f"Database connection failed: {exc}")

def get_connection():
    _init_pool()
    try:
        conn = _POOL.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return conn
    except Exception as exc:
        logger.error(f"Impossible d'obtenir une connexion PostgreSQL : {exc}")
        raise ConnectionError(f"Unable to obtain DB connection: {exc}")

def release_connection(conn):
    if conn and _POOL:
        _POOL.putconn(conn)

def execute_query(query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as exc:
        logger.error(f"Erreur lors de l'exécution de la requête SQL : {exc}")
        raise
    finally:
        release_connection(conn)

def build_query(filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
    query = "SELECT * FROM real_estate WHERE 1=1"
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
def load_data(filters: Dict[str, Any]) -> pd.DataFrame:
    query, params = build_query(filters)
    return execute_query(query, params)

def load_timeseries(city: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
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
    return execute_query(query, params)

# Nouvelles fonctions pour les tables de stats agrégées
def get_department_stats(department_name: str, logement_type: str = "total") -> pd.DataFrame:
    query = """
        SELECT * FROM stats_department
        WHERE department_name = %s AND logement_type = %s
    """
    return execute_query(query, [department_name, logement_type])

def get_region_stats(region_name: str, logement_type: str = "total") -> pd.DataFrame:
    query = """
        SELECT * FROM stats_regions
        WHERE region_name = %s AND logement_type = %s
    """
    return execute_query(query, [region_name, logement_type])

def get_zipcode_stats(zipcode: int, logement_type: str = "total") -> pd.DataFrame:
    query = """
        SELECT * FROM stats_zipcode
        WHERE zipcode_name = %s AND logement_type = %s
    """
    return execute_query(query, [zipcode, logement_type])

# Nouvelles fonctions pour charger les tables de correspondance
@st.cache_data(show_spinner=False)
def get_all_zipcodes() -> pd.DataFrame:
    return execute_query("SELECT * FROM zipcode")

@st.cache_data(show_spinner=False)
def get_all_regions() -> pd.DataFrame:
    return execute_query("SELECT * FROM region")

@st.cache_data(show_spinner=False)
def get_all_departments() -> pd.DataFrame:
    return execute_query("SELECT * FROM department")
