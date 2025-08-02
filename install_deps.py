
#!/usr/bin/env python3
"""
Script simple para instalar discord.py en cualquier host
"""

import subprocess
import sys
import os

def install_discord():
    """Instalar discord.py usando múltiples métodos"""
    methods = [
        [sys.executable, "-m", "pip", "install", "discord.py"],
        [sys.executable, "-m", "pip", "install", "--user", "discord.py"],
        ["pip3", "install", "discord.py"],
        ["pip", "install", "discord.py"],
        [sys.executable, "-m", "pip", "install", "--break-system-packages", "discord.py"],
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"🔄 Método {i}: {' '.join(method)}")
        try:
            result = subprocess.run(method, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✅ discord.py instalado exitosamente con método {i}")
                return True
            else:
                print(f"❌ Método {i} falló: {result.stderr}")
        except Exception as e:
            print(f"❌ Método {i} error: {e}")
    
    print("❌ Todos los métodos fallaron")
    return False

def test_import():
    """Probar importar discord"""
    try:
        import discord
        print(f"✅ discord.py version {discord.__version__} importado correctamente")
        return True
    except ImportError as e:
        print(f"❌ No se puede importar discord: {e}")
        return False

if __name__ == "__main__":
    print("📦 Instalador de dependencias para Discord Bot")
    print(f"🐍 Python {sys.version}")
    
    # Probar si ya está instalado
    if test_import():
        print("✅ discord.py ya está instalado")
        sys.exit(0)
    
    # Instalar
    print("🔄 Instalando discord.py...")
    if install_discord():
        # Probar importación
        if test_import():
            print("🎉 Instalación exitosa")
            sys.exit(0)
    
    print("❌ Instalación falló")
    print("🔧 Intenta manualmente:")
    print("   pip install discord.py")
    print("   pip3 install discord.py")
    sys.exit(1)
