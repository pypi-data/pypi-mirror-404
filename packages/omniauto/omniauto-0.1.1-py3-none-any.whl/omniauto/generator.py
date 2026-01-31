import inspect
import json
from pathlib import Path
from typing import Dict, Any
from .core import auto

class StubGenerator:
    """
    Genera archivos de stubs para autocompletado en el IDE.
    """
    
    def generate_python_stub(self, output_path: str = None):
        """
        Genera un archivo .pyi con definiciones para autocompletado.
        
        Args:
            output_path: Ruta donde guardar el archivo. Por defecto es 'auto_stub.pyi'.
        """
        if output_path is None:
            output_path = "auto_stub.pyi"
        
        lines = [
            "# ARCHIVO GENERADO AUTOMÁTICAMENTE POR OMNIAUTO",
            "# NO EDITAR MANUALMENTE",
            "",
            "from typing import Any, Callable",
            "",
            "class _UIStub:",
        ]
        
        # Generar stubs para categoría UI
        ui_funcs = auto.list_functions('ui')
        for func_name in ui_funcs:
            func = auto.get_function('ui', func_name)
            if func:
                sig = inspect.signature(func)
                lines.append(f"    def {func_name}{sig}: ...")
        
        lines.extend([
            "",
            "class _DataStub:",
        ])
        
        # Generar stubs para categoría Data
        data_funcs = auto.list_functions('data')
        for func_name in data_funcs:
            func = auto.get_function('data', func_name)
            if func:
                sig = inspect.signature(func)
                lines.append(f"    def {func_name}{sig}: ...")
        
        lines.extend([
            "",
            "class OmniAutoStub:",
            "    ui: _UIStub",
            "    data: _DataStub",
            "    utils: Any",
        ])
        
        # Agregar módulos descubiertos
        for module_name in auto._modules:
            lines.append(f"    {module_name}: Any")
        
        lines.extend([
            "",
            "auto: OmniAutoStub",
        ])
        
        # Escribir archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"Stub generado en {output_path}")
    
    def generate_ai_context(self, output_path: str = None):
        """
        Genera un archivo JSON con contexto para LLMs como Copilot.
        
        Args:
            output_path: Ruta donde guardar el archivo. 
                        Por defecto es '.copilot/omniauto_context.json'.
        """
        if output_path is None:
            output_path = ".copilot/omniauto_context.json"
        
        # Crear directorio si no existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        context = {
            "project_structure": {
                "entry_point": "from omniauto import auto",
                "available_categories": list(auto._categories.keys())
            },
            "available_functions": {}
        }
        
        for category in auto._categories:
            funcs = auto.list_functions(category)
            for func_name in funcs:
                func = auto.get_function(category, func_name)
                if func:
                    key = f"{category}.{func_name}"
                    context["available_functions"][key] = {
                        "doc": func.__doc__ or "Sin documentación",
                        "signature": str(inspect.signature(func)),
                        "module": getattr(func, '__module__', 'desconocido')
                    }
        
        # Agregar metadata adicional
        context["modules_discovered"] = list(auto._modules.keys())
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
        
        print(f"Contexto para IA generado en {output_path}")

def generate_all_stubs():
    """Función de conveniencia para generar todos los stubs."""
    generator = StubGenerator()
    generator.generate_python_stub()
    generator.generate_ai_context()