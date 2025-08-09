# binance_arbitrage_bot/performance/latency_optimizer.py

import time
import logging
from typing import Dict, List, Callable
from functools import wraps
from collections import deque
import statistics

class LatencyOptimizer:
    def __init__(self):
        self.call_times = {}  # Función -> deque de tiempos
        self.cache = {}       # Cache simple para datos frecuentes
        self.cache_ttl = {}   # TTL para cache
        self.max_samples = 100  # Máximo de muestras por función
        
    def measure_latency(self, func_name: str):
        """Decorador para medir latencia de funciones"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self._record_timing(func_name, execution_time)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_timing(f"{func_name}_error", execution_time)
                    raise e
            return wrapper
        return decorator
    
    def _record_timing(self, func_name: str, execution_time: float):
        """Registra tiempo de ejecución"""
        if func_name not in self.call_times:
            self.call_times[func_name] = deque(maxlen=self.max_samples)
        
        self.call_times[func_name].append(execution_time)
    
    def cached_call(self, cache_key: str, ttl_seconds: int = 60):
        """Decorador para cachear resultados de funciones"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                
                # Verificar si existe en cache y no ha expirado
                if (cache_key in self.cache and 
                    cache_key in self.cache_ttl and
                    current_time < self.cache_ttl[cache_key]):
                    return self.cache[cache_key]
                
                # Ejecutar función y cachear resultado
                result = func(*args, **kwargs)
                self.cache[cache_key] = result
                self.cache_ttl[cache_key] = current_time + ttl_seconds
                
                return result
            return wrapper
        return decorator
    
    def get_performance_stats(self) -> Dict:
        """Obtiene estadísticas de rendimiento"""
        stats = {}
        
        for func_name, times in self.call_times.items():
            if len(times) > 0:
                times_list = list(times)
                stats[func_name] = {
                    'calls': len(times),
                    'avg_time': statistics.mean(times_list),
                    'min_time': min(times_list),
                    'max_time': max(times_list),
                    'median_time': statistics.median(times_list),
                    'std_dev': statistics.stdev(times_list) if len(times_list) > 1 else 0
                }
        
        return stats
    
    def get_slowest_functions(self, top_n: int = 5) -> List[Dict]:
        """Obtiene las funciones más lentas"""
        stats = self.get_performance_stats()
        
        # Ordenar por tiempo promedio
        sorted_funcs = sorted(
            stats.items(), 
            key=lambda x: x[1]['avg_time'], 
            reverse=True
        )
        
        return [
            {
                'function': func_name,
                'avg_time': data['avg_time'],
                'calls': data['calls'],
                'total_time': data['avg_time'] * data['calls']
            }
            for func_name, data in sorted_funcs[:top_n]
        ]
    
    def optimize_api_calls(self):
        """Optimiza llamadas a la API"""
        # Implementar pool de conexiones persistentes
        try:
            import requests
            session = requests.Session()
            session.headers.update({
                'Connection': 'keep-alive',
                'Keep-Alive': 'timeout=5, max=100'
            })
            return session
        except Exception as e:
            logging.warning(f"No se pudo optimizar conexiones: {e}")
            return None
    
    def clear_old_cache(self):
        """Limpia cache expirado"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self.cache_ttl.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.cache_ttl.pop(key, None)
        
        if expired_keys:
            logging.debug(f"🗑️ Cache limpiado: {len(expired_keys)} entradas")
    
    def get_cache_stats(self) -> Dict:
        """Obtiene estadísticas del cache"""
        return {
            'cache_entries': len(self.cache),
            'cache_size_kb': sum(len(str(v)) for v in self.cache.values()) / 1024,
            'hit_potential': len(self.cache)  # Aproximación
        }
    
    def show_performance_report(self):
        """Muestra reporte de rendimiento"""
        print(f"\n⚡ REPORTE DE RENDIMIENTO")
        print(f"="*50)
        
        # Top funciones lentas
        slowest = self.get_slowest_functions(3)
        if slowest:
            print(f"🐌 FUNCIONES MÁS LENTAS:")
            for func in slowest:
                print(f"   {func['function']}: {func['avg_time']:.3f}s avg ({func['calls']} calls)")
        
        # Estadísticas de cache
        cache_stats = self.get_cache_stats()
        print(f"\n💾 CACHE:")
        print(f"   Entradas: {cache_stats['cache_entries']}")
        print(f"   Tamaño: {cache_stats['cache_size_kb']:.1f} KB")
        
        # Recomendaciones
        print(f"\n💡 OPTIMIZACIONES:")
        if slowest and slowest[0]['avg_time'] > 2.0:
            print(f"   - Optimizar función: {slowest[0]['function']}")
        if cache_stats['cache_entries'] < 5:
            print(f"   - Aumentar uso de cache")
        print(f"   - Verificar conectividad de red")
        print(f"="*50)

# Instancia global
latency_optimizer = LatencyOptimizer()

# Decoradores listos para usar
def measure_time(func_name: str):
    return latency_optimizer.measure_latency(func_name)

def cache_result(key: str, ttl: int = 60):
    return latency_optimizer.cached_call(key, ttl)