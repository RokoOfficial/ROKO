
"""
AutoFlux Engines - Gerenciamento de engines de processamento de dados
"""

import logging
from typing import Any, List, Optional, Union

# Imports opcionais com fallbacks
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    pl = None
    HAS_POLARS = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

logger = logging.getLogger(__name__)

class EngineManager:
    """Gerencia diferentes engines de processamento de dados."""
    
    def __init__(self, preferred_engine: str = 'auto'):
        """
        Inicializa o gerenciador de engines.
        
        Args:
            preferred_engine: Engine preferida ('auto', 'pandas', 'polars', 'numpy')
        """
        self.preferred_engine = preferred_engine.lower()
        self.available_engines = self._detect_available_engines()
        
        logger.info(f"EngineManager inicializado - Engine preferida: {self.preferred_engine}")
        logger.debug(f"Engines disponíveis: {self.available_engines}")
    
    def _detect_available_engines(self) -> List[str]:
        """Detecta engines disponíveis no sistema."""
        engines = []
        if HAS_PANDAS:
            engines.append('pandas')
        if HAS_POLARS:
            engines.append('polars')
        if HAS_NUMPY:
            engines.append('numpy')
        return engines
    
    def get_optimal_engine(self, data: Any) -> str:
        """
        Determina a engine ótima para os dados fornecidos.
        
        Args:
            data: Dados para processar
            
        Returns:
            str: Nome da engine ótima
        """
        if self.preferred_engine != 'auto':
            return self.preferred_engine
        
        # Auto-detecção baseada no tipo de dados
        if HAS_POLARS and isinstance(data, pl.DataFrame):
            return 'polars'
        elif HAS_PANDAS and isinstance(data, pd.DataFrame):
            return 'pandas'
        elif HAS_NUMPY and isinstance(data, np.ndarray):
            return 'numpy'
        else:
            # Fallback para a primeira engine disponível
            return self.available_engines[0] if self.available_engines else 'python'
    
    def calculate_batch_size(self, data: Any) -> int:
        """
        Calcula tamanho ideal de batch baseado nos dados e engine.
        
        Args:
            data: Dados para processar
            
        Returns:
            int: Tamanho do batch
        """
        # Tamanho alvo por batch: 20MB
        target_batch_bytes = 20 * 1024 * 1024
        
        engine = self.get_optimal_engine(data)
        
        if engine == 'polars' and HAS_POLARS and isinstance(data, pl.DataFrame):
            data_bytes = data.estimated_size()
            total_items = data.height
        elif engine == 'pandas' and HAS_PANDAS and isinstance(data, pd.DataFrame):
            data_bytes = data.memory_usage(deep=True).sum()
            total_items = len(data)
        elif engine == 'numpy' and HAS_NUMPY and isinstance(data, np.ndarray):
            data_bytes = data.nbytes
            total_items = len(data)
        else:
            # Fallback para outros tipos
            total_items = len(data) if hasattr(data, '__len__') else 10000
            data_bytes = total_items * 100  # Estimativa
        
        # Calcula número de batches baseado no tamanho dos dados
        approx_batches = max(1, data_bytes // target_batch_bytes)
        batch_size = max(1000, total_items // approx_batches)
        
        logger.debug(f"Engine: {engine}, Data size: {data_bytes/1024/1024:.1f}MB, Batch size: {batch_size}")
        return batch_size
    
    def should_bypass_batch(self, data: Any) -> bool:
        """
        Determina se deve pular o processamento em batches.
        
        Args:
            data: Dados para analisar
            
        Returns:
            bool: True se deve pular batching
        """
        engine = self.get_optimal_engine(data)
        
        if engine == 'polars' and HAS_POLARS and isinstance(data, pl.DataFrame):
            return data.height <= 5_000_000
        elif engine == 'pandas' and HAS_PANDAS and isinstance(data, pd.DataFrame):
            return len(data) <= 5_000_000
        elif engine == 'numpy' and HAS_NUMPY and isinstance(data, np.ndarray):
            return len(data) <= 5_000_000
        else:
            return len(data) <= 5_000_000 if hasattr(data, '__len__') else False
    
    def create_batches(self, data: Any, batch_size: int) -> List[Any]:
        """
        Cria batches dos dados usando a engine apropriada.
        
        Args:
            data: Dados para dividir
            batch_size: Tamanho de cada batch
            
        Returns:
            List[Any]: Lista de batches
        """
        engine = self.get_optimal_engine(data)
        
        if engine == 'polars' and HAS_POLARS and isinstance(data, pl.DataFrame):
            return self._create_polars_batches(data, batch_size)
        elif engine == 'pandas' and HAS_PANDAS and isinstance(data, pd.DataFrame):
            return self._create_pandas_batches(data, batch_size)
        elif engine == 'numpy' and HAS_NUMPY and isinstance(data, np.ndarray):
            return self._create_numpy_batches(data, batch_size)
        else:
            return self._create_generic_batches(data, batch_size)
    
    def _create_polars_batches(self, df: 'pl.DataFrame', batch_size: int) -> List['pl.DataFrame']:
        """Cria batches para Polars DataFrame."""
        batches = []
        for i in range(0, df.height, batch_size):
            batch = df.slice(i, batch_size)
            batches.append(batch)
        return batches
    
    def _create_pandas_batches(self, df: 'pd.DataFrame', batch_size: int) -> List['pd.DataFrame']:
        """Cria batches para Pandas DataFrame."""
        batches = []
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batches.append(batch)
        return batches
    
    def _create_numpy_batches(self, arr: 'np.ndarray', batch_size: int) -> List['np.ndarray']:
        """Cria batches para NumPy array."""
        batches = []
        for i in range(0, len(arr), batch_size):
            batch = arr[i:i+batch_size]
            batches.append(batch)
        return batches
    
    def _create_generic_batches(self, data: Any, batch_size: int) -> List[Any]:
        """Cria batches para tipos genéricos."""
        if hasattr(data, '__getitem__') and hasattr(data, '__len__'):
            batches = []
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                batches.append(batch)
            return batches
        else:
            # Se não conseguir dividir, retorna como um batch único
            return [data]
    
    def merge_results(self, results: List[Any], original_data: Any) -> Any:
        """
        Merge dos resultados processados usando a engine apropriada.
        
        Args:
            results: Lista de resultados processados
            original_data: Dados originais para referência
            
        Returns:
            Any: Dados merged
        """
        if not results:
            return original_data
        
        engine = self.get_optimal_engine(original_data)
        
        if engine == 'polars' and HAS_POLARS:
            return self._merge_polars_results(results)
        elif engine == 'pandas' and HAS_PANDAS:
            return self._merge_pandas_results(results)
        elif engine == 'numpy' and HAS_NUMPY:
            return self._merge_numpy_results(results)
        else:
            return self._merge_generic_results(results)
    
    def _merge_polars_results(self, results: List['pl.DataFrame']) -> 'pl.DataFrame':
        """Merge resultados Polars."""
        return pl.concat(results)
    
    def _merge_pandas_results(self, results: List['pd.DataFrame']) -> 'pd.DataFrame':
        """Merge resultados Pandas."""
        return pd.concat(results, ignore_index=True)
    
    def _merge_numpy_results(self, results: List['np.ndarray']) -> 'np.ndarray':
        """Merge resultados NumPy."""
        return np.concatenate(results)
    
    def _merge_generic_results(self, results: List[Any]) -> List[Any]:
        """Merge resultados genéricos."""
        # Para tipos genéricos, simplesmente concatena listas
        if all(isinstance(r, list) for r in results):
            merged = []
            for result in results:
                merged.extend(result)
            return merged
        else:
            return results
