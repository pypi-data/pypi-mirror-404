import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from .discovery import ModuleDiscoverer

class OmniAuto:
    """
    Punto único de verdad dinámico para todo el proyecto.
    """
    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._categories: Dict[str, Any] = {}
        self._metadata: Dict[str, Dict] = {}
        self.discoverer = ModuleDiscoverer()
        
        # Crear categorías por defecto
        self._categories['ui'] = type('UI', (), {})()
        self._categories['data'] = type('Data', (), {})()
        self._categories['utils'] = type('Utils', (), {})()
        
        # Auto-descubrimiento al inicializar
        self.discover_modules()
        
    def discover_modules(self, module_path: Optional[str] = None):
        """
        Descubre y carga módulos automáticamente.
        """
        try:
            modules = self.discoverer.discover(module_path)
            
            for module_name, module in modules.items():
                self.register_module(module_name, module)
        except Exception as e:
            print(f"  Advertencia en descubrimiento de módulos: {e}")
    
    def register_module(self, name: str, module):
        """
        Registra un módulo en el sistema OmniAuto.
        """
        if name in self._modules:
            return  # Ya registrado
        
        self._modules[name] = module
        
        # Registrar funciones categorizadas del módulo
        for func_name, func in inspect.getmembers(module, callable):
            if hasattr(func, '_omniauto_category'):
                category = func._omniauto_category
                self._register_function_internal(func, category)
        
        # También exponer el módulo directamente bajo su nombre
        setattr(self, name, module)
    
    def _register_function_internal(self, func, category: str = 'general'):
        """Registro interno sin decoradores"""
        # Crear categoría si no existe
        if category not in self._categories:
            self._categories[category] = type(category.capitalize(), (), {})()
        
        # Registrar en la categoría
        setattr(self._categories[category], func.__name__, func)
        
        # Guardar metadata
        key = f"{category}.{func.__name__}"
        self._metadata[key] = {
            'function': func.__name__,
            'doc': func.__doc__,
            'signature': str(inspect.signature(func)),
            'tags': getattr(func, '_omniauto_tags', [])
        }
        
        return func
    
    def register_function(self, func, category: str = 'general', tags: List[str] = None):
        """
        Registra una función individual en una categoría.
        """
        if tags is None:
            tags = []
            
        # Marcar la función con metadata
        func._omniauto_category = category
        func._omniauto_tags = tags
        
        return self._register_function_internal(func, category)
    
    @property
    def ui(self):
        """Acceso a funciones de UI."""
        return self._categories.get('ui', None)
    
    @property
    def data(self):
        """Acceso a funciones de datos."""
        return self._categories.get('data', None)
    
    @property
    def utils(self):
        """Acceso a funciones de utilidad."""
        return self._categories.get('utils', None)
    
    @property
    def metadata(self):
        """Metadatos de todas las funciones registradas."""
        return self._metadata
    
    def get_function(self, category: str, name: str):
        """Obtiene una función por categoría y nombre."""
        category_obj = self._categories.get(category)
        if category_obj:
            return getattr(category_obj, name, None)
        return None
    
    def list_functions(self, category: Optional[str] = None):
        """Lista todas las funciones registradas, opcionalmente filtradas por categoría."""
        if category:
            category_obj = self._categories.get(category)
            if category_obj:
                return [attr for attr in dir(category_obj) if not attr.startswith('_')]
            return []
        
        all_funcs = {}
        for cat_name, cat_obj in self._categories.items():
            all_funcs[cat_name] = [attr for attr in dir(cat_obj) if not attr.startswith('_')]
        
        return all_funcs
    
    def reload_modules(self):
        """Recarga todos los módulos registrados."""
        for module_name, module in self._modules.items():
            importlib.reload(module)
        print("[ok] Módulos recargados correctamente.")

# Instancia global única
auto = OmniAuto()