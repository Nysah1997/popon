
#!/usr/bin/env python3
"""
Script de inicio universal para el Discord Time Tracker Bot
Detecta automáticamente el entorno y configura las dependencias necesarias
"""

import os
import sys
import subprocess
import importlib.util
import json

def run_command(command, shell=False):
    """Ejecutar comando de forma segura"""
    try:
        if shell:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        else:
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout ejecutando comando")
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def install_package(package):
    """Instalar paquete usando múltiples métodos"""
    print(f"🔄 Intentando instalar {package}...")
    
    # Método 1: pip install
    success, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", package])
    if success:
        print(f"✅ {package} instalado con pip")
        return True
    
    # Método 2: pip install --user
    print("🔄 Intentando con --user...")
    success, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "--user", package])
    if success:
        print(f"✅ {package} instalado con pip --user")
        return True
    
    # Método 3: pip3 install
    print("🔄 Intentando con pip3...")
    success, stdout, stderr = run_command(["pip3", "install", package])
    if success:
        print(f"✅ {package} instalado con pip3")
        return True
    
    # Método 4: python -m pip install --break-system-packages (para algunos sistemas)
    print("🔄 Intentando con --break-system-packages...")
    success, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "--break-system-packages", package])
    if success:
        print(f"✅ {package} instalado con --break-system-packages")
        return True
    
    # Método 5: apt install (para sistemas con apt)
    if package == "discord.py":
        print("🔄 Intentando con apt (sistemas Debian/Ubuntu)...")
        success, stdout, stderr = run_command(["apt", "install", "-y", "python3-discord"], shell=True)
        if success:
            print(f"✅ discord instalado con apt")
            return True
    
    print(f"❌ No se pudo instalar {package}")
    print(f"Error: {stderr}")
    return False

def check_package_installed(module_name):
    """Verificar si un paquete está instalado"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            return True
        
        # Intentar importar directamente
        __import__(module_name)
        return True
    except ImportError:
        return False

def setup_python_path():
    """Configurar Python path para incluir directorios comunes de paquetes"""
    import site
    
    # Agregar directorios comunes donde se instalan paquetes
    possible_paths = [
        os.path.expanduser("~/.local/lib/python3.11/site-packages"),
        os.path.expanduser("~/.local/lib/python3.10/site-packages"),
        os.path.expanduser("~/.local/lib/python3.9/site-packages"),
        "/usr/local/lib/python3.11/site-packages",
        "/usr/local/lib/python3.10/site-packages",
        "/usr/lib/python3/dist-packages",
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)

def check_and_install_dependencies():
    """Verificar e instalar dependencias necesarias"""
    print("🔍 Verificando dependencias...")
    
    # Configurar Python path
    setup_python_path()
    
    # Lista de paquetes requeridos
    required_packages = [
        ("discord", "discord.py>=2.3.0"),
        ("asyncio", None),  # asyncio es built-in pero verificamos
    ]
    
    missing_packages = []
    
    # Verificar qué paquetes faltan
    for module_name, package_name in required_packages:
        if not check_package_installed(module_name):
            if package_name:
                missing_packages.append(package_name)
    
    # Instalar paquetes faltantes
    if missing_packages:
        print(f"📦 Instalando dependencias faltantes: {', '.join(missing_packages)}")
        
        for package in missing_packages:
            if install_package(package):
                print(f"✅ {package} instalado correctamente")
                
                # Recargar módulos después de la instalación
                if package.startswith("discord"):
                    setup_python_path()
                    importlib.invalidate_caches()
                    
            else:
                print(f"❌ Error instalando {package}")
                print("🔧 Intenta instalar manualmente:")
                print(f"   pip install {package}")
                print(f"   pip3 install {package}")
                print(f"   python -m pip install {package}")
                return False
        
        print("✅ Instalación de dependencias completada")
        
        # Verificar que todo se instaló correctamente
        print("🔍 Verificando instalación...")
        setup_python_path()
        importlib.invalidate_caches()
        
        for module_name, _ in required_packages:
            if module_name != "asyncio" and not check_package_installed(module_name):
                print(f"❌ {module_name} aún no está disponible después de la instalación")
                return False
        
        print("✅ Todas las dependencias verificadas")
    else:
        print("✅ Todas las dependencias ya están instaladas")
    
    return True

def get_discord_token():
    """Obtener token de Discord desde config.json o variables de entorno"""
    # Intentar cargar desde config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        token = config.get('discord_bot_token')
        if token and token.strip() and token != "tu_token_aqui":
            print("✅ Token cargado desde config.json")
            return token.strip()
    except Exception:
        pass
    
    # Intentar desde variables de entorno
    token = os.getenv('DISCORD_BOT_TOKEN')
    if token and token.strip():
        print("✅ Token cargado desde variables de entorno")
        return token.strip()
    
    return None

def create_minimal_config():
    """Crear config.json mínimo si no existe"""
    if not os.path.exists('config.json'):
        minimal_config = {
            "discord_bot_token": "tu_token_aqui",
            "unlimited_time_role_id": None,
            "notification_channels": {
                "milestones": 1382195219939852500,
                "pauses": 1385005232685318282,
                "cancellations": 1385005232685318284,
                "attendances": 1385005232685318281
            }
        }
        
        try:
            with open('config.json', 'w') as f:
                json.dump(minimal_config, f, indent=2)
            print("✅ Archivo config.json creado")
        except Exception as e:
            print(f"⚠️ No se pudo crear config.json: {e}")

def main():
    """Función principal"""
    print("🚀 Iniciando Discord Time Tracker Bot...")
    print(f"🐍 Python {sys.version}")
    print("🔍 Verificando entorno...")
    
    # Crear config.json si no existe
    create_minimal_config()
    
    # Verificar token antes de instalar dependencias
    token = get_discord_token()
    if not token:
        print("❌ ERROR: No se encontró el token de Discord")
        print("┌─ Configura tu token de una de estas formas:")
        print("│")
        print("│ OPCIÓN 1 (Recomendado): En config.json")
        print("│ Edita config.json y cambia:")
        print('│ "discord_bot_token": "tu_token_aqui"')
        print("│")
        print("│ OPCIÓN 2: Variable de entorno")
        print("│ Configura DISCORD_BOT_TOKEN en tu panel de hosting")
        print("└─")
        return 1
    
    # Instalar dependencias
    if not check_and_install_dependencies():
        print("❌ Error instalando dependencias")
        print("🔧 Soluciones manuales:")
        print("   1. pip install discord.py")
        print("   2. pip3 install discord.py")
        print("   3. python -m pip install discord.py")
        print("   4. apt install python3-discord (Ubuntu/Debian)")
        return 1
    
    # Importar y ejecutar el bot
    try:
        print("🤖 Iniciando bot...")
        
        # Añadir directorio actual al path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Configurar path una vez más antes de importar
        setup_python_path()
        
        # Importar el bot
        import bot
        print("✅ Bot iniciado correctamente")
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("🔧 Verifica que todos los archivos estén presentes")
        print("🔧 O intenta ejecutar directamente: python bot.py")
        return 1
    except KeyboardInterrupt:
        print("🛑 Bot detenido por el usuario")
        return 0
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        print("📋 Verifica tu configuración")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
