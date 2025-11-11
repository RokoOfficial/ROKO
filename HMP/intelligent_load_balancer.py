
"""
Load Balancer Inteligente para Workers HMP
Distribui carga automaticamente para máxima performance
"""

import time
import threading
import psutil
from typing import List, Dict, Any
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import logging

class IntelligentLoadBalancer:
    """Load balancer que adapta número de workers baseado na carga."""
    
    def __init__(self, min_workers: int = 2, max_workers: int = 16):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = min_workers
        
        self.task_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=self.current_workers)
        self.worker_stats = {}
        
        # Métricas em tempo real
        self.cpu_threshold_high = 85.0
        self.cpu_threshold_low = 30.0
        self.memory_threshold = 80.0
        
        self.scaling_lock = threading.Lock()
        self.start_monitoring()
        
        logging.info(f"🔄 Load Balancer ativado: {min_workers}-{max_workers} workers")
    
    def submit_task(self, func, *args, **kwargs):
        """Submete tarefa com balanceamento automático."""
        # Verificar se precisa escalar
        self._auto_scale()
        
        # Submeter tarefa
        future = self.executor.submit(func, *args, **kwargs)
        
        # Atualizar estatísticas
        self._update_stats()
        
        return future
    
    def _auto_scale(self):
        """Escala workers automaticamente baseado na carga."""
        with self.scaling_lock:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            queue_size = self.task_queue.qsize()
            
            # Decidir se deve escalar para cima
            should_scale_up = (
                cpu_usage > self.cpu_threshold_high or
                queue_size > self.current_workers * 2
            ) and self.current_workers < self.max_workers
            
            # Decidir se deve escalar para baixo  
            should_scale_down = (
                cpu_usage < self.cpu_threshold_low and
                queue_size == 0 and
                self.current_workers > self.min_workers
            )
            
            # Verificar limitações de memória
            memory_limited = memory_usage > self.memory_threshold
            
            if should_scale_up and not memory_limited:
                self._scale_up()
            elif should_scale_down:
                self._scale_down()
    
    def _scale_up(self):
        """Aumenta número de workers."""
        old_workers = self.current_workers
        self.current_workers = min(self.current_workers + 2, self.max_workers)
        
        # Recriar executor com mais workers
        self.executor.shutdown(wait=False)
        self.executor = ThreadPoolExecutor(max_workers=self.current_workers)
        
        logging.info(f"⬆️ Scaling UP: {old_workers} → {self.current_workers} workers")
    
    def _scale_down(self):
        """Diminui número de workers."""
        old_workers = self.current_workers
        self.current_workers = max(self.current_workers - 1, self.min_workers)
        
        # Recriar executor com menos workers
        self.executor.shutdown(wait=True)
        self.executor = ThreadPoolExecutor(max_workers=self.current_workers)
        
        logging.info(f"⬇️ Scaling DOWN: {old_workers} → {self.current_workers} workers")
    
    def _update_stats(self):
        """Atualiza estatísticas do load balancer."""
        self.worker_stats = {
            "current_workers": self.current_workers,
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "queue_size": self.task_queue.qsize(),
            "timestamp": time.time()
        }
    
    def start_monitoring(self):
        """Inicia monitoramento contínuo."""
        def monitor_loop():
            while True:
                try:
                    time.sleep(10)  # Verificar a cada 10 segundos
                    self._auto_scale()
                except Exception as e:
                    logging.error(f"Erro no monitoramento: {e}")
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do load balancer."""
        return {
            **self.worker_stats,
            "min_workers": self.min_workers,
            "max_workers": self.max_workers,
            "scaling_efficiency": self._calculate_efficiency()
        }
    
    def _calculate_efficiency(self) -> float:
        """Calcula eficiência do balanceamento."""
        cpu_usage = psutil.cpu_percent()
        optimal_cpu = 70.0  # CPU ideal
        
        # Eficiência baseada em quão próximo estamos do CPU ideal
        efficiency = max(0, 100 - abs(cpu_usage - optimal_cpu))
        return round(efficiency, 2)

# Instância global do load balancer
intelligent_balancer = IntelligentLoadBalancer()
