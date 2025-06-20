import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from streamlit_app.utils.db_connection import build_query

def test_build_query_no_filters():
    query, params = build_query({})
    assert 'WHERE 1=1' in query
    assert 'LIMIT 1000' in query
    assert params == []

def test_build_query_with_filters():
    filters = {
        'city': 'Paris',
        'property_type': 'Appartement',
        'price_min': 100000,
        'price_max': 200000,
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    }
    query, params = build_query(filters)
    assert 'LOWER(location) LIKE' in query
    assert 'LOWER(property_type) = %s' in query
    assert 'price BETWEEN %s AND %s' in query
    assert 'scraped_at BETWEEN %s AND %s' in query
    assert len(params) == 6
