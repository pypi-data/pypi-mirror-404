import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Dict, Any

class ModuleDiscoverer:
    """
    Descubre módulos automáticamente en carpetas específicas.
    """
    def __init__(self):
        self.modules_path = None
    
    def discover(self, modules_path: str = None) -> Dict[str, Any]:
        """
        Descubre todos los módulos en la ruta especificada.
        
        Args:
            modules_path: Ruta a la carpeta de módulos. 
                         Por defecto busca una carpeta 'modules' en el mismo nivel.
        
        Returns:
            Diccionario con nombre del módulo y el módulo cargado.
        """
        if modules_path is None:
            # Buscar carpeta 'modules' en el directorio actual
            current_dir = Path.cwd()
            modules_dir = current_dir / 'modules'
            
            if not modules_dir.exists():
                # Buscar en el directorio del proyecto
                project_root = self._find_project_root()
                modules_dir = project_root / 'modules'
                
                if not modules_dir.exists():
                    print(f"Advertencia: No se encontró carpeta 'modules' en {current_dir} o {project_root}")
                    return {}
            
            modules_path = str(modules_dir)
        
        self.modules_path = modules_path
        
        # Agregar la ruta al sys.path si no está
        if modules_path not in sys.path:
            sys.path.insert(0, modules_path)
        
        modules = {}
        modules_dir = Path(modules_path)
        
        # Buscar todos los archivos .py en la carpeta
        for py_file in modules_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            module_name = py_file.stem
            try:
                # Importar el módulo
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                modules[module_name] = module
            except Exception as e:
                print(f"Error cargando módulo {module_name}: {e}")
        
        return modules
    
    def _find_project_root(self):
        """Encuentra la raíz del proyecto buscando marcadores como .git, pyproject.toml, etc."""
        current = Path.cwd()
        
        while current != current.parent:
            markers = ['.git', 'pyproject.toml', 'setup.py', 'requirements.txt']
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        
        return Path.cwd()