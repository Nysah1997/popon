# Discord Time Tracker Bot - Archivos Finales

## Archivos incluidos:

### Archivos principales:
- `bot.py` - Archivo principal del bot con todos los comandos
- `time_tracker.py` - Sistema de seguimiento de tiempo
- `config.json` - Configuración (pon tu token aquí)

### Archivos de inicio:
- `start.py` - Script universal para diferentes hosts (recomendado)
- `main.py` - Archivo alternativo de entrada
- `run.py` - Script de ejecución

### Documentación:
- `README.md` - Documentación completa
- `HOSTING_SETUP.md` - Instrucciones para diferentes hosts
- `INSTRUCCIONES.md` - Este archivo

## Configuración rápida:

### 1. Configurar token:
Edita `config.json` y cambia:
```json
"discord_bot_token": "tu_token_real_aqui"
```

### 2. Para hosts como Pterodactyl:
- Configura `PY_FILE` = `start.py` en tu panel
- Reinicia el bot

### 3. Para otros hosts:
- Usa `python bot.py` o `python start.py`

## Nuevos comandos implementados:

### Comando de limpieza de base de datos:
- `/limpiar_base_datos` - Muestra información y solicita confirmación
- `/limpiar_base_datos_confirmar` - Ejecuta la limpieza escribiendo "SI"

### Diferencias:
- `/reiniciar_todos_tiempos` - Pone tiempos en 0 pero mantiene usuarios
- `/limpiar_base_datos` - Elimina completamente todos los usuarios

## Todos los comandos disponibles:

### Comandos administrativos:
- `/iniciar_tiempo` - Iniciar seguimiento para un usuario
- `/pausar_tiempo` - Pausar seguimiento
- `/despausar_tiempo` - Reanudar seguimiento
- `/sumar_minutos` - Agregar tiempo manualmente
- `/restar_minutos` - Restar tiempo manualmente
- `/ver_tiempos` - Ver todos los tiempos
- `/reiniciar_tiempo` - Reiniciar tiempo de un usuario
- `/reiniciar_todos_tiempos` - Reiniciar todos los tiempos
- `/limpiar_base_datos` - Eliminar todos los usuarios (con confirmación)
- `/cancelar_tiempo` - Cancelar tiempo de un usuario
- `/saber_tiempo` - Ver tiempo de cualquier usuario

### Comandos de configuración:
- `/configurar_canal_tiempos` - Canal para notificaciones de milestones
- `/configurar_canal_pausas` - Canal para notificaciones de pausas
- `/configurar_canal_cancelaciones` - Canal para cancelaciones
- `/configurar_canal_despausados` - Canal para reanudaciones
- `/configurar_rol_tiempo_ilimitado` - Rol con tiempo ilimitado
- `/configurar_permisos_comandos` - Rol para usar comandos admin
- `/configurar_mi_tiempo` - Rol para usar /mi_tiempo

### Comando de usuario:
- `/mi_tiempo` - Ver tu propio tiempo (requiere rol específico)

## Características del sistema:

### Sistema de pausas:
- Usuarios se cancelan automáticamente tras 3 pausas
- Notificaciones automáticas en canales configurados

### Sistema de créditos:
- Sin rol especial: 1 crédito/minuto hasta 2h, luego 2 créditos/minuto
- Con rol especial: 2 créditos/minuto hasta 4h, luego 3 créditos/minuto

### Límites de tiempo:
- Sin rol especial: Límite de 2 horas
- Con rol especial: Sin límite, pero se pausa automáticamente cada hora

### Notificaciones automáticas:
- Milestones de cada hora completada
- Pausas y reanudaciones
- Cancelaciones manuales y automáticas

Todos los archivos están listos para usar. Solo necesitas configurar el token en `config.json`.