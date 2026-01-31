import importlib
import sys
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

def reload_module(module_name: str):
    """Recarga un módulo específico."""
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        print(f"[INFO] Módulo {module_name} recargado.")
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

def create_example_project(target_dir: Optional[str] = None) -> Path:
    """
    Crea una estructura de ejemplo completa para probar Omniauto.
    
    Returns:
        Ruta al directorio creado.
    """
    if target_dir is None:
        target_dir = Path.cwd() / "omniauto_example"
    
    target_dir = Path(target_dir)
    
    # Limpiar si ya existe
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    # Crear estructura completa
    modules_dir = target_dir / "modules"
    tests_dir = target_dir / "tests"
    docs_dir = target_dir / "docs"
    config_dir = target_dir / "config"
    
    modules_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)
    config_dir.mkdir(exist_ok=True)
    
    # ======================
    # MÓDULO 1: auth.py
    # ======================
    auth_module = modules_dir / "auth.py"
    auth_content = '''"""
Módulo de autenticación y gestión de usuarios.
"""

from omniauto import ui, data, utils
from typing import Optional, Dict, List

@ui(tags=['login', 'security', 'users'])
def login(username: str, password: str) -> Dict[str, Any]:
    """
    Autentica un usuario en el sistema.
    
    Args:
        username: Nombre de usuario
        password: Contraseña
        
    Returns:
        Diccionario con resultado de autenticación
    """
    # Simulación de autenticación
    if username == "admin" and password == "admin123":
        return {
            "success": True,
            "user_id": 1,
            "username": username,
            "role": "admin",
            "token": "fake-jwt-token-12345"
        }
    else:
        return {
            "success": False,
            "error": "Credenciales inválidas"
        }

@ui(tags=['logout', 'session'])
def logout(user_id: int) -> bool:
    """
    Cierra la sesión de un usuario.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        True si se cerró la sesión correctamente
    """
    print(f"[AUTH] Sesión cerrada para usuario {user_id}")
    return True

@data(tags=['users', 'database', 'crud'])
def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene el perfil de un usuario.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Diccionario con información del usuario o None si no existe
    """
    users = {
        1: {"id": 1, "name": "Admin", "email": "admin@example.com", "role": "admin"},
        2: {"id": 2, "name": "User", "email": "user@example.com", "role": "user"}
    }
    return users.get(user_id)

@utils(tags=['validation', 'security'])
def validate_password(password: str) -> List[str]:
    """
    Valida que una contraseña cumpla con los requisitos.
    
    Args:
        password: Contraseña a validar
        
    Returns:
        Lista de errores de validación (vacía si es válida)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not any(c.isdigit() for c in password):
        errors.append("La contraseña debe contener al menos un número")
    
    if not any(c.isupper() for c in password):
        errors.append("La contraseña debe contener al menos una mayúscula")
    
    return errors

# Función sin decorador (no será registrada automáticamente)
def _hash_password(password: str) -> str:
    """
    Función interna para hashear contraseñas.
    No está decorada, por lo que no será registrada por Omniauto.
    """
    # En un caso real, usaríamos hashlib
    return f"hashed_{password}"
'''
    auth_module.write_text(auth_content, encoding='utf-8')
    
    # ======================
    # MÓDULO 2: ventanas.py
    # ======================
    ventanas_module = modules_dir / "ventanas.py"
    ventanas_content = '''"""
Módulo de interfaces de usuario y ventanas.
"""

from omniauto import ui
from typing import List, Optional
import datetime

@ui(tags=['dashboard', 'main'])
def show_dashboard(user_role: str) -> Dict[str, Any]:
    """
    Muestra el dashboard principal según el rol del usuario.
    
    Args:
        user_role: Rol del usuario (admin, user, guest)
        
    Returns:
        Configuración del dashboard
    """
    widgets = []
    
    if user_role == "admin":
        widgets = [
            {"type": "stats", "title": "Usuarios activos", "value": 42},
            {"type": "stats", "title": "Ingresos mensuales", "value": "$15,230"},
            {"type": "chart", "title": "Actividad reciente"},
            {"type": "table", "title": "Últimos registros"}
        ]
    else:
        widgets = [
            {"type": "stats", "title": "Tareas pendientes", "value": 5},
            {"type": "chart", "title": "Mi progreso"},
            {"type": "calendar", "title": "Agenda"}
        ]
    
    return {
        "title": f"Dashboard - {user_role}",
        "widgets": widgets,
        "timestamp": datetime.datetime.now().isoformat()
    }

@ui(tags=['forms', 'input'])
def show_form(form_type: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Muestra un formulario específico.
    
    Args:
        form_type: Tipo de formulario (login, register, settings, etc.)
        data: Datos iniciales para el formulario
        
    Returns:
        Configuración del formulario
    """
    forms = {
        "login": {
            "fields": [
                {"name": "username", "type": "text", "label": "Usuario", "required": True},
                {"name": "password", "type": "password", "label": "Contraseña", "required": True},
                {"name": "remember", "type": "checkbox", "label": "Recordarme"}
            ],
            "submit_text": "Iniciar Sesión"
        },
        "register": {
            "fields": [
                {"name": "name", "type": "text", "label": "Nombre completo"},
                {"name": "email", "type": "email", "label": "Correo electrónico"},
                {"name": "password", "type": "password", "label": "Contraseña"},
                {"name": "confirm_password", "type": "password", "label": "Confirmar contraseña"}
            ],
            "submit_text": "Registrarse"
        },
        "settings": {
            "fields": [
                {"name": "theme", "type": "select", "label": "Tema", 
                 "options": ["claro", "oscuro", "auto"]},
                {"name": "language", "type": "select", "label": "Idioma",
                 "options": ["es", "en", "fr", "de"]},
                {"name": "notifications", "type": "checkbox", "label": "Notificaciones"}
            ],
            "submit_text": "Guardar"
        }
    }
    
    form_config = forms.get(form_type, {"fields": [], "submit_text": "Enviar"})
    
    if data:
        form_config["initial_data"] = data
    
    return form_config

@ui(tags=['navigation', 'menu'])
def build_navigation_menu(user_permissions: List[str]) -> List[Dict[str, Any]]:
    """
    Construye el menú de navegación según los permisos del usuario.
    
    Args:
        user_permissions: Lista de permisos del usuario
        
    Returns:
        Lista de elementos del menú
    """
    base_menu = [
        {"id": "home", "label": "Inicio", "icon": "home", "route": "/"},
        {"id": "dashboard", "label": "Dashboard", "icon": "dashboard", "route": "/dashboard"},
        {"id": "profile", "label": "Perfil", "icon": "user", "route": "/profile"}
    ]
    
    # Añadir items según permisos
    if "view_reports" in user_permissions:
        base_menu.append({"id": "reports", "label": "Reportes", "icon": "chart", "route": "/reports"})
    
    if "manage_users" in user_permissions:
        base_menu.append({"id": "users", "label": "Usuarios", "icon": "users", "route": "/users"})
    
    if "admin" in user_permissions:
        base_menu.append({"id": "admin", "label": "Administración", "icon": "settings", "route": "/admin"})
    
    return base_menu
'''
    ventanas_module.write_text(ventanas_content, encoding='utf-8')
    
    # ======================
    # MÓDULO 3: datos.py
    # ======================
    datos_module = modules_dir / "datos.py"
    datos_content = '''"""
Módulo de procesamiento y análisis de datos.
"""

from omniauto import data, utils
from typing import List, Dict, Any, Optional
import statistics
import csv
import json

@data(tags=['analysis', 'statistics'])
def analyze_dataset(data: List[float]) -> Dict[str, Any]:
    """
    Analiza un conjunto de datos numéricos.
    
    Args:
        data: Lista de valores numéricos
        
    Returns:
        Estadísticas del dataset
    """
    if not data:
        return {"error": "Dataset vacío"}
    
    return {
        "count": len(data),
        "mean": statistics.mean(data),
        "median": statistics.median(data),
        "stdev": statistics.stdev(data) if len(data) > 1 else 0,
        "min": min(data),
        "max": max(data),
        "sum": sum(data)
    }

@data(tags=['import', 'csv', 'files'])
def import_csv_file(filepath: str, delimiter: str = ',') -> List[Dict[str, Any]]:
    """
    Importa datos desde un archivo CSV.
    
    Args:
        filepath: Ruta al archivo CSV
        delimiter: Delimitador de campos
        
    Returns:
        Lista de diccionarios con los datos
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=delimiter)
            return list(reader)
    except Exception as e:
        print(f"[ERROR] Error al importar CSV: {e}")
        return []

@data(tags=['export', 'json', 'files'])
def export_to_json(data: Any, filepath: str, indent: int = 2) -> bool:
    """
    Exporta datos a un archivo JSON.
    
    Args:
        data: Datos a exportar
        filepath: Ruta de destino
        indent: Indentación del JSON
        
    Returns:
        True si se exportó correctamente
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Error al exportar JSON: {e}")
        return False

@utils(tags=['transform', 'data'])
def transform_data(data: List[Dict], mapping: Dict[str, str]) -> List[Dict]:
    """
    Transforma datos renombrando columnas.
    
    Args:
        data: Lista de diccionarios con datos
        mapping: Mapeo de nombres antiguos a nuevos
        
    Returns:
        Datos transformados
    """
    transformed = []
    
    for item in data:
        new_item = {}
        for old_key, new_key in mapping.items():
            if old_key in item:
                new_item[new_key] = item[old_key]
            else:
                new_item[new_key] = None
        transformed.append(new_item)
    
    return transformed

@data(tags=['filter', 'query'])
def filter_data(data: List[Dict], conditions: Dict[str, Any]) -> List[Dict]:
    """
    Filtra datos según condiciones.
    
    Args:
        data: Lista de diccionarios con datos
        conditions: Condiciones de filtrado
        
    Returns:
        Datos filtrados
    """
    filtered = []
    
    for item in data:
        match = True
        for key, value in conditions.items():
            if key not in item or item[key] != value:
                match = False
                break
        
        if match:
            filtered.append(item)
    
    return filtered
'''
    datos_module.write_text(datos_content, encoding='utf-8')
    
    # ======================
    # MÓDULO 4: api.py
    # ======================
    api_module = modules_dir / "api.py"
    api_content = '''"""
Módulo de integración con APIs externas.
"""

from omniauto import data, utils
import requests
from typing import Dict, Any, Optional
import time

@data(tags=['http', 'rest', 'external'])
def fetch_from_api(url: str, method: str = 'GET', 
                   params: Optional[Dict] = None,
                   headers: Optional[Dict] = None,
                   timeout: int = 30) -> Dict[str, Any]:
    """
    Realiza una petición HTTP a una API externa.
    
    Args:
        url: URL de la API
        method: Método HTTP (GET, POST, PUT, DELETE)
        params: Parámetros de la petición
        headers: Encabezados HTTP
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        Respuesta de la API
    """
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params if method == 'GET' else None,
            json=params if method != 'GET' else None,
            headers=headers,
            timeout=timeout
        )
        
        response.raise_for_status()
        
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json() if response.content else None,
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }

@data(tags=['cache', 'performance'])
def cached_api_call(url: str, cache_duration: int = 300) -> Dict[str, Any]:
    """
    Realiza una llamada a API con cache básico.
    
    Args:
        url: URL de la API
        cache_duration: Duración de la cache en segundos
        
    Returns:
        Datos de la API (pueden ser cacheados)
    """
    # Simulación simple de cache
    cache_key = f"api_cache_{hash(url)}"
    
    # En una implementación real usaríamos redis, memcached, etc.
    # Por simplicidad, siempre llamamos a la API
    return fetch_from_api(url)

@utils(tags=['validation', 'api'])
def validate_api_response(response: Dict[str, Any], 
                         expected_keys: List[str] = None) -> List[str]:
    """
    Valida una respuesta de API.
    
    Args:
        response: Respuesta de la API
        expected_keys: Claves que se esperan en la respuesta
        
    Returns:
        Lista de errores de validación
    """
    errors = []
    
    if not response.get("success", False):
        errors.append("La petición a la API no fue exitosa")
    
    if expected_keys:
        data = response.get("data", {})
        if isinstance(data, dict):
            for key in expected_keys:
                if key not in data:
                    errors.append(f"Falta la clave esperada: {key}")
    
    return errors

@data(tags=['batch', 'processing'])
def batch_api_calls(urls: List[str], 
                   max_concurrent: int = 3) -> List[Dict[str, Any]]:
    """
    Realiza múltiples llamadas a API de forma eficiente.
    
    Args:
        urls: Lista de URLs a llamar
        max_concurrent: Número máximo de llamadas concurrentes
        
    Returns:
        Lista de respuestas
    """
    results = []
    
    # Simulación de procesamiento por lotes
    for i in range(0, len(urls), max_concurrent):
        batch = urls[i:i + max_concurrent]
        print(f"[API] Procesando lote {i//max_concurrent + 1} con {len(batch)} URLs")
        
        for url in batch:
            result = fetch_from_api(url)
            results.append(result)
    
    return results
'''
    api_module.write_text(api_content, encoding='utf-8')
    
    # ======================
    # ARCHIVO PRINCIPAL
    # ======================
    main_script = target_dir / "main.py"
    main_content = '''"""
Sistema de ejemplo completo con Omniauto.
"""

from omniauto import auto
import json
from typing import Dict, Any

def print_header(title: str):
    """Imprime un encabezado formateado."""
    print("\\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def demo_authentication():
    """Demo del módulo de autenticación."""
    print_header("DEMO: SISTEMA DE AUTENTICACIÓN")
    
    # 1. Login
    print("1. Inicio de sesión:")
    login_result = auto.ui.login("admin", "admin123")
    print(f"   Resultado: {login_result['success']}")
    print(f"   Usuario: {login_result.get('username', 'N/A')}")
    print(f"   Token: {login_result.get('token', 'N/A')[:20]}...")
    
    if login_result["success"]:
        user_id = login_result["user_id"]
        
        # 2. Perfil de usuario
        print("\\n2. Perfil de usuario:")
        profile = auto.data.get_user_profile(user_id)
        if profile:
            print(f"   Nombre: {profile['name']}")
            print(f"   Email: {profile['email']}")
            print(f"   Rol: {profile['role']}")
        
        # 3. Validación de contraseña
        print("\\n3. Validación de contraseña:")
        password_errors = auto.utils.validate_password("weak")
        if password_errors:
            print("   Errores encontrados:")
            for error in password_errors:
                print(f"   - {error}")
        
        # 4. Logout
        print("\\n4. Cierre de sesión:")
        logout_ok = auto.ui.logout(user_id)
        print(f"   Resultado: {logout_ok}")

def demo_user_interface():
    """Demo del módulo de interfaces."""
    print_header("DEMO: INTERFACES DE USUARIO")
    
    # 1. Dashboard
    print("1. Dashboard para diferentes roles:")
    for role in ["admin", "user", "guest"]:
        dashboard = auto.ui.show_dashboard(role)
        print(f"   {role.upper()}: {dashboard['title']}")
        print(f"     Widgets: {len(dashboard['widgets'])}")
    
    # 2. Formularios
    print("\\n2. Formularios disponibles:")
    form_types = ["login", "register", "settings"]
    for form_type in form_types:
        form_config = auto.ui.show_form(form_type)
        print(f"   {form_type.upper()}: {len(form_config['fields'])} campos")
    
    # 3. Menú de navegación
    print("\\n3. Menús según permisos:")
    permissions_sets = [
        ["view_reports"],
        ["manage_users"],
        ["admin", "view_reports", "manage_users"]
    ]
    
    for perms in permissions_sets:
        menu = auto.ui.build_navigation_menu(perms)
        print(f"   Permisos {perms}: {len(menu)} items en menú")

def demo_data_processing():
    """Demo del módulo de procesamiento de datos."""
    print_header("DEMO: PROCESAMIENTO DE DATOS")
    
    # 1. Análisis estadístico
    print("1. Análisis de dataset:")
    data = [23, 45, 67, 89, 12, 34, 56, 78, 90, 21]
    analysis = auto.data.analyze_dataset(data)
    
    print(f"   Datos: {data}")
    print(f"   Media: {analysis['mean']:.2f}")
    print(f"   Mediana: {analysis['median']}")
    print(f"   Desviación estándar: {analysis['stdev']:.2f}")
    
    # 2. Transformación de datos
    print("\\n2. Transformación de datos:")
    sample_data = [
        {"id": 1, "nombre": "Juan", "edad": 30},
        {"id": 2, "nombre": "María", "edad": 25}
    ]
    mapping = {"id": "identificador", "nombre": "name", "edad": "age"}
    transformed = auto.utils.transform_data(sample_data, mapping)
    
    print(f"   Datos originales: {sample_data}")
    print(f"   Datos transformados: {transformed}")
    
    # 3. Filtrado de datos
    print("\\n3. Filtrado de datos:")
    filtered = auto.data.filter_data(sample_data, {"edad": 30})
    print(f"   Datos filtrados (edad=30): {filtered}")

def demo_api_integration():
    """Demo del módulo de integración con APIs."""
    print_header("DEMO: INTEGRACIÓN CON APIS")
    
    # 1. Llamada a API pública de prueba
    print("1. Llamada a API pública:")
    api_result = auto.data.fetch_from_api("https://jsonplaceholder.typicode.com/posts/1")
    
    if api_result["success"]:
        print(f"   Status: {api_result['status_code']}")
        print(f"   Datos: {json.dumps(api_result['data'], indent=2)}")
    else:
        print(f"   Error: {api_result.get('error', 'Desconocido')}")
    
    # 2. Validación de respuesta
    print("\\n2. Validación de respuesta de API:")
    validation_errors = auto.utils.validate_api_response(
        api_result, 
        expected_keys=["userId", "id", "title", "body"]
    )
    
    if validation_errors:
        print("   Errores encontrados:")
        for error in validation_errors:
            print(f"   - {error}")
    else:
        print("   ✅ Respuesta válida")

def demo_omniauto_features():
    """Demo de características específicas de Omniauto."""
    print_header("DEMO: CARACTERÍSTICAS DE OMNIAUTO")
    
    # 1. Listar todas las funciones
    print("1. Funciones registradas por categoría:")
    all_functions = auto.list_functions()
    
    for category, functions in all_functions.items():
        if functions:
            print(f"   {category.upper()}: {len(functions)} funciones")
            # Mostrar primeras 3 funciones de cada categoría
            for func in functions[:3]:
                print(f"     - {func}")
            if len(functions) > 3:
                print(f"     ... y {len(functions) - 3} más")
    
    # 2. Metadata de funciones
    print("\\n2. Metadata de funciones (ejemplo):")
    if auto.metadata:
        first_key = list(auto.metadata.keys())[0]
        metadata = auto.metadata[first_key]
        print(f"   Función: {first_key}")
        print(f"   Documentación: {metadata['doc'][:50]}...")
        print(f"   Tags: {', '.join(metadata['tags'])}")
    
    # 3. Estadísticas generales
    print("\\n3. Estadísticas del sistema:")
    print(f"   Módulos cargados: {len(auto._modules)}")
    print(f"   Funciones registradas: {len(auto.metadata)}")
    print(f"   Categorías activas: {sum(1 for f in all_functions.values() if f)}")

def generate_documentation():
    """Genera documentación automática del sistema."""
    print_header("DOCUMENTACIÓN DEL SISTEMA")
    
    docs = []
    
    for key, info in auto.metadata.items():
        category, func_name = key.split('.', 1)
        docs.append({
            "category": category,
            "name": func_name,
            "doc": info["doc"] or "Sin documentación",
            "signature": info["signature"],
            "tags": info["tags"]
        })
    
    # Agrupar por categoría
    by_category = {}
    for doc in docs:
        category = doc["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(doc)
    
    # Imprimir documentación
    for category, functions in by_category.items():
        print(f"\\n{category.upper()} ({len(functions)} funciones):")
        print("-" * 40)
        
        for func in sorted(functions, key=lambda x: x["name"]):
            print(f"\\n{func['name']}{func['signature']}")
            print(f"  {func['doc']}")
            if func["tags"]:
                print(f"  Tags: {', '.join(func['tags'])}")

def main():
    """Función principal del sistema de ejemplo."""
    print("=" * 60)
    print("SISTEMA DE EJEMPLO COMPLETO CON OMNIAUTO")
    print("=" * 60)
    
    # Mostrar módulos cargados
    print(f"\\nMódulos descubiertos: {list(auto._modules.keys())}")
    
    # Ejecutar demos
    demo_authentication()
    demo_user_interface()
    demo_data_processing()
    demo_api_integration()
    demo_omniauto_features()
    generate_documentation()
    
    # Instrucciones para el CLI
    print_header("INSTRUCCIONES DEL CLI")
    print("\\nPuedes usar los siguientes comandos:")
    print("  omniauto list                # Listar todas las funciones")
    print("  omniauto generate --type all # Generar stubs y contexto para IA")
    print("  omniauto reload              # Recargar módulos (si los editas)")
    print("  omniauto --help              # Ver todos los comandos disponibles")
    
    print("\\n" + "=" * 60)
    print("FIN DEL SISTEMA DE EJEMPLO")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''
    main_script.write_text(main_content, encoding='utf-8')
    
    # ======================
    # ARCHIVO DE TEST
    # ======================
    test_script = target_dir / "test_system.py"
    test_content = '''"""
Tests del sistema de ejemplo Omniauto.
"""

