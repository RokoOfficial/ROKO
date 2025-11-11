"""
Ultra Performance Monitor - Monitoramento avançado de performance do sistema HMP.
"""

import logging
import time
from typing import Dict, Any, List
from collections import deque
from threading import Lock

class UltraPerformanceMonitor:
    """
    Monitor ultra-otimizado de performance para o sistema HMP.
    Rastreia métricas em tempo real com overhead mínimo.
    """

    def __init__(self):
        self.execution_history = deque(maxlen=1000)
        self.performance_stats = {
            'total_executions': 0,
            'cache_hits': 0,
            'average_execution_time': 0.0,
            'peak_speedup': 0.0,
            'total_workers_used': 0,
            'parallel_executions': 0
        }
        self.lock = Lock()
        self.start_time = time.time()

        logging.info("🚀 Ultra Performance Monitor inicializado")

    def record_execution(self, execution_time: float, workers_used: int = 1, 
                        from_cache: bool = False, parallel_groups: int = 0) -> Dict[str, Any]:
        """
        Registra uma execução e calcula métricas de performance.
        """
        with self.lock:
            self.performance_stats['total_executions'] += 1

            if from_cache:
                self.performance_stats['cache_hits'] += 1

            # Calcular speedup estimado
            estimated_sequential_time = execution_time * workers_used if workers_used > 1 else execution_time
            speedup = estimated_sequential_time / execution_time if execution_time > 0 else 1.0

            # Atualizar peak speedup
            if speedup > self.performance_stats['peak_speedup']:
                self.performance_stats['peak_speedup'] = speedup

            # Atualizar médias
            self.performance_stats['total_workers_used'] += workers_used
            if parallel_groups > 0:
                self.performance_stats['parallel_executions'] += 1

            # Calcular média de tempo de execução
            current_avg = self.performance_stats['average_execution_time']
            total_execs = self.performance_stats['total_executions']
            self.performance_stats['average_execution_time'] = (
                (current_avg * (total_execs - 1) + execution_time) / total_execs
            )

            # Adicionar ao histórico
            execution_record = {
                'timestamp': time.time(),
                'execution_time': execution_time,
                'workers_used': workers_used,
                'from_cache': from_cache,
                'speedup': speedup,
                'parallel_groups': parallel_groups
            }
            self.execution_history.append(execution_record)

            return {
                'execution_time': execution_time,
                'workers_used': workers_used,
                'estimated_speedup': speedup,
                'from_cache': from_cache,
                'total_executions': total_execs
            }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Retorna resumo de performance atual."""
        with self.lock:
            uptime = time.time() - self.start_time
            cache_hit_ratio = (
                self.performance_stats['cache_hits'] / self.performance_stats['total_executions']
                if self.performance_stats['total_executions'] > 0 else 0.0
            )

            avg_workers = (
                self.performance_stats['total_workers_used'] / self.performance_stats['total_executions']
                if self.performance_stats['total_executions'] > 0 else 0.0
            )

            return {
                'uptime_seconds': uptime,
                'total_executions': self.performance_stats['total_executions'],
                'cache_hit_ratio': cache_hit_ratio,
                'average_execution_time': self.performance_stats['average_execution_time'],
                'peak_speedup': self.performance_stats['peak_speedup'],
                'average_workers_per_execution': avg_workers,
                'parallel_execution_ratio': (
                    self.performance_stats['parallel_executions'] / self.performance_stats['total_executions']
                    if self.performance_stats['total_executions'] > 0 else 0.0
                )
            }

    def log_performance_summary(self):
        """Log do resumo de performance."""
        summary = self.get_performance_summary()

        logging.info(f"📊 ULTRA PERFORMANCE SUMMARY:")
        logging.info(f"   • Total Executions: {summary['total_executions']}")
        logging.info(f"   • Cache Hit Ratio: {summary['cache_hit_ratio']:.1%}")
        logging.info(f"   • Average Time: {summary['average_execution_time']:.3f}s")
        logging.info(f"   • Peak Speedup: {summary['peak_speedup']:.1f}x")
        logging.info(f"   • Avg Workers: {summary['average_workers_per_execution']:.1f}")
        logging.info(f"   • Parallel Ratio: {summary['parallel_execution_ratio']:.1%}")

    def get_recent_executions(self, count: int = 10) -> List[Dict[str, Any]]:
        """Retorna execuções recentes."""
        with self.lock:
            return list(self.execution_history)[-count:]

    def reset_stats(self):
        """Reset das estatísticas de performance."""
        with self.lock:
            self.performance_stats = {
                'total_executions': 0,
                'cache_hits': 0,
                'average_execution_time': 0.0,
                'peak_speedup': 0.0,
                'total_workers_used': 0,
                'parallel_executions': 0
            }
            self.execution_history.clear()
            self.start_time = time.time()

        logging.info("🔄 Performance stats resetadas")

# Instância global
ultra_monitor = UltraPerformanceMonitor()

# Propriedades para compatibilidade
@property
def peak_speedup():
    return ultra_monitor.performance_stats['peak_speedup']

# Adicionar ao módulo
ultra_monitor.peak_speedup = property(lambda self: self.performance_stats['peak_speedup'])