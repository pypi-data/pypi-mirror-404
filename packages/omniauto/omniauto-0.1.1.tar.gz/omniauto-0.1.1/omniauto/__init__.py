"""
Omniauto - Single Point of Truth dinámico para proyectos Python
"""

__version__ = "0.1.0"

# Importaciones diferidas para evitar problemas circulares
def __getattr__(name):
    if name == "auto":
        from .core import auto
        return auto
    elif name == "OmniAuto":
        from .core import OmniAuto
        return OmniAuto
    elif name in ["register", "ui", "data", "utils"]:
        from .decorators import __dict__ as dec_dict
        return dec_dict[name]
    raise AttributeError(f"módulo 'omniauto' no tiene atributo '{name}'")

# Para help() y autocompletado básico
__all__ = ["OmniAuto", "auto", "register", "ui", "data", "utils", "setup_autodiscovery"]