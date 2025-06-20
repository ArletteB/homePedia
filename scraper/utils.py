from decimal import Decimal
import re

def convert_to_decimal(value: str, as_decimal: bool = True) -> Decimal:
    """Convertit une chaîne en Decimal ou float selon le besoin
    
    Args:
        value (str): La valeur à convertir
        as_decimal (bool): Si True, retourne un Decimal, sinon un float
        
    Returns:
        Union[Decimal, float]: La valeur convertie
    """
    if not value:
        return None
        
    # Supprime les caractères non numériques sauf le point et la virgule
    clean_value = re.sub(r'[^0-9.,]', '', value)
    
    # Remplace la virgule par un point
    clean_value = clean_value.replace(',', '.')
    
    try:
        if as_decimal:
            return Decimal(clean_value)
        return float(clean_value)
    except (ValueError, decimal.InvalidOperation):
        return None
