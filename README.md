# Discord Time Tracker Bot

Bot de Discord para seguimiento de tiempo con comandos slash.

## Configuración del Token

### Opción 1: Archivo config.json (Recomendado)
Edita el archivo `config.json` y añade tu token:

```json
{
  "discord_bot_token": "tu_token_aqui"
}
```

### Opción 2: Variable de entorno
```bash
export DISCORD_BOT_TOKEN="tu_token_aqui"
```

## Instalación

### Dependencias
```bash
pip install discord.py
```

### Ejecución
```bash
python bot.py
```

## Para diferentes hosts

### Pterodactyl/Panel hosts
- Archivo principal: `bot.py`
- Comando de inicio: `python bot.py`
- Variables de entorno: `DISCORD_BOT_TOKEN`

### Railway/Heroku
- Usar `main.py` o `start.py`
- Configurar Procfile si es necesario

### Replit
- El bot está configurado y listo para usar
- Token configurado como secret

## Comandos disponibles

- `/iniciar_tiempo` - Iniciar seguimiento
- `/pausar_tiempo` - Pausar seguimiento  
- `/despausar_tiempo` - Reanudar seguimiento
- `/ver_tiempos` - Ver tiempos actuales
- `/mi_tiempo` - Ver tu tiempo personal
- Y más comandos administrativos...

## Configuración de roles y canales

Todos los IDs se configuran en `config.json`:
- `unlimited_time_role_id` - Rol para tiempo ilimitado
- `command_permission_role_id` - Rol para usar comandos
- `mi_tiempo_role_id` - Rol para usar /mi_tiempo
- Canales de notificación configurables