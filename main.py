#!/usr/bin/env python3
"""
Archivo principal alternativo para hosts que buscan main.py
Este archivo simplemente importa y ejecuta bot.py
"""

import os
import sys
import asyncio

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        print("🔥 Iniciando bot desde main.py...")
        
        # Importar el módulo bot (esto carga la configuración)
        import bot
        print("✅ Bot importado correctamente")
        
        # Obtener el token y ejecutar el bot
        token = bot.get_discord_token()
        if not token:
            print("❌ Error: Token de Discord no encontrado")
            return 1
        
        print("🔗 Conectando a Discord...")
        bot.bot.run(token)
        
    except KeyboardInterrupt:
        print("🛑 Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        print("📋 Verifica tu configuración en config.json")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)