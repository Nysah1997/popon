import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
import os
from datetime import datetime, timedelta
import time_tracker

# Cargar configuración
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

config = load_config()

# Obtener token
def get_discord_token():
    # Intentar desde config.json
    token = config.get('discord_bot_token')
    if token and token.strip() and token != "tu_token_aqui":
        token = token.strip()
        print("✅ Token cargado desde config.json")
        return token

    # Intentar desde variables de entorno
    token = os.getenv('DISCORD_BOT_TOKEN')
    if token and token.strip():
        token = token.strip()
        print("✅ Token cargado desde variables de entorno")
        return token

    print("❌ No se encontró token en config.json ni en variables de entorno")
    return None

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# IDs de roles
ROLE_IDS = {
    'gold': config.get('gold_role_id', 1382198935971430440),
    'alto': config.get('alto_role_id', None),
    'supervisor': config.get('supervisor_role_id', None),
    'silver': config.get('silver_role_id', None),
    'expediente': config.get('expediente_role_id', None)
}

# Sistema de créditos por rol y día de la semana
CREDIT_SYSTEM = {
    'recluta': {
        4: 3,    # Viernes: 3 créditos por hora (máximo 1h = 3 créditos)
        5: 3,    # Sábado: 3 créditos por hora (máximo 1h = 3 créditos)
        6: 3     # Domingo: 3 créditos por hora (máximo 1h = 3 créditos)
        # TOTAL SEMANAL: 9 créditos máximo
    },
    'gold': {
        4: 5,    # Viernes: 5 créditos por hora
        5: 5,    # Sábado: 5 créditos por hora
        6: 10    # Domingo: 10 créditos por hora
    },
    'alto': {
        4: 3,    # Viernes: 3 créditos por hora (6 créditos en 2h)
        5: 3,    # Sábado: 3 créditos por hora (6 créditos en 2h)
        6: 4     # Domingo: 4 créditos por hora (8 créditos en 2h)
        # TOTAL SEMANAL: 20 créditos máximo
    },
    'supervisor': {
        4: 4,    # Viernes: 4 créditos por hora (8 créditos en 2h)
        5: 4,    # Sábado: 4 créditos por hora (8 créditos en 2h)  
        6: 7     # Domingo: 7 créditos por hora (14 créditos en 2h)
        # TOTAL SEMANAL: 30 créditos máximo
    },
    'silver': {
        4: 6,    # Viernes: 6 créditos por hora (12 créditos en 2h)
        5: 6,    # Sábado: 6 créditos por hora (12 créditos en 2h)
        6: 8     # Domingo: 8 créditos por hora (16 créditos en 2h)  
        # TOTAL SEMANAL: 40 créditos máximo
    },
    'expediente': {
        4: 7,    # Viernes: 7 créditos por hora (14 créditos en 2h)
        5: 7,    # Sábado: 7 créditos por hora (14 créditos en 2h)
        6: 11     # Domingo: 11 créditos por hora (22 créditos en 2h)
        # TOTAL SEMANAL: 50 créditos máximo
    }
}

# Días permitidos para trabajar (viernes, sábado, domingo)
ALLOWED_DAYS = [4, 5, 6]  # 4=viernes, 5=sábado, 6=domingo

# Canales de notificación
NOTIFICATION_CHANNELS = config.get('notification_channels', {})

# Instancia del tracker
tracker = time_tracker.TimeTracker()

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} comandos sincronizados')
    except Exception as e:
        print(f'❌ Error sincronizando comandos: {e}')

def get_user_role(member):
    """Obtener el rol más alto del usuario basado en la jerarquía de Discord"""
    if not member:
        return 'recluta'

    # Obtener todos los roles del usuario ordenados por posición (jerarquía)
    # Discord ordena los roles por posición, donde mayor posición = mayor jerarquía
    user_roles = sorted(member.roles, key=lambda r: r.position, reverse=True)

    # Definir mapeo de IDs a nombres de roles para búsqueda
    role_mapping = {
        ROLE_IDS['expediente']: 'expediente',
        ROLE_IDS['silver']: 'silver', 
        ROLE_IDS['supervisor']: 'supervisor',
        ROLE_IDS['alto']: 'alto',
        ROLE_IDS['gold']: 'gold'
    }

    # Buscar el rol más alto que coincida con nuestros roles configurados
    for role in user_roles:
        if role.id in role_mapping:
            return role_mapping[role.id]

    return 'recluta'

def is_allowed_day():
    """Verificar si hoy es un día permitido (viernes, sábado, domingo)"""
    today = datetime.now().weekday()
    return today in ALLOWED_DAYS

def get_daily_credits(user_role):
    """Obtener créditos del día actual según el rol"""
    if not is_allowed_day():
        return 0

    today = datetime.now().weekday()
    role_credits = CREDIT_SYSTEM.get(user_role, {})
    return role_credits.get(today, 0)

def get_user_daily_time(user_id):
    """Obtener tiempo trabajado hoy por un usuario"""
    return tracker.get_daily_time(user_id)

def can_user_work_today(user_id):
    """Verificar si un usuario puede trabajar hoy según su rol"""
    member = bot.get_guild(bot.guilds[0].id).get_member(user_id) if bot.guilds else None
    user_role = get_user_role(member) if member else 'recluta'

    daily_time = get_user_daily_time(user_id)

    # Rol normal: máximo 1 hora por día
    if user_role == 'recluta':
        max_daily_seconds = 1 * 3600  # 1 hora en segundos
    else:
        # Todos los demás roles: máximo 2 horas por día
        max_daily_seconds = 2 * 3600  # 2 horas en segundos

    return daily_time < max_daily_seconds

def get_user_saved_credits(user_id):
    """Obtener créditos guardados de un usuario"""
    return tracker.get_saved_credits(user_id)

def add_credits_to_user(user_id, credits):
    """Agregar créditos a un usuario"""
    return tracker.add_saved_credits(user_id, credits)

# Función para verificar si el usuario tiene el rol con ID para acceso completo
def has_admin_bypass(member):
    if not member:
        return False
    admin_bypass_role_id = 1366550916773318680  # ← Cambiar este ID por el nuevo rol
    for role in member.roles:
        if role.id == admin_bypass_role_id:
            return True
    return False

# Pagination
class PaginationView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        if self.current_page == 0:
            self.children[0].disabled = True  # Disable first button
        else:
            self.children[0].disabled = False  # Enable first button

        if self.current_page == len(self.embeds) - 1:
            self.children[1].disabled = True  # Disable last button
        else:
            self.children[1].disabled = False  # Enable last button

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

