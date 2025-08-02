# Configuración para Diferentes Hosts

## Para hosts con Pterodactyl/Panel (El error que tienes)

### Variables que necesitas configurar:
- `PY_FILE` = `start.py`
- `DISCORD_BOT_TOKEN` = tu_token_real

### Archivos disponibles para ejecutar:
- `start.py` (Recomendado - auto-instala dependencias)
- `bot.py` (Principal)
- `main.py` (Alternativo)

### Solución al error:
En tu panel de control:
1. Ve a Variables/Environment Variables
2. Configura `PY_FILE` = `start.py`
3. Configura `DISCORD_BOT_TOKEN` = tu token real
4. Reinicia el bot

### Método alternativo (más fácil):
1. Edita `config.json` directamente:
   ```json
   "discord_bot_token": "tu_token_real_aqui"
   ```
2. Usa `start.py` como archivo principal
3. No necesitas configurar variables de entorno

## Para Replit
- Ya configurado automáticamente
- Usa secrets para el token

## Para Railway/Heroku
- Configura `DISCORD_BOT_TOKEN` en variables de entorno
- Usa `start.py` como comando de inicio

## Archivos importantes:
- `config.json` - Configuración principal (recomendado para token)
- `start.py` - Inicio universal con auto-instalación
- `bot.py` - Archivo principal del bot
- `time_tracker.py` - Sistema de seguimiento de tiempo