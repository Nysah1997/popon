
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

class TimeTracker:
    def __init__(self, data_file: str = "user_times.json"):
        self.data_file = data_file
        self.data = self.load_data()
        self.attendance_file = "attendance_data.json"
        self.attendance_data = self.load_attendance_data()
        self.credits_file = "saved_credits.json"
        self.credits_data = self.load_credits_data()

    def load_data(self) -> Dict[str, Any]:
        """Cargar datos desde el archivo JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error cargando datos: {e}")
            return {}

    def save_data(self) -> None:
        """Guardar datos al archivo JSON - optimizado para operaciones masivas"""
        try:
            # Crear backup del archivo anterior
            import shutil
            if os.path.exists(self.data_file):
                backup_file = f"{self.data_file}.backup"
                shutil.copy2(self.data_file, backup_file)
            
            # Guardar con formato compacto para archivos grandes
            with open(self.data_file, 'w', encoding='utf-8') as f:
                if len(self.data) > 50:  # Formato compacto para muchos usuarios
                    json.dump(self.data, f, separators=(',', ':'), ensure_ascii=False)
                else:  # Formato legible para pocos usuarios
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando datos: {e}")
            # Intentar restaurar backup si falla
            try:
                backup_file = f"{self.data_file}.backup"
                if os.path.exists(backup_file):
                    shutil.copy2(backup_file, self.data_file)
                    print("Backup restaurado exitosamente")
            except Exception as backup_error:
                print(f"Error restaurando backup: {backup_error}")

    def pre_register_user(self, user_id: int, user_name: str) -> bool:
        """Pre-registrar usuario para inicio automático"""
        user_id_str = str(user_id)
        current_time = datetime.now().isoformat()

        if user_id_str not in self.data:
            self.data[user_id_str] = {
                'name': user_name,
                'total_time': 0,
                'sessions': [],
                'is_active': False,
                'is_paused': False,
                'pause_count': 0,
                'notified_milestones': [],
                'milestone_completed': False,
                'is_pre_registered': False
            }

        user_data = self.data[user_id_str]

        # Si ya está activo o pre-registrado, no hacer nada
        if user_data.get('is_active', False) or user_data.get('is_pre_registered', False):
            return False

        # Si está pausado, no permitir pre-registro
        if user_data.get('is_paused', False):
            return False

        # Pre-registrar usuario
        user_data['is_pre_registered'] = True
        user_data['pre_register_time'] = current_time
        user_data['name'] = user_name  # Actualizar nombre

        self.save_data()
        return True

    def start_tracking(self, user_id: int, user_name: str) -> bool:
        """Iniciar seguimiento de tiempo para un usuario"""
        user_id_str = str(user_id)
        current_time = datetime.now().isoformat()

        if user_id_str not in self.data:
            self.data[user_id_str] = {
                'name': user_name,
                'total_time': 0,
                'sessions': [],
                'is_active': False,
                'is_paused': False,
                'pause_count': 0,
                'notified_milestones': [],
                'milestone_completed': False,
                'is_pre_registered': False
            }

        user_data = self.data[user_id_str]

        # Si ya está activo, no hacer nada
        if user_data.get('is_active', False):
            return False

        # Si está pausado, no permitir iniciar nuevo tracking
        if user_data.get('is_paused', False):
            return False

        # Limpiar pre-registro si existe
        if user_data.get('is_pre_registered', False):
            user_data['is_pre_registered'] = False
            if 'pre_register_time' in user_data:
                del user_data['pre_register_time']
            if 'pre_register_initiator' in user_data:
                del user_data['pre_register_initiator']

        # Iniciar nueva sesión
        user_data['is_active'] = True
        user_data['is_paused'] = False
        user_data['last_start'] = current_time
        user_data['name'] = user_name  # Actualizar nombre

        self.save_data()
        return True

    def start_tracking_from_pre_register(self, user_id: int) -> bool:
        """Iniciar seguimiento desde pre-registro (para inicio automático a las 8 PM)"""
        user_id_str = str(user_id)
        current_time = datetime.now().isoformat()

        if user_id_str not in self.data:
            return False

        user_data = self.data[user_id_str]

        # Solo funciona si está pre-registrado
        if not user_data.get('is_pre_registered', False):
            return False

        # Si ya está activo, no hacer nada
        if user_data.get('is_active', False):
            return False

        # Iniciar desde pre-registro
        user_data['is_active'] = True
        user_data['is_paused'] = False
        user_data['is_pre_registered'] = False
        user_data['last_start'] = current_time

        # Limpiar pre-registro
        if 'pre_register_time' in user_data:
            del user_data['pre_register_time']
        
        # Limpiar información del admin pre-registrador
        if 'pre_register_initiator' in user_data:
            del user_data['pre_register_initiator']

        self.save_data()
        return True

    def get_pre_registered_users(self) -> Dict[str, Any]:
        """Obtener usuarios pre-registrados"""
        pre_registered = {}
        for user_id_str, data in self.data.items():
            if data.get('is_pre_registered', False):
                pre_registered[user_id_str] = data
        return pre_registered

    def stop_tracking(self, user_id: int) -> bool:
        """Detener seguimiento de tiempo para un usuario"""
        user_id_str = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        if user_id_str not in self.data:
            return False

        user_data = self.data[user_id_str]

        if not user_data.get('is_active', False):
            return False

        # Calcular tiempo de sesión
        session_time = 0
        if user_data.get('last_start'):
            session_start = datetime.fromisoformat(user_data['last_start'])
            session_time = (datetime.now() - session_start).total_seconds()
            
            # Añadir tiempo de sesión al total
            user_data['total_time'] = user_data.get('total_time', 0) + session_time
            
            # Actualizar tiempo diario
            if 'daily_times' not in user_data:
                user_data['daily_times'] = {}
            user_data['daily_times'][today] = user_data['daily_times'].get(today, 0) + session_time

        # Marcar como inactivo
        user_data['is_active'] = False
        user_data['is_paused'] = False

        # Agregar sesión al historial
        if 'sessions' not in user_data:
            user_data['sessions'] = []

        session_record = {
            'start': user_data.get('last_start'),
            'end': datetime.now().isoformat(),
            'duration': session_time,
            'date': today
        }
        user_data['sessions'].append(session_record)

        self.save_data()
        return True

    def pause_tracking(self, user_id: int) -> bool:
        """Pausar seguimiento de tiempo para un usuario"""
        user_id_str = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        if user_id_str not in self.data:
            return False

        user_data = self.data[user_id_str]

        if not user_data.get('is_active', False):
            return False

        # Calcular tiempo de sesión actual y añadirlo al total y diario
        if user_data.get('last_start'):
            session_start = datetime.fromisoformat(user_data['last_start'])
            session_time = (datetime.now() - session_start).total_seconds()
            user_data['total_time'] = user_data.get('total_time', 0) + session_time
            
            # Actualizar tiempo diario
            if 'daily_times' not in user_data:
                user_data['daily_times'] = {}
            user_data['daily_times'][today] = user_data['daily_times'].get(today, 0) + session_time

        # Marcar como pausado
        user_data['is_active'] = False
        user_data['is_paused'] = True
        user_data['pause_start'] = datetime.now().isoformat()
        user_data['pause_count'] = user_data.get('pause_count', 0) + 1

        self.save_data()
        return True

    def resume_tracking(self, user_id: int) -> bool:
        """Reanudar seguimiento de tiempo para un usuario pausado"""
        user_id_str = str(user_id)

        if user_id_str not in self.data:
            return False

        user_data = self.data[user_id_str]

        if not user_data.get('is_paused', False):
            return False

        # Reanudar seguimiento
        user_data['is_active'] = True
        user_data['is_paused'] = False
        user_data['last_start'] = datetime.now().isoformat()

        # Limpiar pause_start
        if 'pause_start' in user_data:
            del user_data['pause_start']

        self.save_data()
        return True

    def get_total_time(self, user_id: int) -> float:
        """Obtener tiempo total acumulado de un usuario"""
        user_id_str = str(user_id)

        if user_id_str not in self.data:
            return 0.0

        user_data = self.data[user_id_str]
        total_time = user_data.get('total_time', 0)

        # Si está activo, añadir tiempo de sesión actual
        if user_data.get('is_active', False) and user_data.get('last_start'):
            session_start = datetime.fromisoformat(user_data['last_start'])
            current_session_time = (datetime.now() - session_start).total_seconds()
            total_time += current_session_time

        return total_time

    def get_daily_time(self, user_id: int) -> float:
        """Obtener tiempo acumulado del día actual de un usuario"""
        user_id_str = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        if user_id_str not in self.data:
            return 0.0

        user_data = self.data[user_id_str]
        
        # Inicializar registro diario si no existe
        if 'daily_times' not in user_data:
            user_data['daily_times'] = {}
        
        daily_time = user_data['daily_times'].get(today, 0)

        # Si está activo hoy, añadir tiempo de sesión actual
        if (user_data.get('is_active', False) and 
            user_data.get('last_start') and 
            user_data.get('last_start').startswith(today)):
            
            session_start = datetime.fromisoformat(user_data['last_start'])
            current_session_time = (datetime.now() - session_start).total_seconds()
            daily_time += current_session_time

        return daily_time

    def get_daily_history(self, user_id: int, days: int = 7) -> Dict[str, float]:
        """Obtener historial de tiempo diario de los últimos N días"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.data:
            return {}
        
        user_data = self.data[user_id_str]
        daily_times = user_data.get('daily_times', {})
        
        # Generar fechas de los últimos N días
        history = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            history[date] = daily_times.get(date, 0)
        
        return history

    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener datos completos de un usuario"""
        user_id_str = str(user_id)
        return self.data.get(user_id_str)

    def get_all_tracked_users(self) -> Dict[str, Any]:
        """Obtener todos los usuarios con seguimiento"""
        return self.data.copy()

    def reset_user_time(self, user_id: int) -> bool:
        """Reiniciar tiempo de un usuario a cero"""
        user_id_str = str(user_id)

        if user_id_str not in self.data:
            return False

        user_data = self.data[user_id_str]
        user_data['total_time'] = 0
        user_data['is_active'] = False
        user_data['is_paused'] = False
        user_data['pause_count'] = 0
        user_data['sessions'] = []
        user_data['notified_milestones'] = []
        user_data['milestone_completed'] = False
        user_data['is_pre_registered'] = False

        # Limpiar campos de seguimiento
        if 'last_start' in user_data:
            del user_data['last_start']
        if 'pause_start' in user_data:
            del user_data['pause_start']
        if 'pre_register_time' in user_data:
            del user_data['pre_register_time']

        self.save_data()
        return True

    def reset_all_user_times(self) -> int:
        """Reiniciar todos los tiempos de usuarios"""
        count = 0
        for user_id_str in list(self.data.keys()):
            user_id = int(user_id_str)
            if self.reset_user_time(user_id):
                count += 1
        return count

    def cancel_user_tracking(self, user_id: int) -> bool:
        """Cancelar completamente el seguimiento de un usuario"""
        user_id_str = str(user_id)

        if user_id_str not in self.data:
            return False

        # Eliminar completamente al usuario
        del self.data[user_id_str]
        self.save_data()
        return True

    def clear_all_data(self) -> bool:
        """Limpiar completamente todos los datos"""
        try:
            self.data = {}
            self.save_data()
            return True
        except Exception as e:
            print(f"Error limpiando datos: {e}")
            return False

    def add_minutes(self, user_id: int, user_name: str, minutes: int) -> bool:
        """Añadir minutos al tiempo de un usuario (solo si ya existe)"""
        user_id_str = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        # Solo permitir si el usuario ya existe
        if user_id_str not in self.data:
            return False

        user_data = self.data[user_id_str]
        seconds_to_add = minutes * 60
        user_data['total_time'] = user_data.get('total_time', 0) + seconds_to_add
        user_data['name'] = user_name  # Actualizar nombre

        # También agregar al tiempo diario para que se refleje en límites diarios
        if 'daily_times' not in user_data:
            user_data['daily_times'] = {}
        user_data['daily_times'][today] = user_data['daily_times'].get(today, 0) + seconds_to_add

        self.save_data()
        return True

    def subtract_minutes(self, user_id: int, minutes: int) -> bool:
        """Restar minutos del tiempo de un usuario"""
        user_id_str = str(user_id)

        if user_id_str not in self.data:
            return False

        user_data = self.data[user_id_str]
        current_time = user_data.get('total_time', 0)
        new_time = max(0, current_time - (minutes * 60))
        user_data['total_time'] = new_time

        self.save_data()
        return True

    def get_pause_count(self, user_id: int) -> int:
        """Obtener número de pausas de un usuario"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            return 0
        return self.data[user_id_str].get('pause_count', 0)

    def get_paused_duration(self, user_id: int) -> float:
        """Obtener duración pausada actual de un usuario"""
        user_id_str = str(user_id)

        if user_id_str not in self.data:
            return 0.0

        user_data = self.data[user_id_str]

        if not user_data.get('is_paused', False) or not user_data.get('pause_start'):
            return 0.0

        pause_start = datetime.fromisoformat(user_data['pause_start'])
        return (datetime.now() - pause_start).total_seconds()

    def format_time_human(self, seconds: float) -> str:
        """Formatear tiempo en formato humano legible"""
        if seconds < 0:
            return "0 Segundos"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours} Hora{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} Minuto{'s' if minutes != 1 else ''}")
        if secs > 0 or not parts:  # Mostrar segundos si no hay otras partes
            parts.append(f"{secs} Segundo{'s' if secs != 1 else ''}")

        return ", ".join(parts)

    def load_attendance_data(self) -> Dict[str, Any]:
        """Cargar datos de asistencias desde archivo JSON"""
        try:
            if os.path.exists(self.attendance_file):
                with open(self.attendance_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error cargando datos de asistencias: {e}")
            return {}

    def save_attendance_data(self) -> None:
        """Guardar datos de asistencias al archivo JSON"""
        try:
            with open(self.attendance_file, 'w', encoding='utf-8') as f:
                json.dump(self.attendance_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando datos de asistencias: {e}")

    def add_manual_attendance(self, admin_id: int, admin_name: str, quantity: int) -> bool:
        """Agregar asistencias manualmente (para comando /sumar_asistencias) - hasta 15 asistencias sin límites"""
        admin_id_str = str(admin_id)
        
        # Verificar que la cantidad esté entre 1 y 15
        if quantity < 1 or quantity > 15:
            return False
        
        # Inicializar datos del admin si no existen
        if admin_id_str not in self.attendance_data:
            self.attendance_data[admin_id_str] = {
                'name': admin_name,
                'daily_attendance': {},
                'total_attendance': 0,
                'manual_weekly_attendance': 0  # Nuevo campo para asistencias manuales semanales
            }
        
        admin_data = self.attendance_data[admin_id_str]
        admin_data['name'] = admin_name  # Actualizar nombre
        
        # Inicializar campo manual semanal si no existe
        if 'manual_weekly_attendance' not in admin_data:
            admin_data['manual_weekly_attendance'] = 0
        
        # Solo agregar al total y al contador semanal manual (NO al diario)
        admin_data['manual_weekly_attendance'] += quantity
        admin_data['total_attendance'] = admin_data.get('total_attendance', 0) + quantity
        self.save_attendance_data()
        return True

    def add_daily_manual_attendance(self, admin_id: int, admin_name: str, quantity: int) -> bool:
        """Agregar asistencias diarias manualmente (para comando /agregar_asistencias_diarias) - máximo 3 por día"""
        admin_id_str = str(admin_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Verificar que la cantidad esté entre 1 y 3
        if quantity < 1 or quantity > 3:
            return False
        
        # Inicializar datos del admin si no existen
        if admin_id_str not in self.attendance_data:
            self.attendance_data[admin_id_str] = {
                'name': admin_name,
                'daily_attendance': {},
                'total_attendance': 0,
                'manual_weekly_attendance': 0
            }
        
        admin_data = self.attendance_data[admin_id_str]
        admin_data['name'] = admin_name  # Actualizar nombre
        
        # Inicializar día si no existe
        if today not in admin_data['daily_attendance']:
            admin_data['daily_attendance'][today] = 0
        
        # Verificar que no exceda 3 asistencias diarias
        if admin_data['daily_attendance'][today] + quantity > 3:
            return False
        
        # SOLO agregar a diarias y totales
        # NO agregar a manual_weekly_attendance porque get_weekly_attendance ya cuenta las diarias
        admin_data['daily_attendance'][today] += quantity
        admin_data['total_attendance'] = admin_data.get('total_attendance', 0) + quantity
        
        # Inicializar campo manual semanal si no existe (pero no sumar aquí)
        if 'manual_weekly_attendance' not in admin_data:
            admin_data['manual_weekly_attendance'] = 0
        
        self.save_attendance_data()
        return True

    def add_attendance(self, admin_id: int, admin_name: str, attendances_to_add: int = 1) -> bool:
        """Agregar asistencia para un administrador (por defecto 1 asistencia)"""
        admin_id_str = str(admin_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Verificar si puede recibir asistencias diarias (no ha transferido hoy)
        if not self.can_receive_daily_attendance(admin_id):
            return False
        
        # Inicializar datos del admin si no existen
        if admin_id_str not in self.attendance_data:
            self.attendance_data[admin_id_str] = {
                'name': admin_name,
                'daily_attendance': {},
                'total_attendance': 0
            }
        
        admin_data = self.attendance_data[admin_id_str]
        admin_data['name'] = admin_name  # Actualizar nombre
        
        # Inicializar día si no existe
        if today not in admin_data['daily_attendance']:
            admin_data['daily_attendance'][today] = 0
        
        # Verificar límite diario (máximo 3 por día)
        if admin_data['daily_attendance'][today] >= 3:
            return False
        
        # Verificar límite semanal (máximo 15 por semana)
        weekly_count = self.get_weekly_attendance(admin_id)
        if weekly_count >= 15:
            return False
        
        # Verificar que no exceda el límite diario
        if admin_data['daily_attendance'][today] + attendances_to_add > 3:
            attendances_to_add = 3 - admin_data['daily_attendance'][today]
        
        # Verificar que no exceda el límite semanal
        if weekly_count + attendances_to_add > 15:
            attendances_to_add = 15 - weekly_count
        
        if attendances_to_add > 0:
            admin_data['daily_attendance'][today] += attendances_to_add
            admin_data['total_attendance'] = admin_data.get('total_attendance', 0) + attendances_to_add
            self.save_attendance_data()
            return True
        
        return False

    def get_daily_attendance(self, admin_id: int) -> int:
        """Obtener asistencias del día actual"""
        admin_id_str = str(admin_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if admin_id_str not in self.attendance_data:
            return 0
        
        return self.attendance_data[admin_id_str]['daily_attendance'].get(today, 0)

    def get_weekly_attendance(self, admin_id: int) -> int:
        """Obtener asistencias de la semana actual"""
        admin_id_str = str(admin_id)
        
        if admin_id_str not in self.attendance_data:
            return 0
        
        admin_data = self.attendance_data[admin_id_str]
        
        # Calcular fechas de la semana actual (lunes a viernes)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        
        weekly_count = 0
        for i in range(5):  # Solo 5 días: lunes a viernes
            date = (start_of_week + timedelta(days=i)).strftime("%Y-%m-%d")
            weekly_count += admin_data['daily_attendance'].get(date, 0)
        
        # Agregar asistencias manuales semanales
        weekly_count += admin_data.get('manual_weekly_attendance', 0)
        
        return weekly_count

    def get_total_attendance(self, admin_id: int) -> int:
        """Obtener total de asistencias"""
        admin_id_str = str(admin_id)
        
        if admin_id_str not in self.attendance_data:
            return 0
        
        return self.attendance_data[admin_id_str].get('total_attendance', 0)

    def get_attendance_info(self, admin_id: int) -> Dict[str, int]:
        """Obtener información completa de asistencias"""
        return {
            'daily': self.get_daily_attendance(admin_id),
            'weekly': self.get_weekly_attendance(admin_id),
            'total': self.get_total_attendance(admin_id)
        }

    def set_time_initiator(self, user_id: int, admin_id: int, admin_name: str) -> None:
        """Registrar quién inició el tiempo para un usuario"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            self.data[user_id_str]['time_initiator'] = {
                'admin_id': admin_id,
                'admin_name': admin_name,
                'timestamp': datetime.now().isoformat()
            }
            self.save_data()

    def get_time_initiator(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener información de quién inició el tiempo para un usuario"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            return self.data[user_id_str].get('time_initiator')
        return None

    def clear_time_initiator(self, user_id: int) -> None:
        """Limpiar información del iniciador del tiempo"""
        user_id_str = str(user_id)
        if user_id_str in self.data and 'time_initiator' in self.data[user_id_str]:
            del self.data[user_id_str]['time_initiator']
            self.save_data()

    def reset_weekly_manual_attendances(self) -> None:
        """Resetear solo las asistencias manuales semanales (para nueva semana)"""
        for admin_id_str in self.attendance_data:
            self.attendance_data[admin_id_str]['manual_weekly_attendance'] = 0
        self.save_attendance_data()

    def reset_daily_transfer_blocks(self) -> None:
        """Resetear bloqueos de transferencia diarios (para nuevo día a las 00:00)"""
        for admin_id_str in self.attendance_data:
            admin_data = self.attendance_data[admin_id_str]
            # Limpiar marcadores de transferencia del día anterior
            if 'transferred_today' in admin_data:
                del admin_data['transferred_today']
            if 'transfer_date' in admin_data:
                del admin_data['transfer_date']
        self.save_attendance_data()

    def transfer_attendances(self, from_user_id: int, to_user_id: int, to_user_name: str, quantity: int) -> bool:
        """Transferir asistencias de un usuario a otro - CEDE asistencias diarias del día actual"""
        from_user_id_str = str(from_user_id)
        to_user_id_str = str(to_user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Verificar que el transferidor tenga datos
        if from_user_id_str not in self.attendance_data:
            return False
        
        from_user_data = self.attendance_data[from_user_id_str]
        
        # Verificar que tenga exactamente 3 asistencias diarias
        daily_count = self.get_daily_attendance(from_user_id)
        if daily_count != 3:
            return False
        
        # Verificar que tenga suficientes asistencias diarias para transferir
        if daily_count < quantity:
            return False
        
        # Inicializar datos del receptor si no existen
        if to_user_id_str not in self.attendance_data:
            self.attendance_data[to_user_id_str] = {
                'name': to_user_name,
                'daily_attendance': {},
                'total_attendance': 0,
                'manual_weekly_attendance': 0
            }
        
        to_user_data = self.attendance_data[to_user_id_str]
        to_user_data['name'] = to_user_name  # Actualizar nombre
        
        # Inicializar día del receptor si no existe
        if today not in to_user_data['daily_attendance']:
            to_user_data['daily_attendance'][today] = 0
        
        # Verificar límites del receptor
        if to_user_data['daily_attendance'][today] + quantity > 3:
            return False
        
        to_weekly_count = self.get_weekly_attendance(to_user_id)
        if to_weekly_count + quantity > 15:
            return False
        
        # LÓGICA CORRECTA FINAL:
        # 1. Restar del transferidor (diarias, semanales Y totales - es la misma asistencia)
        from_user_data['daily_attendance'][today] -= quantity
        from_user_data['total_attendance'] = max(0, from_user_data.get('total_attendance', 0) - quantity)
        
        # 2. Agregar al receptor (diario y total solamente)
        # NO agregar a manual_weekly_attendance porque son asistencias diarias transferidas
        # que ya se contarán automáticamente en get_weekly_attendance()
        to_user_data['daily_attendance'][today] += quantity
        
        # Inicializar manual_weekly_attendance si no existe (pero no sumar aquí)
        if 'manual_weekly_attendance' not in to_user_data:
            to_user_data['manual_weekly_attendance'] = 0
        
        to_user_data['total_attendance'] = to_user_data.get('total_attendance', 0) + quantity
        
        # 3. Marcar al transferidor como "no puede obtener más asistencias hoy"
        from_user_data['transferred_today'] = True
        from_user_data['transfer_date'] = today
        
        self.save_attendance_data()
        return True

    def can_receive_daily_attendance(self, user_id: int) -> bool:
        """Verificar si un usuario puede recibir asistencias diarias (no ha transferido hoy)"""
        user_id_str = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user_id_str not in self.attendance_data:
            return True
        
        user_data = self.attendance_data[user_id_str]
        
        # Verificar si transfirió hoy
        if user_data.get('transferred_today', False):
            transfer_date = user_data.get('transfer_date', '')
            if transfer_date == today:
                return False
        
        return True

    def reset_all_attendances(self) -> bool:
        """Resetear completamente todas las asistencias de todos los usuarios"""
        try:
            self.attendance_data = {}
            self.save_attendance_data()
            return True
        except Exception as e:
            print(f"Error reseteando asistencias: {e}")
            return False

    def set_pre_register_initiator(self, user_id: int, admin_id: int, admin_name: str) -> None:
        """Registrar quién hizo el pre-registro para un usuario"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            self.data[user_id_str]['pre_register_initiator'] = {
                'admin_id': admin_id,
                'admin_name': admin_name,
                'timestamp': datetime.now().isoformat()
            }
            self.save_data()

    def get_pre_register_initiator(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener información de quién hizo el pre-registro para un usuario"""
        user_id_str = str(user_id)
        if user_id_str in self.data:
            return self.data[user_id_str].get('pre_register_initiator')
        return None

    def clear_pre_register_initiator(self, user_id: int) -> None:
        """Limpiar información del admin que hizo el pre-registro"""
        user_id_str = str(user_id)
        if user_id_str in self.data and 'pre_register_initiator' in self.data[user_id_str]:
            del self.data[user_id_str]['pre_register_initiator']
            # No guardar inmediatamente para permitir operaciones en lote

    def batch_save_data(self) -> None:
        """Guardar datos optimizado para operaciones en lote"""
        self.save_data()

    def start_tracking_from_pre_register_batch(self, user_ids: list) -> dict:
        """Iniciar seguimiento desde pre-registro para múltiples usuarios (optimizado)"""
        results = {'success': [], 'failed': []}
        current_time = datetime.now().isoformat()

        for user_id in user_ids:
            try:
                user_id_str = str(user_id)
                
                if user_id_str not in self.data:
                    results['failed'].append(user_id)
                    continue

                user_data = self.data[user_id_str]

                # Solo funciona si está pre-registrado
                if not user_data.get('is_pre_registered', False):
                    results['failed'].append(user_id)
                    continue

                # Si ya está activo, no hacer nada
                if user_data.get('is_active', False):
                    results['failed'].append(user_id)
                    continue

                # Iniciar desde pre-registro
                user_data['is_active'] = True
                user_data['is_paused'] = False
                user_data['is_pre_registered'] = False
                user_data['last_start'] = current_time

                # Limpiar pre-registro
                if 'pre_register_time' in user_data:
                    del user_data['pre_register_time']
                
                # Limpiar información del admin pre-registrador
                if 'pre_register_initiator' in user_data:
                    del user_data['pre_register_initiator']

                results['success'].append(user_id)

            except Exception as e:
                print(f"Error procesando usuario {user_id}: {e}")
                results['failed'].append(user_id)

        # Guardar una sola vez al final
        self.save_data()
        return results

    def is_user_active(self, user_id: int) -> bool:
        """Verificar si un usuario tiene tiempo activo"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            return False
        return self.data[user_id_str].get('is_active', False)

    def is_user_paused(self, user_id: int) -> bool:
        """Verificar si un usuario tiene tiempo pausado"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            return False
        return self.data[user_id_str].get('is_paused', False)

    def start_time(self, user_id: int) -> bool:
        """Iniciar tiempo para un usuario (alias de start_tracking)"""
        user = self.data.get(str(user_id), {})
        user_name = user.get('name', f'Usuario_{user_id}')
        return self.start_tracking(user_id, user_name)

    def pause_time(self, user_id: int) -> bool:
        """Pausar tiempo para un usuario (alias de pause_tracking)"""
        return self.pause_tracking(user_id)

    def unpause_time(self, user_id: int) -> bool:
        """Reanudar tiempo para un usuario (alias de resume_tracking)"""
        return self.resume_tracking(user_id)

    def cancel_time(self, user_id: int) -> bool:
        """Cancelar tiempo para un usuario (alias de stop_tracking)"""
        return self.stop_tracking(user_id)

    def get_user_time(self, user_id: int) -> dict:
        """Obtener información de tiempo de un usuario"""
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            return {}
        
        user_data = self.data[user_id_str].copy()
        total_seconds = self.get_total_time(user_id)
        
        return {
            'total_seconds': total_seconds,
            'is_active': user_data.get('is_active', False),
            'is_paused': user_data.get('is_paused', False),
            'start_time': user_data.get('last_start'),
            'pause_count': user_data.get('pause_count', 0)
        }

    def get_all_user_times(self) -> dict:
        """Obtener tiempos de todos los usuarios"""
        result = {}
        for user_id_str in self.data:
            user_id = int(user_id_str)
            result[user_id_str] = self.get_user_time(user_id)
        return result

    def load_credits_data(self) -> Dict[str, Any]:
        """Cargar datos de créditos guardados desde archivo JSON"""
        try:
            if os.path.exists(self.credits_file):
                with open(self.credits_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error cargando datos de créditos: {e}")
            return {}

    def save_credits_data(self) -> None:
        """Guardar datos de créditos al archivo JSON"""
        try:
            with open(self.credits_file, 'w', encoding='utf-8') as f:
                json.dump(self.credits_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando datos de créditos: {e}")

    def get_saved_credits(self, user_id: int) -> int:
        """Obtener créditos guardados de un usuario"""
        user_id_str = str(user_id)
        return self.credits_data.get(user_id_str, {}).get('total_credits', 0)

    def add_saved_credits(self, user_id: int, credits: int) -> bool:
        """Agregar créditos guardados a un usuario"""
        try:
            user_id_str = str(user_id)
            if user_id_str not in self.credits_data:
                self.credits_data[user_id_str] = {
                    'total_credits': 0,
                    'daily_credits_history': {}
                }
            
            self.credits_data[user_id_str]['total_credits'] += credits
            
            # Registrar en historial diario
            today = datetime.now().strftime("%Y-%m-%d")
            if 'daily_credits_history' not in self.credits_data[user_id_str]:
                self.credits_data[user_id_str]['daily_credits_history'] = {}
            
            daily_history = self.credits_data[user_id_str]['daily_credits_history']
            daily_history[today] = daily_history.get(today, 0) + credits
            
            self.save_credits_data()
            return True
        except Exception as e:
            print(f"Error agregando créditos: {e}")
            return False

    def clear_user_saved_credits(self, user_id: int) -> bool:
        """Limpiar créditos guardados de un usuario específico"""
        try:
            user_id_str = str(user_id)
            if user_id_str in self.credits_data:
                del self.credits_data[user_id_str]
                self.save_credits_data()
            return True
        except Exception as e:
            print(f"Error limpiando créditos del usuario {user_id}: {e}")
            return False

    def clear_all_saved_credits(self) -> bool:
        """Limpiar todos los créditos guardados de todos los usuarios"""
        try:
            self.credits_data = {}
            self.save_credits_data()
            return True
        except Exception as e:
            print(f"Error limpiando créditos guardados: {e}")
            return False

    def reset_daily_times(self) -> None:
        """Resetear tiempos diarios de todos los usuarios para permitir trabajar nuevamente"""
        today = datetime.now().strftime("%Y-%m-%d")
        for user_id_str in self.data:
            user_data = self.data[user_id_str]
            
            # Inicializar daily_times si no existe
            if 'daily_times' not in user_data:
                user_data['daily_times'] = {}
            
            # RESETEAR el tiempo diario de hoy a 0 para permitir trabajar nuevamente
            user_data['daily_times'][today] = 0
            
            # Resetear flags de milestones completados para permitir ganar créditos nuevamente
            if 'milestone_1h_completed' in user_data:
                del user_data['milestone_1h_completed']
            if 'milestone_2h_completed' in user_data:
                del user_data['milestone_2h_completed']
                
        self.save_data()

    def reset_all_total_times(self) -> None:
        """Resetear tiempos totales de todos los usuarios a 0"""
        for user_id_str in self.data:
            user_data = self.data[user_id_str]
            
            # Resetear tiempo total a 0
            user_data['total_time'] = 0
            
            # Limpiar historial de sesiones
            user_data['sessions'] = []
            
            # Limpiar historial de tiempos diarios
            user_data['daily_times'] = {}
            
        self.save_data()
