
#!/usr/bin/env python3
"""
Script para verificar la validez del token de Discord
"""

import json
import os
import requests
import sys

def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: config.json no encontrado")
        return {}
    except json.JSONDecodeError:
        print("❌ Error: config.json tiene formato inválido")
        return {}

def get_token():
    config = load_config()
    
    # Intentar desde config.json
    token = config.get('discord_bot_token')
    if token and token.strip() and token != "tu_token_aqui":
        return token.strip(), "config.json"
    
    # Intentar desde variables de entorno
    token = os.getenv('DISCORD_BOT_TOKEN')
    if token and token.strip():
        return token.strip(), "variables de entorno"
    
    return None, None

def verify_token(token):
    """Verificar si el token es válido haciendo una petición a Discord API"""
    headers = {
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Verificar el token haciendo una petición simple
        response = requests.get('https://discord.com/api/v10/gateway/bot', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return True, f"Token válido. Sesiones recomendadas: {data.get('session_start_limit', {}).get('total', 'N/A')}"
        elif response.status_code == 401:
            return False, "Token inválido o mal formateado"
        elif response.status_code == 503:
            return False, "Servicio Discord temporalmente no disponible (503)"
        else:
            return False, f"Error HTTP {response.status_code}: {response.text}"
            
    except requests.exceptions.ConnectTimeout:
        return False, "Timeout de conexión - verifica tu internet"
    except requests.exceptions.ConnectionError:
        return False, "Error de conexión - verifica tu internet"
    except Exception as e:
        return False, f"Error inesperado: {e}"

def main():
    print("🔍 Verificador de Token de Discord")
    print("-" * 40)
    
    # Obtener token
    token, source = get_token()
    
    if not token:
        print("❌ No se encontró token de Discord")
        print("\n📋 Para solucionarlo:")
        print("1. Ve a https://discord.com/developers/applications")
        print("2. Selecciona tu aplicación")
        print("3. Ve a 'Bot' en el menú lateral")
        print("4. Copia el token y actualiza config.json")
        return 1
    
    print(f"✅ Token encontrado en: {source}")
    print(f"📏 Longitud del token: {len(token)} caracteres")
    
    # Verificar formato básico
    if not token.startswith(('MTA', 'MTM', 'OTA', 'ODg', 'ODE')):
        print("⚠️ Advertencia: El token no tiene el formato esperado")
    
    # Verificar token con Discord API
    print("\n🔗 Verificando token con Discord API...")
    is_valid, message = verify_token(token)
    
    if is_valid:
        print(f"✅ {message}")
        print("\n🎉 ¡El token es válido! El bot debería funcionar correctamente.")
        return 0
    else:
        print(f"❌ {message}")
        print("\n📋 Para solucionarlo:")
        print("1. Ve a https://discord.com/developers/applications")
        print("2. Selecciona tu aplicación")
        print("3. Ve a 'Bot' en el menú lateral")
        print("4. Haz clic en 'Reset Token'")
        print("5. Copia el nuevo token y actualiza config.json")
        return 1

if __name__ == "__main__":
    sys.exit(main())
