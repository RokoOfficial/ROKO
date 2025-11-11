
"""
AutoFlux Utils - Utilitários e ferramentas auxiliares
"""

import time
import logging
import psutil
import threading
from contextlib import contextmanager
from typing import Dict, Any, Optional
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor de performance para operações AutoFlux."""
    
    def __init__(self):
        """Inicializa o monitor de performance."""
        self.metrics = defaultdict(list)
        self.current_execution = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def monitor_execution(self, operation_name: str = "default"):
        """
        Context manager para monitorar execução de operações.
        
        Args:
            operation_name: Nome da operação sendo monitorada
        """
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            with self._lock:
                self.current_execution[operation_name] = {
                    'start_time': start_time,
                    'start_memory': start_memory
                }
            
            yield
            
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            with self._lock:
                self.metrics[operation_name].append({
                    'execution_time': execution_time,
                    'memory_used': memory_delta,
                    'timestamp': end_time
                })
                
                if operation_name in self.current_execution:
                    del self.current_execution[operation_name]
            
            logger.debug(f"Operação '{operation_name}': {execution_time:.3f}s, Memória: {memory_delta:+.1f}MB")
    
    def get_metrics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém métricas de performance.
        
        Args:
            operation_name: Nome da operação (None para todas)
            
        Returns:
            Dict[str, Any]: Métricas de performance
        """
        with self._lock:
            if operation_name:
                if operation_name not in self.metrics:
                    return {}
                
                metrics_list = self.metrics[operation_name]
                if not metrics_list:
                    return {}
                
                return {
                    'operation': operation_name,
                    'total_executions': len(metrics_list),
                    'avg_execution_time': sum(m['execution_time'] for m in metrics_list) / len(metrics_list),
                    'total_execution_time': sum(m['execution_time'] for m in metrics_list),
                    'avg_memory_used': sum(m['memory_used'] for m in metrics_list) / len(metrics_list),
                    'last_execution': metrics_list[-1] if metrics_list else None
                }
            else:
                # Retornar métricas de todas as operações
                all_metrics = {}
                for op_name in self.metrics:
                    all_metrics[op_name] = self.get_metrics(op_name)
                return all_metrics
    
    def reset_metrics(self, operation_name: Optional[str] = None):
        """
        Reset das métricas.
        
        Args:
            operation_name: Nome da operação (None para todas)
        """
        with self._lock:
            if operation_name:
                self.metrics[operation_name].clear()
            else:
                self.metrics.clear()
    
    def get_summary(self) -> str:
        """
        Obtém sumário formatado das métricas.
        
        Returns:
            str: Sumário das métricas
        """
        summary_lines = ["📊 AutoFlux Performance Summary", "=" * 40]
        
        all_metrics = self.get_metrics()
        
        if not all_metrics:
            summary_lines.append("Nenhuma métrica disponível")
            return "\n".join(summary_lines)
        
        for operation, metrics in all_metrics.items():
            if not metrics:
                continue
                
            summary_lines.extend([
                f"\n🔧 Operação: {operation}",
                f"   Execuções: {metrics['total_executions']}",
                f"   Tempo médio: {metrics['avg_execution_time']:.3f}s",
                f"   Tempo total: {metrics['total_execution_time']:.3f}s",
                f"   Memória média: {metrics['avg_memory_used']:+.1f}MB"
            ])
        
        return "\n".join(summary_lines)

class ResourceManager:
    """Gerenciador de recursos do sistema."""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Obtém informações do sistema.
        
        Returns:
            Dict[str, Any]: Informações do sistema
        """
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        return {
            'cpu_count_logical': cpu_count,
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'memory_total_gb': memory.total / (1024 ** 3),
            'memory_available_gb': memory.available / (1024 ** 3),
            'memory_percent_used': memory.percent,
            'cpu_percent': psutil.cpu_percent(interval=1)
        }
    
    @staticmethod
    def get_optimal_workers() -> int:
        """
        Calcula número ótimo de workers baseado nos recursos.
        
        Returns:
            int: Número ótimo de workers
        """
        info = ResourceManager.get_system_info()
        
        # Fórmula baseada em CPU e memória disponível
        cpu_workers = info['cpu_count_logical']
        memory_workers = max(1, int(info['memory_available_gb'] / 2))  # 2GB por worker
        
        optimal = min(cpu_workers, memory_workers)
        
        # Ajustar baseado no uso atual de CPU
        if info['cpu_percent'] > 80:
            optimal = max(1, optimal // 2)
        
        return optimal
    
    @staticmethod
    def check_memory_pressure() -> bool:
        """
        Verifica se há pressão de memória no sistema.
        
        Returns:
            bool: True se há pressão de memória
        """
        memory = psutil.virtual_memory()
        return memory.percent > 85  # Mais de 85% de uso

class BatchOptimizer:
    """Otimizador de batches para processamento eficiente."""
    
    def __init__(self):
        """Inicializa o otimizador de batches."""
        self.performance_history = deque(maxlen=100)
    
    def optimize_batch_size(self, data_size: int, current_batch_size: int, 
                          execution_time: float, memory_used: float) -> int:
        """
        Otimiza o tamanho do batch baseado na performance histórica.
        
        Args:
            data_size: Tamanho total dos dados
            current_batch_size: Tamanho atual do batch
            execution_time: Tempo de execução do último batch
            memory_used: Memória usada pelo último batch
            
        Returns:
            int: Tamanho otimizado do batch
        """
        # Armazenar performance atual
        self.performance_history.append({
            'batch_size': current_batch_size,
            'execution_time': execution_time,
            'memory_used': memory_used,
            'throughput': current_batch_size / execution_time if execution_time > 0 else 0
        })
        
        if len(self.performance_history) < 3:
            return current_batch_size  # Dados insuficientes
        
        # Analisar tendências
        recent_performance = list(self.performance_history)[-3:]
        avg_throughput = sum(p['throughput'] for p in recent_performance) / len(recent_performance)
        avg_memory = sum(p['memory_used'] for p in recent_performance) / len(recent_performance)
        
        # Verificar recursos disponíveis
        system_info = ResourceManager.get_system_info()
        memory_pressure = ResourceManager.check_memory_pressure()
        
        new_batch_size = current_batch_size
        
        # Lógica de otimização
        if memory_pressure or avg_memory > 1000:  # > 1GB por batch
            # Reduzir batch size se há pressão de memória
            new_batch_size = max(1000, current_batch_size // 2)
        elif avg_throughput > 0 and not memory_pressure:
            # Aumentar batch size se performance está boa
            if system_info['memory_available_gb'] > 4:  # Memória suficiente
                new_batch_size = min(data_size, int(current_batch_size * 1.5))
        
        logger.debug(f"Otimização de batch: {current_batch_size} → {new_batch_size}")
        return new_batch_size

# Utilitários globais
def format_bytes(bytes_value: int) -> str:
    """
    Formata bytes em unidades legíveis.
    
    Args:
        bytes_value: Valor em bytes
        
    Returns:
        str: Valor formatado
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_time(seconds: float) -> str:
    """
    Formata tempo em unidades legíveis.
    
    Args:
        seconds: Tempo em segundos
        
    Returns:
        str: Tempo formatado
    """
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{int(minutes)}m {secs:.1f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"

# Singleton instances para uso global
_performance_monitor = PerformanceMonitor()
_batch_optimizer = BatchOptimizer()

def get_performance_monitor() -> PerformanceMonitor:
    """Obtém instância global do monitor de performance."""
    return _performance_monitor

def get_batch_optimizer() -> BatchOptimizer:
    """Obtém instância global do otimizador de batches."""
    return _batch_optimizer
