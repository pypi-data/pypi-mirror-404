from functools import wraps
from typing import List, Optional

def register(category: str = 'general', tags: Optional[List[str]] = None):
    """
    Decorador para marcar funciones para registro en OmniAuto.
    """
    if tags is None:
        tags = []
    
    def decorator(func):
        # Marcar la función con metadatos
        func._omniauto_category = category
        func._omniauto_tags = tags
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Transferir los atributos al wrapper
        wrapper._omniauto_category = category
        wrapper._omniauto_tags = tags
        return wrapper
    
    return decorator

# Alias para categorías comunes
def ui(tags: Optional[List[str]] = None):
    """Decorador para funciones de UI."""
    return register('ui', tags)

def data(tags: Optional[List[str]] = None):
    """Decorador para funciones de datos."""
    return register('data', tags)

def utils(tags: Optional[List[str]] = None):
    """Decorador para funciones de utilidad."""
    return register('utils', tags)