def create_paginated_embeds(data, title, color, items_per_page=10):
    """Crea embeds paginados a partir de una lista de datos."""
    embeds = []
    num_pages = (len(data) + items_per_page - 1) // items_per_page  # Calcula el número de páginas

    for i in range(num_pages):
        start_index = i * items_per_page
        end_index = min((i + 1) * items_per_page, len(data))
        page_data = data[start_index:end_index]

        embed = discord.Embed(title=f"{title} (Página {i + 1}/{num_pages})", color=color)
        for item in page_data:
            embed.add_field(name=item['name'], value=item['value'], inline=False)
        embeds.append(embed)

    return embeds

@bot.tree.command(name="iniciar_tiempo", description="Iniciar seguimiento de tiempo para un usuario")
async def iniciar_tiempo(interaction: discord.Interaction, usuario: discord.Member):
    import pytz

    user_id = usuario.id
    member = interaction.guild.get_member(user_id)
    user_role = get_user_role(member)

    # Obtener hora actual en Chile
    chile_tz = pytz.timezone('America/Santiago')
    chile_time = datetime.now(chile_tz)

    # Verificar día permitido (con bypass para admin)
    is_admin_bypass = has_admin_bypass(member)
    if not is_allowed_day() and not is_admin_bypass:
        embed = discord.Embed(
            title="❌ Día no permitido",
            description="Solo se puede trabajar los viernes, sábados y domingos.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Verificar límite diario según rol
    if not can_user_work_today(user_id):
        daily_time = get_user_daily_time(user_id)
        hours = int(daily_time // 3600)
        minutes = int((daily_time % 3600) // 60)

        # Mensaje diferente según el rol
        if user_role == 'recluta':
            limit_message = "su 1 hora diaria permitida"
        else:
            limit_message = "sus 2 horas diarias permitidas"

        embed = discord.Embed(
            title="❌ Límite diario alcanzado",
            description=f"{usuario.mention} ya completó {limit_message}.\n"
                       f"Tiempo trabajado hoy: {hours}h {minutes}m\n"
                       f"Podrá trabajar nuevamente mañana.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Verificar si ya tiene tiempo activo
    if tracker.is_user_active(user_id):
        embed = discord.Embed(
            title="⚠️ Usuario ya tiene tiempo activo",
            description=f"{usuario.mention} ya tiene un seguimiento de tiempo activo.",
            color=0xffaa00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Verificar si está pausado
    if tracker.is_user_paused(user_id):
        embed = discord.Embed(
            title="⚠️ Usuario pausado",
            description=f"{usuario.mention} tiene tiempo pausado. Usa `/despausar_tiempo` primero.",
            color=0xffaa00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # LÓGICA PRINCIPAL: Pre-registro antes de las 12:23, inicio inmediato después
    target_hour = 14
    target_minute = 31

    # Crear tiempo objetivo para comparación
    target_time = chile_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

    if chile_time < target_time:
        # PRE-REGISTRO (antes de las 12:23)
        success = tracker.pre_register_user(user_id, usuario.display_name)

        if success:
            # Registrar quién hizo el pre-registro
            tracker.set_pre_register_initiator(user_id, interaction.user.id, interaction.user.display_name)

            await interaction.response.send_message(
                f"📝 Se ha registrado el tiempo de {usuario.mention} por {interaction.user.mention}",
                ephemeral=False
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"{usuario.mention} ya está pre-registrado o tiene tiempo activo.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        # INICIO INMEDIATO (12:23 en adelante) - NO se otorgan créditos aquí
        success = tracker.start_time(user_id)

        if success:
            await interaction.response.send_message(
                f"⏰ El tiempo de {usuario.mention} ha sido iniciado por {interaction.user.mention}",
                ephemeral=False
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo iniciar el seguimiento.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="pausar_tiempo", description="Pausar seguimiento de tiempo de un usuario")
async def pausar_tiempo(interaction: discord.Interaction, usuario: discord.Member):
    user_id = usuario.id

    if not tracker.is_user_active(user_id):
        embed = discord.Embed(
            title="❌ Usuario sin tiempo activo",
            description=f"{usuario.mention} no tiene un seguimiento de tiempo activo.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    success = tracker.pause_time(user_id)

    if success:
        time_data = tracker.get_user_time(user_id)
        hours = int(time_data['total_seconds'] // 3600)
        minutes = int((time_data['total_seconds'] % 3600) // 60)

        embed = discord.Embed(
            title="⏸️ Tiempo pausado",
            description=f"Tiempo pausado para {usuario.mention} por {interaction.user.mention}\n"
                       f"Tiempo acumulado: {hours}h {minutes}m",
            color=0xffaa00
        )
        await interaction.response.send_message(embed=embed)

        # Notificar en canal de pausas
        if NOTIFICATION_CHANNELS.get('pauses'):
            channel = bot.get_channel(NOTIFICATION_CHANNELS['pauses'])
            if channel:
                await channel.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Error",
            description="No se pudo pausar el tiempo.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="despausar_tiempo", description="Reanudar seguimiento de tiempo de un usuario")
async def despausar_tiempo(interaction: discord.Interaction, usuario: discord.Member):
    user_id = usuario.id

    if not tracker.is_user_paused(user_id):
        embed = discord.Embed(
            title="❌ Usuario sin tiempo pausado",
            description=f"{usuario.mention} no tiene un tiempo pausado para reanudar.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    success = tracker.unpause_time(user_id)

    if success:
        embed = discord.Embed(
            title="▶️ Tiempo reanudado",
            description=f"Tiempo reanudado para {usuario.mention} por {interaction.user.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)

        # Notificar en canal de despausas
        if NOTIFICATION_CHANNELS.get('unpause'):
            channel = bot.get_channel(NOTIFICATION_CHANNELS['unpause'])
            if channel:
                await channel.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Error",
            description="No se pudo reanudar el tiempo.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="sumar_tiempo", description="Sumar tiempo a un usuario (en minutos)")
async def sumar_tiempo(interaction: discord.Interaction, usuario: discord.Member, minutos: int):
    """Suma minutos al tiempo de un usuario."""
    user_id = usuario.id

    # Verificar que los minutos sean válidos (entre 1 y 120)
    if minutos < 1 or minutos > 120:
        embed = discord.Embed(
            title="❌ Error",
            description="Los minutos deben estar entre 1 y 120.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Verificar si el usuario existe en el sistema
    if str(user_id) not in tracker.data:
        embed = discord.Embed(
            title="❌ Usuario no encontrado",
            description=f"{usuario.mention} no tiene tiempo registrado. Debe tener tiempo activo primero.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Obtener tiempo total actual antes de sumar
    tiempo_anterior = tracker.get_total_time(user_id)
    horas_antes = tiempo_anterior / 3600

    # Sumar los minutos usando el método correcto
    success = tracker.add_minutes(user_id, usuario.display_name, minutos)

    if success:
        # Obtener tiempo total después de sumar
        tiempo_nuevo = tracker.get_total_time(user_id)
        horas_despues = tiempo_nuevo / 3600

        # Obtener rol del usuario para calcular créditos
        member = interaction.guild.get_member(user_id)
        user_role = get_user_role(member) if member else 'recluta'

        # Obtener créditos por hora según rol y día
        today = datetime.now().weekday()
        role_credits = CREDIT_SYSTEM.get(user_role, {})

        # Verificar si es admin bypass para días no permitidos
        is_admin_bypass = has_admin_bypass(member)
        if is_admin_bypass and today not in ALLOWED_DAYS:
            credits_per_hour = role_credits.get(4, 0)  # Usar créditos del viernes
        else:
            credits_per_hour = role_credits.get(today, 0)

        # Verificar si se completaron nuevas horas y otorgar créditos
        creditos_otorgados = 0
        milestones_completados = []

        # Verificar milestone de 1 hora
        if horas_antes < 1 and horas_despues >= 1:
            if not tracker.data[str(user_id)].get('milestone_1h_completed', False):
                tracker.data[str(user_id)]['milestone_1h_completed'] = True
                if credits_per_hour > 0:
                    creditos_otorgados += credits_per_hour
                    add_credits_to_user(user_id, credits_per_hour)
                    milestones_completados.append(f"1 hora (+{int(credits_per_hour) if credits_per_hour == int(credits_per_hour) else credits_per_hour} créditos)")

        # Verificar milestone de 2 horas
        if horas_antes < 2 and horas_despues >= 2:
            if not tracker.data[str(user_id)].get('milestone_2h_completed', False):
                tracker.data[str(user_id)]['milestone_2h_completed'] = True
                if credits_per_hour > 0:
                    creditos_otorgados += credits_per_hour
                    add_credits_to_user(user_id, credits_per_hour)
                    milestones_completados.append(f"2 horas (+{int(credits_per_hour) if credits_per_hour == int(credits_per_hour) else credits_per_hour} créditos)")

        # Verificar si debe detenerse automáticamente 
        tiempo_total_horas = tiempo_nuevo / 3600

        # Para rol recluta: detener al alcanzar 1 hora
        if user_role == 'recluta' and tiempo_total_horas >= 1.0:
            if tracker.is_user_active(user_id) or tracker.is_user_paused(user_id):
                tracker.stop_tracking(user_id)

        # Para otros roles: detener al alcanzar 2 horas
        elif user_role != 'recluta' and tiempo_total_horas >= 2.0:
            if tracker.is_user_active(user_id) or tracker.is_user_paused(user_id):
                tracker.stop_tracking(user_id)

        # Guardar cambios
        tracker.save_data()

        # Mensaje simple sin información de detención automática
        mensaje = f"⏱️ {interaction.user.mention} sumó {minutos} minutos a {usuario.mention}"

        await interaction.response.send_message(mensaje)

        # Notificar en canal de milestones si se otorgaron créditos
        if milestones_completados and credits_per_hour > 0:
            milestone_channel = bot.get_channel(1385005232685318281)
            if milestone_channel:
                try:
                    # Mapear rol interno a nombre de cargo
                    role_names = {
                        'expediente': 'Expediente',
                        'silver': 'Silver',
                        'supervisor': 'Supervisor',
                        'alto': 'Alto',
                        'gold': 'Gold',
                        'recluta': 'Recluta'
                    }
                    role_display = role_names.get(user_role, user_role.title())

                    notificacion = f"🎉 **Créditos otorgados manualmente:**\n"
                    notificacion += f"{usuario.mention} - {', '.join(milestones_completados)} - Cargo: {role_display}"
                    await milestone_channel.send(notificacion)
                except Exception as e:
                    print(f"Error enviando notificación de milestone manual: {e}")

    else:
        embed = discord.Embed(
            title="❌ Error",
            description="No se pudo sumar el tiempo.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="mi_tiempo", description="Ver tu tiempo personal")
async def mi_tiempo(interaction: discord.Interaction):
    user_id = interaction.user.id
    member = interaction.guild.get_member(user_id)
    user_role = get_user_role(member)

    time_data = tracker.get_user_time(user_id)

    if not time_data:
        embed = discord.Embed(
            title=f"Tu Tiempo - @{interaction.user.display_name}",
            color=0x3498db,
            timestamp=datetime.now()
        )

        # Agregar foto de perfil del usuario
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        embed.add_field(
            name="⏱️ Tiempo Total",
            value="0 Segundos",
            inline=False
        )

        embed.add_field(
            name="📍 Estado", 
            value="⭕ Inactivo",
            inline=False
        )

        embed.add_field(
            name="💰 Créditos Ganados",
            value="0 créditos",
            inline=False
        )

        role_limits = {
            'expediente': f'Expediente - Límite: Sin límite',
            'silver': f'Silver - Límite: Sin límite',
            'supervisor': f'Supervisor - Límite: Sin límite', 
            'alto': f'Alto - Límite: Sin límite',
            'gold': f'Gold - Límite: 2 horas',
            'recluta': f'Recluta - Límite: 2 horas'
        }

        embed.add_field(
            name="👤 Tu Rol",
            value=role_limits.get(user_role, 'Recluta - Límite: 2 horas'),
            inline=False
        )

        embed.set_footer(text="Tu información personal de tiempo")

        await interaction.response.send_message(embed=embed, ephemeral=False)
        return

    # Usar tiempo total acumulado (incluyendo tiempo sumado manualmente)
    total_seconds = int(time_data['total_seconds'])
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Formatear tiempo
    if total_seconds == 0:
        time_display = "0 Segundos"
    else:
        time_display = f"{hours} Hora{'s' if hours != 1 else ''}, {minutes} Minuto{'s' if minutes != 1 else ''}, {seconds} Segundo{'s' if seconds != 1 else ''}"

    # Obtener créditos guardados del usuario (solo los de horas completas anteriores)
    saved_credits = get_user_saved_credits(user_id)

    # NO calcular créditos en tiempo real
    # Los créditos se otorgan únicamente al completar 1 o 2 horas en check_time_limits()

    # Estado
    if time_data['is_active']:
        status = "🟢 Activo"
    elif time_data['is_paused']:
        status = "⏸️ Pausado"
    else:
        status = "⭕ Inactivo"

    # Información del rol basada en el sistema existente
    # Obtener tiempo trabajado hoy
    daily_seconds = tracker.get_daily_time(user_id)
    daily_hours = daily_seconds / 3600

    # Límites diferentes según el rol
    if user_role == 'recluta':
        max_hours = 1
        remaining_hours = max(0, 1 - daily_hours)
    else:
        max_hours = 2
        remaining_hours = max(0, 2 - daily_hours)

    role_limits = {
        'recluta': f'Recluta - Límite: 1 hora diaria (Restante: {remaining_hours:.1f}h)',
        'expediente': f'Expediente - Límite: 2 horas diarias (Restante: {remaining_hours:.1f}h)',
        'silver': f'Silver - Límite: 2 horas diarias (Restante: {remaining_hours:.1f}h)',
        'supervisor': f'Supervisor - Límite: 2 horas diarias (Restante: {remaining_hours:.1f}h)', 
        'alto': f'Alto - Límite: 2 horas diarias (Restante: {remaining_hours:.1f}h)',
        'gold': f'Gold - Límite: 2 horas diarias (Restante: {remaining_hours:.1f}h)'
    }

    embed = discord.Embed(
        title=f"Tu Tiempo - @{interaction.user.display_name}",
        color=0x3498db,
        timestamp=datetime.now()
    )

    # Agregar foto de perfil del usuario
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    embed.add_field(
        name="⏱️ Tiempo Total",
        value=time_display,
        inline=False
    )

    embed.add_field(
        name="📍 Estado", 
        value=status,
        inline=False
    )

    embed.add_field(
        name="💰 Créditos Guardados",
        value=f"{saved_credits} créditos",
        inline=False
    )

    # Mostrar información de créditos pendientes solo si está trabajando
    if time_data and (time_data['is_active'] or time_data['is_paused']):
        today = datetime.now().weekday()
        role_credits = CREDIT_SYSTEM.get(user_role, {})

        # Verificar si es admin bypass para días no permitidos
        member = interaction.guild.get_member(user_id)
        is_admin_bypass = has_admin_bypass(member)
        if is_admin_bypass and today not in ALLOWED_DAYS:
            credits_per_hour = role_credits.get(4, 0)  # Usar créditos del viernes
        else:
            credits_per_hour = role_credits.get(today, 0)

        if credits_per_hour > 0:
            total_hours = total_seconds / 3600
            if total_hours < 1:
                embed.add_field(
                    name="⏳ Próxima Recompensa",
                    value=f"Al completar 1 hora: +{credits_per_hour} créditos",
                    inline=False
                )
            elif total_hours < 2:
                embed.add_field(
                    name="⏳ Próxima Recompensa", 
                    value=f"Al completar 2 horas: +{credits_per_hour} créditos",
                    inline=False
                )

    embed.add_field(
        name="👤 Tu Rol",
        value=role_limits.get(user_role, 'Recluta - Límite: 2 horas'),
        inline=False
    )

    embed.set_footer(text="Tu información personal de tiempo")

    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="ver_tiempos", description="Ver tiempos de usuarios activos (con tiempo corriendo o pausado)")
async def ver_tiempos(interaction: discord.Interaction):

    all_times = tracker.get_all_user_times()

    # Filtrar solo usuarios con tiempo activo o pausado
    active_users = {}
    for user_id, time_data in all_times.items():
        if time_data.get('is_active', False) or time_data.get('is_paused', False):
            active_users[user_id] = time_data

    if not active_users:
        embed = discord.Embed(
            title="📊 Tiempos activos",
            description="No hay usuarios con tiempo activo en este momento.",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed)
        return

    # Preparar datos para paginación
    user_data_list = []
    for user_id, time_data in active_users.items():
        try:
            user = bot.get_user(int(user_id))
            if user:
                member = interaction.guild.get_member(int(user_id))
                user_role = get_user_role(member) if member else 'recluta'
                display_name = member.display_name if member else user.name

                total_seconds = int(time_data['total_seconds'])
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60

                # Formatear tiempo
                if hours > 0:
                    time_display = f"{hours} Hora{'s' if hours != 1 else ''}"
                    if minutes > 0:
                        time_display += f" {minutes} Minuto{'s' if minutes != 1 else ''}"
                    if seconds > 0:
                        time_display += f" {seconds} Segundo{'s' if seconds != 1 else ''}"
                elif minutes > 0:
                    time_display = f"{minutes} Minuto{'s' if minutes != 1 else ''}"
                    if seconds > 0:
                        time_display += f" y {seconds} Segundo{'s' if seconds != 1 else ''}"
                else:
                    time_display = f"{seconds} Segundo{'s' if seconds != 1 else ''}"

                status = "🟢 Activo" if time_data['is_active'] else "⏸️ Pausado"

                user_data_list.append({
                    'name': display_name,
                    'value': f"**Estado:** {status}\n**Tiempo:** {time_display}\n**Rol:** {user_role.title()}"
                })
        except:
            continue

    if not user_data_list:
        embed = discord.Embed(
            title="📊 Tiempos Activos",
            description="No hay usuarios con tiempo activo en este momento.",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed)
        return

    # Crear embeds paginados
    embeds = create_paginated_embeds(user_data_list, "📊 Tiempos Activos", 0x3498db)

    if len(embeds) == 1:
        await interaction.response.send_message(embed=embeds[0])
    else:
        view = PaginationView(embeds)
        await interaction.response.send_message(embed=embeds[0], view=view)

@bot.tree.command(name="cancelar_tiempo", description="Cancelar seguimiento de tiempo de un usuario")
async def cancelar_tiempo(interaction: discord.Interaction, usuario: discord.Member):

    user_id = usuario.id

    if not tracker.is_user_active(user_id) and not tracker.is_user_paused(user_id):
        embed = discord.Embed(
            title="❌ Usuario sin tiempo activo",
            description=f"{usuario.mention} no tiene tiempo activo o pausado.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Obtener tiempo antes de cancelar
    time_data = tracker.get_user_time(user_id)
    total_seconds = int(time_data['total_seconds'])
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Formatear tiempo
    if hours > 0:
        time_display = f"{hours} Hora{'s' if hours != 1 else ''}"
        if minutes > 0:
            time_display += f" {minutes} Minuto{'s' if minutes != 1 else ''}"
        if seconds > 0:
            time_display += f" {seconds} Segundo{'s' if seconds != 1 else ''}"
    elif minutes > 0:
        time_display = f"{minutes} Minuto{'s' if minutes != 1 else ''}"
        if seconds > 0:
            time_display += f" y {seconds} Segundo{'s' if seconds != 1 else ''}"
    else:
        time_display = f"{seconds} Segundo{'s' if seconds != 1 else ''}"

    success = tracker.cancel_time(user_id)

    if success:
        embed = discord.Embed(
            title="❌ Tiempo cancelado",
            description=f"Tiempo cancelado para {usuario.mention}\n"
                       f"Tiempo que tenía: {time_display}",
            color=0xff6b6b
        )
        await interaction.response.send_message(embed=embed)

        # Notificar en canal de cancelaciones
        if NOTIFICATION_CHANNELS.get('cancellations'):
            channel = bot.get_channel(NOTIFICATION_CHANNELS['cancellations'])
            if channel:
                await channel.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Error",
            description="No se pudo cancelar el tiempo.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="paga_alto", description="Ver créditos de usuarios con rol Alto")
async def paga_alto(interaction: discord.Interaction):

    all_times = tracker.get_all_user_times()

    if not all_times:
        embed = discord.Embed(
            title="💰 Pagos Alto",
            description="No hay usuarios con tiempo registrado.",
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(
        title="💰 Pagos - Rol Alto",
        description="Usuarios con rol Alto y sus créditos",
        color=0xE74C3C
    )

    alto_users = []
    for user_id, time_data in all_times.items():
        try:
            user = bot.get_user(int(user_id))
            if user:
                member = interaction.guild.get_member(int(user_id))
                if member:
                    user_role = get_user_role(member)
                    if user_role == 'alto':
                        daily_credits = get_daily_credits(user_role)
                        hours = int(time_data['total_seconds'] // 3600)
                        minutes = int((time_data['total_seconds'] % 3600) // 60)

                        status = "🟢" if time_data['is_active'] else "⏸️" if time_data['is_paused'] else "⭕"

                        alto_users.append({
                            'name': user.display_name,
                            'time': f"{hours}h {minutes}m",
                            'credits': daily_credits,
                            'status': status
                        })
        except:
            continue

    if alto_users:
        for user_data in alto_users:
            embed.add_field(
                name=f"{user_data['status']} {user_data['name']}",
                value=f"**Tiempo:** {user_data['time']}\n**Créditos hoy:** {user_data['credits']}",
                inline=True
            )
    else:
        embed.add_field(
            name="Sin usuarios",
            value="No hay usuarios con rol Alto activos.",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="paga_recluta", description="Ver créditos de usuarios con rol Recluta")
async def paga_recluta(interaction: discord.Interaction):

    all_times = tracker.get_all_user_times()

    if not all_times:
        embed = discord.Embed(
            title="💰 Pagos Recluta",
            description="No hay usuarios con tiempo registrado.",
            color=0x95A5A6
        )
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(
        title="💰 Pagos - Rol Recluta",
        description="Usuarios con rol Recluta y sus créditos",
        color=0x95A5A6
    )

    recluta_users = []
    for user_id, time_data in all_times.items():
        try:
            user = bot.get_user(int(user_id))
            if user:
                member = interaction.guild.get_member(int(user_id))
                if member:
                    user_role = get_user_role(member)
                    if user_role == 'recluta':
                        daily_credits = get_daily_credits(user_role)
                        hours = int(time_data['total_seconds'] // 3600)
                        minutes = int((time_data['total_seconds'] % 3600) // 60)

                        status = "🟢" if time_data['is_active'] else "⏸️" if time_data['is_paused'] else "⭕"

                        recluta_users.append({
                            'name': user.display_name,
                            'time': f"{hours}h {minutes}m",
                            'credits': daily_credits,
                            'status': status
                        })
        except:
            continue

    if recluta_users:
        for user_data in recluta_users:
            embed.add_field(
                name=f"{user_data['status']} {user_data['name']}",
                value=f"**Tiempo:** {user_data['time']}\n**Créditos hoy:** {user_data['credits']}",
                inline=True
            )
    else:
        embed.add_field(
            name="Sin usuarios",
            value="No hay usuarios con rol Recluta activos.",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="paga_gold", description="Ver créditos de usuarios con rol Gold")
async def paga_gold(interaction: discord.Interaction):

    all_times = tracker.get_all_user_times()

    if not all_times:
        embed = discord.Embed(
            title="💰 Pagos Gold",
            description="No hay usuarios con tiempo registrado.",
            color=0xFFD700
        )
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(
        title="💰 Pagos - Rol Gold",
        description="Usuarios con rol Gold y sus créditos",
        color=0xFFD700
    )

    gold_users = []
    for user_id, time_data in all_times.items():
        try:
            user = bot.get_user(int(user_id))
            if user:
                member = interaction.guild.get_member(int(user_id))
                if member:
                    user_role = get_user_role(member)
                    if user_role == 'gold':
                        daily_credits = get_daily_credits(user_role)
                        hours = int(time_data['total_seconds'] // 3600)
                        minutes = int((time_data['total_seconds'] % 3600) // 60)

                        status = "🟢" if time_data['is_active'] else "⏸️" if time_data['is_paused'] else "⭕"

                        gold_users.append({
                            'name': user.display_name,
                            'time': f"{hours}h {minutes}m",
                            'credits': daily_credits,
                            'status': status
                        })
        except:
            continue

    if gold_users:
        for user_data in gold_users:
            embed.add_field(
                name=f"{user_data['status']} {user_data['name']}",
                value=f"**Tiempo:** {user_data['time']}\n**Créditos hoy:** {user_data['credits']}",
                inline=True
            )
    else:
        embed.add_field(
            name="Sin usuarios",
            value="No hay usuarios con rol Gold activos.",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="reset_horas_max", description="Resetar límites diarios, créditos guardados y tiempos totales de todos los usuarios")
async def reset_horas_max(interaction: discord.Interaction):

    try:
        # Obtener total de usuarios afectados antes del reset
        all_users = tracker.get_all_user_times()
        total_users = len(all_users)

        # Resetear tiempos diarios y flags de milestone de todos los usuarios
        tracker.reset_daily_times()

        # Resetear créditos guardados de todos los usuarios
        tracker.clear_all_saved_credits()

        # NUEVO: Resetear tiempos totales de todos los usuarios
        tracker.reset_all_total_times()

        embed = discord.Embed(
            title="🔄 Reset completo realizado",
            description=f"Se ha realizado un reset completo de **{total_users}** usuarios.\n\n"
                       f"**Acciones realizadas:**\n"
                       f"• ✅ Límites diarios reseteados\n"
                       f"• ✅ Flags de 1 hora y 2 horas limpiados\n"
                       f"• ✅ Créditos guardados eliminados\n"
                       f"• ✅ **Tiempos totales reseteados a 0**\n"
                       f"• ✅ Historial de sesiones limpiado\n"
                       f"• ✅ Todos los usuarios pueden volver a trabajar",
            color=0x00ff00
        )

        embed.add_field(
            name="⚠️ Importante",
            value="**TODOS LOS TIEMPOS HAN SIDO ELIMINADOS**\nEste es un reset completo del sistema.",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"No se pudo realizar el reset completo: {e}",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="limpiar_base_datos", description="Limpiar tiempos, pre-registros y créditos de usuarios Recluta y Gold únicamente")
async def limpiar_base_datos(interaction: discord.Interaction):

    # Obtener todos los usuarios para verificar roles
    all_users = tracker.get_all_user_times()
    users_to_clean = []

    for user_id_str in list(all_users.keys()):
        try:
            user_id = int(user_id_str)
            member = interaction.guild.get_member(user_id)
            if member:
                user_role = get_user_role(member)
                if user_role in ['recluta', 'gold']:
                    users_to_clean.append({'id': user_id, 'name': member.display_name, 'role': user_role})
        except:
            continue

    if not users_to_clean:
        embed = discord.Embed(
            title="ℹ️ Sin usuarios para limpiar",
            description="No se encontraron usuarios con roles Recluta o Gold para limpiar.",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Limpiar datos específicos por rol
    cleaned_count = 0

    for user_info in users_to_clean:
        user_id = user_info['id']

        # Limpiar tiempos y pre-registros
        if tracker.reset_user_time(user_id):
            cleaned_count += 1

        # Limpiar créditos guardados
        tracker.clear_user_saved_credits(user_id)

    embed = discord.Embed(
        title="✅ Limpieza selectiva completada",
        description=f"Se limpiaron **{cleaned_count}** usuarios con roles **Recluta** y **Gold**.\n\n"
                   f"**Datos eliminados:**\n"
                   f"• Tiempos registrados\n"
                   f"• Pre-registros activos\n" 
                   f"• Créditos guardados\n"
                   f"• Historial de sesiones",
        color=0x00ff00
    )

    # Mostrar lista de usuarios limpiados
    if len(users_to_clean) <= 10:
        user_list = "\n".join([f"• {user['name']} ({user['role'].title()})" for user in users_to_clean])
        embed.add_field(
            name="👥 Usuarios afectados:",
            value=user_list,
            inline=False
        )
    else:
        embed.add_field(
            name="👥 Usuarios afectados:",
            value=f"{len(users_to_clean)} usuarios con roles Recluta y Gold",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="limpiar_creditos_guardados", description="Limpiar créditos, tiempos y datos de usuarios Expediente, Silver, Supervisor y Alto únicamente")
async def limpiar_creditos_guardados(interaction: discord.Interaction):

    # Obtener todos los usuarios para verificar roles
    all_users = tracker.get_all_user_times()
    users_to_clean = []

    for user_id_str in list(all_users.keys()):
        try:
            user_id = int(user_id_str)
            member = interaction.guild.get_member(user_id)
            if member:
                user_role = get_user_role(member)
                if user_role in ['expediente', 'silver', 'supervisor', 'alto']:
                    users_to_clean.append({'id': user_id, 'name': member.display_name, 'role': user_role})
        except:
            continue

    if not users_to_clean:
        embed = discord.Embed(
            title="ℹ️ Sin usuarios para limpiar",
            description="No se encontraron usuarios con roles Expediente, Silver, Supervisor o Alto para limpiar.",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Limpiar datos específicos por rol
    cleaned_count = 0

    for user_info in users_to_clean:
        user_id = user_info['id']

        # Limpiar tiempos y todos los datos
        if tracker.reset_user_time(user_id):
            cleaned_count += 1

        # Limpiar créditos guardados
        tracker.clear_user_saved_credits(user_id)

    embed = discord.Embed(
        title="✅ Limpieza selectiva completada",
        description=f"Se limpiaron **{cleaned_count}** usuarios con roles **Expediente**, **Silver**, **Supervisor** y **Alto**.\n\n"
                   f"**Datos eliminados:**\n"
                   f"• Créditos guardados\n"
                   f"• Tiempos registrados\n"
                   f"• Pre-registros activos\n"
                   f"• Historial de sesiones\n"
                   f"• Estados de pausa/activo",
        color=0x00ff00
    )

    # Mostrar lista de usuarios limpiados
    if len(users_to_clean) <= 10:
        user_list = "\n".join([f"• {user['name']} ({user['role'].title()})" for user in users_to_clean])
        embed.add_field(
            name="👥 Usuarios afectados:",
            value=user_list,
            inline=False
        )
    else:
        embed.add_field(
            name="👥 Usuarios afectados:",
            value=f"{len(users_to_clean)} usuarios con roles Expediente, Silver, Supervisor y Alto",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# Tarea para verificar tiempo cada minuto
@bot.event
async def setup_hook():
    """Configurar tareas en segundo plano"""
    check_time_limits.start()
    check_auto_start.start()

from discord.ext import tasks

@tasks.loop(minutes=1)
async def check_time_limits():
    """Verificar límites de tiempo cada minuto - optimizado para 80+ usuarios simultáneos"""
    try:
        all_times = tracker.get_all_user_times()
        milestone_channel = bot.get_channel(1385005232685318281)

        if not all_times:
            return

        # Ajuste dinámico del chunk_size basado en la cantidad de usuarios
        total_users = len(all_times)
        if total_users > 60:
            chunk_size = 8  # Chunks más pequeños para 60+ usuarios
        elif total_users > 30:
            chunk_size = 10
        else:
            chunk_size = 15

        user_items = list(all_times.items())

        # Listas para agrupar notificaciones
        completed_1h_users = []
        completed_2h_users = []

        print(f"🔄 Procesando {total_users} usuarios en chunks de {chunk_size}...")

        for i in range(0, len(user_items), chunk_size):
            chunk = user_items[i:i + chunk_size]
            chunk_start_time = datetime.now()

            for user_id_str, time_data in chunk:
                try:
                    if not time_data.get('is_active', False):
                        continue

                    user_id = int(user_id_str)
                    total_seconds = time_data['total_seconds']
                    total_minutes = total_seconds // 60

                    # Verificar milestone de 1 hora
                    if (total_minutes >= 60 and 
                        not tracker.data[user_id_str].get('milestone_1h_completed', False)):

                        # Marcar como completado inmediatamente para evitar duplicados
                        tracker.data[user_id_str]['milestone_1h_completed'] = True

                        user = bot.get_user(user_id)
                        if user:
                            try:
                                guild = milestone_channel.guild if milestone_channel else None
                                member = guild.get_member(user_id) if guild else None
                                user_role = get_user_role(member) if member else 'recluta'

                                today = datetime.now().weekday()
                                role_credits = CREDIT_SYSTEM.get(user_role, {})

                                # Verificar si es admin bypass
                                is_admin_bypass = has_admin_bypass(member)
                                if is_admin_bypass and today not in ALLOWED_DAYS:
                                    credits_per_hour = role_credits.get(4, 0)  # Usar créditos del viernes
                                else:
                                    credits_per_hour = role_credits.get(today, 0)

                                credits_earned = credits_per_hour if credits_per_hour > 0 else 0
                                if credits_earned == int(credits_earned):
                                    credits_earned = int(credits_earned)

                                # Guardar créditos y detener tiempo
                                if credits_earned > 0:
                                    add_credits_to_user(user_id, credits_earned)

                                tracker.stop_tracking(user_id)

                                # Agregar a lista para notificación grupal (incluir rol)
                                completed_1h_users.append((user, credits_earned, user_role))

                            except Exception as role_error:
                                print(f"Error procesando rol de usuario {user_id}: {role_error}")
                                tracker.stop_tracking(user_id)

                    # Verificar milestone de 2 horas
                    elif (total_minutes >= 120 and 
                          not tracker.data[user_id_str].get('milestone_2h_completed', False)):

                        # Marcar como completado inmediatamente para evitar duplicados
                        tracker.data[user_id_str]['milestone_2h_completed'] = True

                        user = bot.get_user(user_id)
                        if user:
                            try:
                                guild = milestone_channel.guild if milestone_channel else None
                                member = guild.get_member(user_id) if guild else None
                                user_role = get_user_role(member) if member else 'recluta'

                                today = datetime.now().weekday()
                                role_credits = CREDIT_SYSTEM.get(user_role, {})

                                # Verificar si es admin bypass
                                is_admin_bypass = has_admin_bypass(member)
                                if is_admin_bypass and today not in ALLOWED_DAYS:
                                    credits_per_hour = role_credits.get(4, 0)  # Usar créditos del viernes
                                else:
                                    credits_per_hour = role_credits.get(today, 0)

                                credits_earned = credits_per_hour if credits_per_hour > 0 else 0
                                total_credits_2h = credits_per_hour * 2 if credits_per_hour > 0 else 0

                                if credits_earned == int(credits_earned):
                                    credits_earned = int(credits_earned)
                                if total_credits_2h == int(total_credits_2h):
                                    total_credits_2h = int(total_credits_2h)

                                # Guardar créditos y detener tiempo
                                if credits_earned > 0:
                                    add_credits_to_user(user_id, credits_earned)

                                tracker.stop_tracking(user_id)

                                # Agregar a lista para notificación grupal (incluir rol)
                                completed_2h_users.append((user, total_credits_2h, user_role))

                            except Exception as role_error:
                                print(f"Error procesando rol de usuario {user_id}: {role_error}")
                                tracker.stop_tracking(user_id)

                except Exception as user_error:
                    print(f"Error procesando usuario {user_id_str}: {user_error}")
                    continue

            # Guardar datos tras cada chunk con retry
            try:
                tracker.save_data()
            except Exception as save_error:
                print(f"Error guardando datos chunk {i//chunk_size + 1}: {save_error}")
                # Retry una vez
                try:
                    await asyncio.sleep(0.5)
                    tracker.save_data()
                except:
                    print(f"Error crítico guardando chunk {i//chunk_size + 1}")

            # Pausa adaptativa entre chunks
            chunk_processing_time = (datetime.now() - chunk_start_time).total_seconds()
            if i + chunk_size < len(user_items):
                # Pausa más larga si el chunk tardó mucho
                if chunk_processing_time > 2:
                    await asyncio.sleep(2.0)
                else:
                    await asyncio.sleep(1.2)

                # Log de progreso para chunks grandes
                if total_users > 50:
                    print(f"📊 Chunk {i//chunk_size + 1}/{(len(user_items)-1)//chunk_size + 1} completado")

        # Enviar notificaciones agrupadas de forma más robusta
        if milestone_channel and (completed_1h_users or completed_2h_users):
            try:
                print(f"📤 Enviando notificaciones: {len(completed_1h_users)} de 1h, {len(completed_2h_users)} de 2h")

                # Notificaciones de 1 hora (máximo 8 por mensaje para evitar límites)
                if completed_1h_users:
                    for i in range(0, len(completed_1h_users), 8):
                        try:
                            batch = completed_1h_users[i:i+8]
                            user_mentions = []
                            for user, credits, user_role in batch:
                                # Mapear rol interno a nombre de cargo
                                role_names = {
                                    'expediente': 'Expediente',
                                    'silver': 'Silver',
                                    'supervisor': 'Supervisor',
                                    'alto': 'Alto',
                                    'gold': 'Gold',
                                    'recluta': 'Recluta'
                                }
                                role_display = role_names.get(user_role, user_role.title())
                                user_mentions.append(f"{user.mention} ({credits} créditos) - Cargo: {role_display}")

                            message = f"🎉 **Usuarios que completaron 1 hora ({i+1}-{min(i+8, len(completed_1h_users))}):**\n" + "\n".join(user_mentions)
                            await milestone_channel.send(message)
                            await asyncio.sleep(1.5)  # Pausa más larga para evitar rate limits
                        except Exception as batch_error:
                            print(f"Error enviando lote 1h {i//8 + 1}: {batch_error}")
                            await asyncio.sleep(2)

                # Notificaciones de 2 horas (máximo 8 por mensaje)
                if completed_2h_users:
                    for i in range(0, len(completed_2h_users), 8):
                        try:
                            batch = completed_2h_users[i:i+8]
                            user_mentions = []
                            for user, credits, user_role in batch:
                                # Mapear rol interno a nombre de cargo
                                role_names = {
                                    'expediente': 'Expediente',
                                    'silver': 'Silver',
                                    'supervisor': 'Supervisor',
                                    'alto': 'Alto',
                                    'gold': 'Gold',
                                    'recluta': 'Recluta'
                                }
                                role_display = role_names.get(user_role, user_role.title())
                                user_mentions.append(f"{user.mention} ({credits} créditos) - Cargo: {role_display}")

                            message = f"🎉 **Usuarios que completaron 2 horas ({i+1}-{min(i+8, len(completed_2h_users))}):**\n" + "\n".join(user_mentions)
                            await milestone_channel.send(message)
                            await asyncio.sleep(1.5)
                        except Exception as batch_error:
                            print(f"Error enviando lote 2h {i//8 + 1}: {batch_error}")
                            await asyncio.sleep(2)

                print(f"✅ Notificaciones enviadas completamente")

            except Exception as notification_error:
                print(f"Error crítico enviando notificaciones: {notification_error}")

    except Exception as e:
        print(f"Error crítico en verificación de límites: {e}")
        # Continuar funcionando incluso si hay errores

@tasks.loop(minutes=1)
async def check_auto_start():
    """Verificar y ejecutar inicio automático - optimizado para 80+ usuarios simultáneos"""
    try:
        # Obtener hora actual en Chile (UTC-3)
        import pytz
        chile_tz = pytz.timezone('America/Santiago')
        chile_time = datetime.now(chile_tz)

        # Verificar si son exactamente las 12:25 PM (hora de prueba)
        if chile_time.hour == 14 and chile_time.minute == 32:
            pre_registered_users = tracker.get_pre_registered_users()

            if pre_registered_users:
                movements_channel = bot.get_channel(NOTIFICATION_CHANNELS.get('movements'))
                total_users = len(pre_registered_users)

                print(f"🚀 Iniciando proceso automático para {total_users} usuarios...")

                # Ajuste dinámico del batch_size según la cantidad de usuarios
                if total_users > 60:
                    batch_size = 10  # Lotes más pequeños para 60+ usuarios
                elif total_users > 30:
                    batch_size = 12
                else:
                    batch_size = 15

                # Usar el método optimizado en lotes de time_tracker
                user_ids = [int(user_id_str) for user_id_str in pre_registered_users.keys()]

                started_users = []
                failed_users = []

                # Procesar en chunks para evitar timeouts
                for i in range(0, len(user_ids), batch_size):
                    batch_ids = user_ids[i:i + batch_size]
                    batch_start_time = datetime.now()

                    try:
                        # Usar método batch optimizado del tracker
                        results = tracker.start_tracking_from_pre_register_batch(batch_ids)

                        # Procesar resultados del batch
                        for user_id in results['success']:
                            user = bot.get_user(user_id)
                            if user:
                                started_users.append(user.mention)
                                # Limpiar información del pre-registro
                                tracker.clear_pre_register_initiator(user_id)
                            else:
                                failed_users.append(f"Usuario {user_id} (no encontrado)")

                        # Agregar fallos del batch
                        for user_id in results['failed']:
                            failed_users.append(f"Usuario {user_id} (error de inicio)")

                        batch_processing_time = (datetime.now() - batch_start_time).total_seconds()

                        # Log de progreso para lotes grandes
                        if total_users > 30:
                            print(f"📊 Lote {i//batch_size + 1}/{(len(user_ids)-1)//batch_size + 1}: {len(results['success'])} iniciados, {len(results['failed'])} fallidos (tiempo: {batch_processing_time:.1f}s)")

                        # Pausa adaptativa entre lotes
                        if i + batch_size < len(user_ids):
                            if batch_processing_time > 3:
                                await asyncio.sleep(1.5)  # Pausa más larga si el lote tardó mucho
                            else:
                                await asyncio.sleep(1.0)

                    except Exception as batch_error:
                        print(f"Error procesando lote {i//batch_size + 1}: {batch_error}")
                        # Procesamiento individual como fallback
                        for user_id in batch_ids:
                            try:
                                success = tracker.start_tracking_from_pre_register(user_id)
                                if success:
                                    user = bot.get_user(user_id)
                                    if user:
                                        started_users.append(user.mention)
                                        tracker.clear_pre_register_initiator(user_id)
                                    else:
                                        failed_users.append(f"Usuario {user_id} (no encontrado)")
                                else:
                                    failed_users.append(f"Usuario {user_id} (error individual)")
                            except Exception as individual_error:
                                print(f"Error individual usuario {user_id}: {individual_error}")
                                failed_users.append(f"Usuario {user_id} (excepción)")

                        await asyncio.sleep(1.5)

                print(f"✅ Proceso automático completado:")
                print(f"   ✅ {len(started_users)} usuarios iniciados correctamente")
                print(f"   ❌ {len(failed_users)} usuarios con errores")

                # Notificación de inicio automático deshabilitada
                # if started_users and movements_channel:
                #     try:
                #         if len(started_users) <= 15:
                #             # Notificación detallada para pocos usuarios
                #             users_text = ", ".join(started_users)
                #             await movements_channel.send(
                #                 f"🤖 **INICIO AUTOMÁTICO - 12:25 PM**\n"
                #                 f"⏰ Usuarios iniciados automáticamente:\n"
                #                 f"{users_text}\n"
                #                 f"📊 Total: {len(started_users)} usuarios"
                #             )
                #         else:
                #             # Mensaje resumen para muchos usuarios + muestra de 10
                #             sample_users = started_users[:10]
                #             sample_text = ", ".join(sample_users)

                #             await movements_channel.send(
                #                 f"🤖 **INICIO AUTOMÁTICO - 12:25 PM**\n"
                #                 f"📊 {len(started_users)} usuarios iniciados automáticamente\n"
                #                 f"❌ {len(failed_users)} usuarios con error\n\n"
                #                 f"👥 Muestra (primeros 10): {sample_text}"
                #                 f"{'...' if len(started_users) > 10 else ''}"
                #             )
                #     except Exception as notification_error:
                #         print(f"Error enviando notificación: {notification_error}")

    except Exception as e:
        print(f"Error crítico en verificación de inicio automático: {e}")
        # Continuar funcionando incluso si hay errores

@check_auto_start.before_loop
async def before_check_auto_start():
    """Esperar a que el bot esté listo antes de iniciar la tarea"""
    await bot.wait_until_ready()

@check_time_limits.before_loop
async def before_check_time_limits():
    """Esperar a que el bot esté listo antes de iniciar la tarea"""
    await bot.wait_until_ready()

# Función principal
if __name__ == "__main__":
    token = get_discord_token()
    if not token:
        print("❌ Error: Token de Discord no encontrado")
        print("Configura tu token en config.json o como variable de entorno DISCORD_BOT_TOKEN")
        exit(1)

    # Verificar que el token tenga el formato correcto
    if not token.startswith(('MTA', 'MTM', 'OTA', 'ODg', 'ODE')):
        print("❌ Error: El token parece ser inválido")
        print("Verifica que copiaste el token completo desde Discord Developer Portal")
        exit(1)

    try:
        print("🔗 Intentando conectar a Discord...")
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        print("❌ Error: Token de Discord inválido")
        print("1. Ve a https://discord.com/developers/applications")
        print("2. Selecciona tu aplicación")
        print("3. Ve a 'Bot' en el menú lateral")
        print("4. Haz clic en 'Reset Token' y copia el nuevo token")
        print("5. Actualiza config.json con el nuevo token")
    except discord.HTTPException as e:
        if e.status == 503:
            print("❌ Error 503: Servicio temporalmente no disponible")
            print("Esto puede ser:")
            print("1. Discord está experimentando problemas - intenta en unos minutos")
            print("2. Tu token ha expirado - resetea el token en Discord Developer Portal")
            print("3. Problemas de red - verifica tu conexión a internet")
        else:
            print(f"❌ Error HTTP {e.status}: {e}")
    except Exception as e:
        print(f"❌ Error ejecutando bot: {e}")
        print("📋 Verifica tu configuración en config.json")