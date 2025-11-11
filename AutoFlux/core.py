
"""
AutoFlux Core - Núcleo principal do sistema de processamento paralelo
"""

import concurrent.futures
import os
import psutil
import gc
import logging
from functools import wraps
from itertools import islice
from typing import Any, Dict, List, Optional, Union, Callable

from .engines import EngineManager
from .utils import PerformanceMonitor

# Imports opcionais com fallbacks
try:
    from loky import ProcessPoolExecutor as LokyExecutor
    HAS_LOKY = True
except ImportError:
    HAS_LOKY = False

logger = logging.getLogger(__name__)

class AutoFluxROKO:
    """
    Motor de processamento paralelo unificado para ROKO.
    
    Combina todas as melhores características das versões AutoFlux
    para processamento seguro, eficiente e adaptativo de dados.
    """
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        memory_safe: bool = True,
        timeout: Optional[float] = None,
        safe_mode: bool = True,
        engine: str = 'auto',
        enable_gc: bool = True,
        flatten_3d: bool = True
    ):
        """
        Inicializa AutoFluxROKO.
        
        Args:
            max_workers: Número máximo de workers (None = automático)
            memory_safe: Ajusta workers baseado na RAM disponível
            timeout: Timeout para operações em segundos
            safe_mode: Modo seguro com validações extras
            engine: Engine preferida ('auto', 'pandas', 'polars', 'numpy')
            enable_gc: Habilita garbage collection entre batches
            flatten_3d: Achata arrays 3D automaticamente
        """
        self.timeout = timeout
        self.safe_mode = safe_mode
        self.enable_gc = enable_gc
        self.flatten_3d = flatten_3d
        
        # Inicializar componentes
        self.engine_manager = EngineManager(engine)
        self.performance_monitor = PerformanceMonitor()
        
        if memory_safe:
            self.max_workers = self._calculate_safe_workers()
        else:
            self.max_workers = max_workers or (os.cpu_count() * 2)
            
        logger.info(f"AutoFluxROKO inicializado - Workers: {self.max_workers}, Engine: {engine}")
    
    def _calculate_safe_workers(self) -> int:
        """Calcula número seguro de workers baseado na RAM disponível."""
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        cpu_cores = os.cpu_count() or 1
        
        # Fórmula conservadora: 1 worker por 2GB RAM, limitado pelos CPUs
        safe_workers = max(1, min(cpu_cores, int(ram_gb // 2)))
        
        logger.debug(f"RAM: {ram_gb:.1f}GB, CPUs: {cpu_cores}, Workers seguros: {safe_workers}")
        return safe_workers
    
    def _calculate_batch_size(self, data: Any) -> int:
        """Calcula tamanho ideal de batch baseado nos dados e memória."""
        return self.engine_manager.calculate_batch_size(data)
    
    def _should_bypass_batch(self, data: Any) -> bool:
        """Determina se deve pular o processamento em batches para datasets pequenos."""
        return self.engine_manager.should_bypass_batch(data)
    
    def parallel(
        self,
        strategy: str = 'auto',
        use_process: bool = False,
        chunk_management: bool = True
    ):
        """
        Decorador principal para processamento paralelo.
        
        Args:
            strategy: 'auto', 'threads', 'process', 'sequential'
            use_process: Força uso de ProcessPoolExecutor
            chunk_management: Habilita gerenciamento inteligente de chunks
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                data = args[0] if args else kwargs.get('data')
                
                if strategy == 'sequential':
                    return func(*args, **kwargs)
                
                # Auto-bypass para dados pequenos
                if self._should_bypass_batch(data):
                    logger.debug("Dados pequenos detectados - executando sequencialmente")
                    return func(*args, **kwargs)
                
                # Seleção de executor
                if strategy == 'process' or use_process:
                    executor_class = LokyExecutor if HAS_LOKY else concurrent.futures.ProcessPoolExecutor
                else:
                    executor_class = concurrent.futures.ThreadPoolExecutor
                
                return self._execute_parallel(
                    func, executor_class, chunk_management, *args, **kwargs
                )
            
            return wrapper
        return decorator
    
    def _execute_parallel(self, func, executor_class, chunk_management, *args, **kwargs):
        """Executa função em paralelo com monitoramento de performance."""
        
        with self.performance_monitor.monitor_execution():
            data = args[0] if args else kwargs.get('data')
            batch_size = self._calculate_batch_size(data)
            
            try:
                with executor_class(max_workers=self.max_workers) as executor:
                    # Processar em batches
                    batches = self._create_batches(data, batch_size)
                    futures = []
                    
                    for batch in batches:
                        future = executor.submit(func, batch, *args[1:], **kwargs)
                        futures.append(future)
                    
                    # Coletar resultados
                    results = []
                    for future in concurrent.futures.as_completed(futures, timeout=self.timeout):
                        try:
                            result = future.result()
                            results.append(result)
                            
                            if self.enable_gc:
                                gc.collect()
                                
                        except Exception as e:
                            logger.error(f"Erro no processamento paralelo: {e}")
                            if self.safe_mode:
                                raise
                    
                    return self._merge_results(results, data)
                    
            except Exception as e:
                logger.error(f"Erro na execução paralela: {e}")
                if self.safe_mode:
                    raise
                # Fallback para execução sequencial
                return func(*args, **kwargs)
    
    def _create_batches(self, data: Any, batch_size: int) -> List[Any]:
        """Cria batches dos dados para processamento paralelo."""
        return self.engine_manager.create_batches(data, batch_size)
    
    def _merge_results(self, results: List[Any], original_data: Any) -> Any:
        """Merge dos resultados processados em paralelo."""
        return self.engine_manager.merge_results(results, original_data)

# Função de conveniência
def create_autoflux(**kwargs) -> AutoFluxROKO:
    """Cria instância do AutoFlux com configuração padrão."""
    return AutoFluxROKO(**kwargs)
