import importlib
import sys
from pathlib import Path
from typing import Optional

def reload_module(module_name: str):
    """Recarga un módulo específico."""
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        print(f"[OK] Módulo {module_name} recargado.")
    else:
        print(f"[WARN] Módulo {module_name} no encontrado.")

def setup_autodiscovery(modules_dir: str = "modules") -> 'OmniAuto':
    """
    Configura el descubrimiento automático de módulos.
    
    Returns:
        Instancia de OmniAuto configurada.
    """
    from .core import OmniAuto
    
    auto_instance = OmniAuto()
    auto_instance.discover_modules(modules_dir)
    
    return auto_instance

def create_example_project(target_dir: Optional[str] = None):
    """Crea una estructura de ejemplo para probar OmniAuto"""
    if target_dir is None:
        target_dir = Path.cwd() / "omniauto_example"
    
    target_dir = Path(target_dir)
    modules_dir = target_dir / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear ejemplo de módulo (SIN EMOJIS para evitar encoding issues)
    example_module = modules_dir / "example.py"
    example_content = '''"""
Ejemplo de módulo para OmniAuto
"""

from omniauto import ui, data

@ui()
def saludar_usuario(nombre: str) -> str:
    """Saluda a un usuario por su nombre"""
    return f"Hola, {nombre}!"

@data(tags=['procesamiento', 'datos'])
def calcular_promedio(numeros: list) -> float:
    """Calcula el promedio de una lista de números"""
    return sum(numeros) / len(numeros) if numeros else 0

@ui(tags=['ventana'])
def abrir_ventana():
    """Simula abrir una ventana"""
    print("Ventana abierta")
    return True

# Función sin decorador (no será registrada automáticamente)
def funcion_privada():
    """Esta función no será registrada por OmniAuto"""
    return "privada"
'''
    example_module.write_text(example_content, encoding='utf-8')
    
    # Crear script de prueba (SIN EMOJIS)
    test_script = target_dir / "test_omniauto.py"
    test_content = '''"""
Prueba de OmniAuto
"""

from omniauto import auto

print("=== OMNIAUTO TEST ===")
print("Modulos descubiertos:", list(auto._modules.keys()))
print("\\nFunciones disponibles por categoria:")

for categoria, funciones in auto.list_functions().items():
    if funciones:  # Solo mostrar categorías con funciones
        print(f"{categoria.upper()}:")
        for func in funciones:
            print(f"  - {func}")

print("\\n=== USANDO FUNCIONES ===")

# Usar funciones si existen
if hasattr(auto.ui, 'saludar_usuario'):
    resultado = auto.ui.saludar_usuario('Mundo')
    print(f"Saludo: {resultado}")

if hasattr(auto.data, 'calcular_promedio'):
    promedio = auto.data.calcular_promedio([1, 2, 3, 4, 5])
    print(f"Promedio de [1,2,3,4,5]: {promedio}")

if hasattr(auto.ui, 'abrir_ventana'):
    ventana_ok = auto.ui.abrir_ventana()
    print(f"Ventana abierta: {ventana_ok}")

print("\\n=== METADATA ===")
print(f"Funciones registradas: {len(auto.metadata)}")

print("\\n=== FIN TEST ===")
'''
    test_script.write_text(test_content, encoding='utf-8')
    
    # Crear un main.py de ejemplo
    main_script = target_dir / "main.py"
    main_content = '''"""
Ejemplo principal usando OmniAuto
"""

from omniauto import auto
import time

def main():
    print("=== PROYECTO CON OMNIAUTO ===")
    
    # Mostrar lo que se ha descubierto
    print("\\n[1] Modulos cargados:")
    for mod in auto._modules:
        print(f"    - {mod}")
    
    print("\\n[2] Funciones disponibles:")
    for cat, funcs in auto.list_functions().items():
        if funcs:
            print(f"    {cat}: {', '.join(funcs)}")
    
    print("\\n[3] Ejecutando funciones...")
    
    # Ejecutar algunas funciones
    if hasattr(auto.ui, 'saludar_usuario'):
        print(f"    >> {auto.ui.saludar_usuario('Desarrollador')}")
    
    if hasattr(auto.data, 'calcular_promedio'):
        datos = [10, 20, 30, 40, 50]
        print(f"    >> Promedio de {datos}: {auto.data.calcular_promedio(datos)}")
    
    print("\\n[4] Para recargar módulos:")
    print("    >>> auto.reload_modules()")
    
    print("\\n[5] Para usar CLI:")
    print("    $ omniauto list")
    print("    $ omniauto generate")

if __name__ == "__main__":
    main()
'''
    main_script.write_text(main_content, encoding='utf-8')
    
    # Crear README para el ejemplo
    readme_file = target_dir / "README.md"
    readme_content = """# Ejemplo Omniauto

Este es un proyecto de ejemplo para probar OmniAuto.

## Estructura

- `modules/` - Módulos descubiertos automáticamente
- `main.py` - Script principal de ejemplo
- `test_omniauto.py` - Script de prueba

## Uso

```bash
# Ejecutar prueba
python test_omniauto.py

# Ejecutar ejemplo principal
python main.py

# Usar CLI de Omniauto
omniauto list
omniauto generate"""