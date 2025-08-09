# binance_arbitrage_bot/monitoring/health_checker.py

import time
import logging
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HealthStatus:
    """Estado de salud de un componente"""
    component: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    last_check: float
    response_time: float

class HealthChecker:
    def __init__(self):
        self.components = {}
        self.check_interval = 30  # 30 segundos
        self.last_full_check = 0
        
    def check_system_health(self) -> Dict[str, HealthStatus]:
        """Verifica la salud completa del sistema"""
        current_time = time.time()
        
        # Solo hacer check completo cada cierto intervalo
        if current_time - self.last_full_check < self.check_interval:
            return self.components
        
        print("🏥 Verificando salud del sistema...")
        
        # 1. API de Binance
        self._check_binance_api()
        
        # 2. Conectividad de red
        self._check_network_connectivity()
        
        # 3. Recursos del sistema
        self._check_system_resources()
        
        # 4. Base de datos (si existe)
        self._check_database_connection()
        
        # 5. Módulos críticos
        self._check_critical_modules()
        
        self.last_full_check = current_time
        
        # Mostrar resumen
        self._show_health_summary()
        
        return self.components
    
    def _check_binance_api(self):
        """Verifica estado de la API de Binance"""
        start_time = time.time()
        
        try:
            from binance_api.client import client
            
            # Test básico de conectividad
            server_time = client.get_server_time()
            response_time = time.time() - start_time
            
            if response_time < 2.0:
                status = 'healthy'
                message = f"API respondiendo en {response_time:.2f}s"
            elif response_time < 5.0:
                status = 'warning'
                message = f"API lenta: {response_time:.2f}s"
            else:
                status = 'critical'
                message = f"API muy lenta: {response_time:.2f}s"
            
            self.components['binance_api'] = HealthStatus(
                'Binance API', status, message, time.time(), response_time
            )
            
        except Exception as e:
            self.components['binance_api'] = HealthStatus(
                'Binance API', 'critical', f"Error: {str(e)}", time.time(), 999.9
            )
    
    def _check_network_connectivity(self):
        """Verifica conectividad de red"""
        import requests
        start_time = time.time()
        
        try:
            response = requests.get('https://api.binance.com/api/v3/ping', timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200 and response_time < 1.0:
                status = 'healthy'
                message = f"Red estable: {response_time:.2f}s"
            elif response.status_code == 200:
                status = 'warning'
                message = f"Red lenta: {response_time:.2f}s"
            else:
                status = 'critical'
                message = f"Error HTTP: {response.status_code}"
            
            self.components['network'] = HealthStatus(
                'Red', status, message, time.time(), response_time
            )
            
        except Exception as e:
            self.components['network'] = HealthStatus(
                'Red', 'critical', f"Sin conectividad: {str(e)}", time.time(), 999.9
            )
    
    def _check_system_resources(self):
        """Verifica recursos del sistema"""
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Determinar estado general
            if cpu_percent < 70 and memory_percent < 80:
                status = 'healthy'
                message = f"CPU: {cpu_percent:.1f}%, RAM: {memory_percent:.1f}%"
            elif cpu_percent < 85 and memory_percent < 90:
                status = 'warning'
                message = f"Recursos altos - CPU: {cpu_percent:.1f}%, RAM: {memory_percent:.1f}%"
            else:
                status = 'critical'
                message = f"Recursos críticos - CPU: {cpu_percent:.1f}%, RAM: {memory_percent:.1f}%"
            
            self.components['system'] = HealthStatus(
                'Sistema', status, message, time.time(), 0.0
            )
            
        except ImportError:
            # psutil no disponible
            self.components['system'] = HealthStatus(
                'Sistema', 'warning', 'psutil no disponible - no se puede monitorear', time.time(), 0.0
            )
        except Exception as e:
            self.components['system'] = HealthStatus(
                'Sistema', 'warning', f"Error monitoreando: {str(e)}", time.time(), 0.0
            )
    
    def _check_database_connection(self):
        """Verifica conexión a base de datos (si existe)"""
        # Por ahora, marcar como no aplicable
        self.components['database'] = HealthStatus(
            'Base de Datos', 'healthy', 'No configurada (archivo local)', time.time(), 0.0
        )
    
    def _check_critical_modules(self):
        """Verifica módulos críticos del bot"""
        modules_to_check = [
            ('strategies.triangular', 'Estrategias'),
            ('binance_api.market_data', 'Datos de Mercado'),
            ('config.settings', 'Configuración'),
        ]
        
        healthy_modules = 0
        total_modules = len(modules_to_check)
        
        for module_name, display_name in modules_to_check:
            try:
                __import__(module_name)
                healthy_modules += 1
            except Exception as e:
                logging.warning(f"Módulo {module_name} tiene problemas: {e}")
        
        if healthy_modules == total_modules:
            status = 'healthy'
            message = f"Todos los módulos operativos ({healthy_modules}/{total_modules})"
        elif healthy_modules > total_modules * 0.7:
            status = 'warning'
            message = f"Algunos módulos con problemas ({healthy_modules}/{total_modules})"
        else:
            status = 'critical'
            message = f"Múltiples módulos fallando ({healthy_modules}/{total_modules})"
        
        self.components['modules'] = HealthStatus(
            'Módulos', status, message, time.time(), 0.0
        )
    
    def _show_health_summary(self):
        """Muestra resumen del estado de salud"""
        healthy_count = len([c for c in self.components.values() if c.status == 'healthy'])
        warning_count = len([c for c in self.components.values() if c.status == 'warning'])
        critical_count = len([c for c in self.components.values() if c.status == 'critical'])
        
        print(f"\n🏥 ESTADO DE SALUD DEL SISTEMA")
        print(f"="*50)
        
        for component in self.components.values():
            if component.status == 'healthy':
                icon = "✅"
            elif component.status == 'warning':
                icon = "⚠️"
            else:
                icon = "❌"
            
            print(f"{icon} {component.component}: {component.message}")
        
        print(f"="*50)
        print(f"📊 Resumen: {healthy_count} saludables, {warning_count} advertencias, {critical_count} críticos")
        
        # Alerta general
        if critical_count > 0:
            print("🚨 ATENCIÓN: Hay componentes críticos que requieren atención")
        elif warning_count > 0:
            print("⚠️ ADVERTENCIA: Hay componentes que requieren monitoreo")
        else:
            print("🎉 SISTEMA SALUDABLE: Todos los componentes funcionan correctamente")
    
    def get_overall_health(self) -> str:
        """Obtiene estado general de salud"""
        if not self.components:
            return 'unknown'
        
        statuses = [c.status for c in self.components.values()]
        
        if 'critical' in statuses:
            return 'critical'
        elif 'warning' in statuses:
            return 'warning'
        else:
            return 'healthy'
    
    def get_health_report(self) -> Dict:
        """Genera reporte detallado de salud"""
        overall = self.get_overall_health()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall,
            'components': {},
            'recommendations': []
        }
        
        for name, status in self.components.items():
            report['components'][name] = {
                'status': status.status,
                'message': status.message,
                'response_time': status.response_time,
                'last_check': status.last_check
            }
        
        # Generar recomendaciones
        if overall == 'critical':
            report['recommendations'].append("Revisar componentes críticos antes de continuar")
        elif overall == 'warning':
            report['recommendations'].append("Monitorear componentes con advertencias")
        
        if any(c.response_time > 3.0 for c in self.components.values()):
            report['recommendations'].append("Verificar conectividad de red")
        
        return report
    
    def is_healthy_for_trading(self) -> bool:
        """Verifica si el sistema está saludable para trading"""
        critical_components = ['binance_api', 'network']
        
        for comp_name in critical_components:
            if comp_name in self.components:
                if self.components[comp_name].status == 'critical':
                    return False
        
        return True

# Instancia global
health_checker = HealthChecker()