import unittest
from omniauto import auto
from pathlib import Path

class TestOmniautoSystem(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada test."""
        pass  # Usamos la instancia global auto
    
    def test_modules_discovered(self):
        """Verifica que los módulos se descubrieron correctamente."""
        expected_modules = {'auth', 'ventanas', 'datos', 'api'}
        actual_modules = set(auto._modules.keys())
        
        self.assertTrue(
            expected_modules.issubset(actual_modules),
            f"Faltan módulos: {expected_modules - actual_modules}"
        )
    
    def test_authentication_functions(self):
        """Test de funciones de autenticación."""
        # Login exitoso
        result = auto.ui.login("admin", "admin123")
        self.assertTrue(result["success"])
        self.assertEqual(result["username"], "admin")
        
        # Login fallido
        result = auto.ui.login("invalid", "wrong")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_data_processing_functions(self):
        """Test de funciones de procesamiento de datos."""
        data = [1, 2, 3, 4, 5]
        analysis = auto.data.analyze_dataset(data)
        
        self.assertEqual(analysis["count"], 5)
        self.assertEqual(analysis["sum"], 15)
        self.assertEqual(analysis["mean"], 3)
        self.assertEqual(analysis["median"], 3)
    
    def test_ui_functions(self):
        """Test de funciones de interfaz."""
        # Dashboard para admin
        dashboard = auto.ui.show_dashboard("admin")
        self.assertIn("title", dashboard)
        self.assertIn("widgets", dashboard)
        self.assertGreater(len(dashboard["widgets"]), 0)
        
        # Formulario de login
        form = auto.ui.show_form("login")
        self.assertIn("fields", form)
        self.assertIn("submit_text", form)
    
    def test_metadata_registration(self):
        """Verifica que las funciones tengan metadata."""
        self.assertGreater(len(auto.metadata), 0)
        
        # Verificar que algunas funciones específicas tienen metadata
        test_functions = [
            "ui.login",
            "data.analyze_dataset",
            "utils.validate_password"
        ]
        
        for func_key in test_functions:
            self.assertIn(
                func_key, auto.metadata,
                f"Falta metadata para {func_key}"
            )
            self.assertIn("doc", auto.metadata[func_key])
            self.assertIn("signature", auto.metadata[func_key])
    
    def test_function_categories(self):
        """Verifica que las funciones están correctamente categorizadas."""
        functions_by_category = auto.list_functions()
        
        # Verificar que existen las categorías principales
        expected_categories = {"ui", "data", "utils"}
        actual_categories = set(functions_by_category.keys())
        
        self.assertTrue(
            expected_categories.issubset(actual_categories),
            f"Faltan categorías: {expected_categories - actual_categories}"
        )
        
        # Verificar que cada categoría tiene funciones
        for category in expected_categories:
            self.assertGreater(
                len(functions_by_category[category]), 0,
                f"La categoría {category} está vacía"
            )
    
    def test_api_functions(self):
        """Test de funciones de API (sin conexión real)."""
        # Test de validación de respuesta
        mock_response = {
            "success": True,
            "data": {"userId": 1, "id": 1, "title": "test", "body": "test"}
        }
        
        errors = auto.utils.validate_api_response(
            mock_response,
            expected_keys=["userId", "id", "title", "body"]
        )
        
        self.assertEqual(len(errors), 0)
        
        # Test con respuesta inválida
        mock_response_invalid = {
            "success": True,
            "data": {"userId": 1}  # Faltan keys
        }
        
        errors = auto.utils.validate_api_response(
            mock_response_invalid,
            expected_keys=["userId", "id", "title", "body"]
        )
        
        self.assertGreater(len(errors), 0)

def run_tests():
    """Ejecuta todos los tests y muestra resultados."""
    print("Ejecutando tests del sistema Omniauto...")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestOmniautoSystem)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ Todos los tests pasaron correctamente")
    else:
        print("❌ Algunos tests fallaron")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests()
'''
    test_script.write_text(test_content, encoding='utf-8')
    
    # ======================
    # CONFIGURACIÓN
    # ======================
    config_file = config_dir / "settings.json"
    config_content = '''{
    "app_name": "Sistema Ejemplo Omniauto",
    "version": "1.0.0",
    "settings": {
        "debug": true,
        "log_level": "INFO",
        "max_file_size": 10485760,
        "allowed_extensions": [".py", ".json", ".csv", ".txt"]
    },
    "paths": {
        "modules": "./modules",
        "logs": "./logs",
        "data": "./data",
        "cache": "./cache"
    },
    "api_endpoints": {
        "external_api": "https://jsonplaceholder.typicode.com",
        "internal_api": "http://localhost:8000"
    },
    "features": {
        "autodiscovery": true,
        "hot_reload": true,
        "generate_stubs": true,
        "ai_context": true
    }
}
'''
    config_file.write_text(config_content, encoding='utf-8')
    
    # ======================
    # REQUIREMENTS
    # ======================
    requirements_file = target_dir / "requirements.txt"
    requirements_content = '''omniauto>=0.1.0
requests>=2.31.0
click>=8.0.0

# Para desarrollo
pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0
'''
    requirements_file.write_text(requirements_content, encoding='utf-8')
    
    # ======================
    # README DEL EJEMPLO
    # ======================
    readme_file = target_dir / "README.md"
    readme_content = """# Sistema de Ejemplo Omniauto

    Este es un sistema de ejemplo completo que demuestra las capacidades de Omniauto en un escenario real.

    ## Estructura del Proyecto
    omniauto_example/
    ├── modules/ # Módulos descubiertos automáticamente
    │ ├── auth.py # Autenticación y usuarios
    │ ├── ventanas.py # Interfaces y UI
    │ ├── datos.py # Procesamiento de datos
    │ └── api.py # Integración con APIs
    ├── tests/ # Tests automatizados
    │ └── test_system.py
    ├── config/ # Configuración
    │ └── settings.json
    ├── docs/ # Documentación
    ├── main.py # Sistema principal
    ├── test_system.py # Tests
    └── requirements.txt # Dependencias


    ## Funcionalidades Demostradas

    ### 1. Sistema de Autenticación
    - Login/logout de usuarios
    - Validación de credenciales
    - Gestión de perfiles
    - Validación de contraseñas

    ### 2. Interfaces de Usuario
    - Dashboards dinámicos según roles
    - Formularios configurables
    - Menús de navegación basados en permisos

    ### 3. Procesamiento de Datos
    - Análisis estadístico
    - Importación/exportación de datos
    - Transformación y filtrado
    - Validación de datos

    ### 4. Integración con APIs
    - Llamadas HTTP a APIs externas
    - Validación de respuestas
    - Procesamiento por lotes
    - Cache básico

    ## Cómo Usar

    ### 1. Ejecutar el sistema principal
    ```bash
    python main.py

    python test_system.py


    # Listar todas las funciones disponibles
    omniauto list

    # Generar stubs para autocompletado
    omniauto generate --type python

    # Generar contexto para IA
    omniauto generate --type ai

    # Recargar módulos (desarrollo)
    omniauto reload

    Características de Omniauto Demostradas
    Descubrimiento automático: Los 4 módulos se descubren automáticamente

    Organización por categorías: Funciones organizadas en UI, Data, Utils

    Metadata completa: Cada función tiene documentación, firma y tags

    CLI integrado: Herramientas para desarrollo y mantenimiento

    Sistema de tags: Búsqueda y organización por etiquetas

    Extensión del Sistema
    Para añadir nuevas funcionalidades:

    Crea un nuevo archivo en modules/ (ej: notifications.py)

    Decora tus funciones con @ui, @data, o @utils

    Omniauto las descubrirá automáticamente

    Usa auto.reload_modules() para cargar cambios sin reiniciar

    Requisitos
    Python 3.7+

    Omniauto 0.1.0+

    Dependencias listadas en requirements.txt
    """

    readme_file.write_text(readme_content, encoding='utf-8')

    #======================
    #SCRIPT DE INICIO RÁPIDO
    #======================
    quickstart_file = target_dir / "quickstart.py"
    quickstart_content = '''"""
    Script de inicio rápido para Omniauto.
    """

    from omniauto import auto

    print("=== INICIO RÁPIDO OMNIAUTO ===")
    print("Este script muestra las funcionalidades básicas de Omniauto.")
    print()

    1. Mostrar lo que se cargó
    print("1. Módulos descubiertos automáticamente:")
    for module_name in auto._modules:
    print(f" - {module_name}")

    print()

    2. Mostrar funciones disponibles
    print("2. Funciones disponibles (primeras 5 de cada categoría):")
    for category, functions in auto.list_functions().items():
    if functions:
    print(f" {category.upper()}:")
    for func in functions[:5]:
    print(f" • {func}")
    if len(functions) > 5:
    print(f" ... y {len(functions) - 5} más")

    print()

    3. Ejemplo rápido de uso
    print("3. Ejemplo rápido de uso:")
    if hasattr(auto.ui, 'login'):
    result = auto.ui.login("admin", "admin123")
    print(f" Login: {'Éxito' if result['success'] else 'Falló'}")

    if hasattr(auto.data, 'analyze_dataset'):
    analysis = auto.data.analyze_dataset([10, 20, 30, 40, 50])
    print(f" Análisis de datos: Media = {analysis['mean']}")

    print()

    4. Instrucciones para explorar más
    print("4. Para explorar más:")
    print(" • Ejecuta 'python main.py' para el demo completo")
    print(" • Ejecuta 'omniauto list' para ver todas las funciones")
    print(" • Ejecuta 'omniauto generate' para crear stubs y contexto IA")
    print()

    print("=== FIN INICIO RÁPIDO ===")
    '''
    quickstart_file.write_text(quickstart_content, encoding='utf-8')

    # ======================
    # INFORMACIÓN FINAL
    # ======================
    print(f"[INFO] Proyecto de ejemplo creado en: {target_dir}")
    print(f"[INFO] Estructura creada:")
    print(f"  {target_dir}/")
    print(f"  ├── modules/")
    print(f"  │   ├── auth.py       (Autenticación)")
    print(f"  │   ├── ventanas.py   (Interfaces)")
    print(f"  │   ├── datos.py      (Procesamiento)")
    print(f"  │   └── api.py        (APIs externas)")
    print(f"  ├── tests/")
    print(f"  │   └── test_system.py")
    print(f"  ├── config/")
    print(f"  │   └── settings.json")
    print(f"  ├── docs/")
    print(f"  ├── main.py           (Sistema principal)")
    print(f"  ├── test_system.py    (Tests)")
    print(f"  ├── quickstart.py     (Inicio rápido)")
    print(f"  ├── requirements.txt  (Dependencias)")
    print(f"  └── README.md         (Documentación)")
    print()
    print("[COMANDOS] Para probar:")
    print(f"  cd {target_dir}")
    print(f"  python main.py              # Sistema completo")
    print(f"  python quickstart.py        # Inicio rápido")
    print(f"  python test_system.py       # Ejecutar tests")
    print(f"  omniauto list               # Listar funciones")
    print(f"  omniauto generate --type all # Generar herramientas")

    return target_dir