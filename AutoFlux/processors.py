"""
AutoFlux Processors - Processadores de dados especializados para ROKO
"""

import logging
from typing import Any, Union, List, Dict

# Imports opcionais
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    import numexpr as ne
    HAS_NUMEXPR = True
except ImportError:
    ne = None
    HAS_NUMEXPR = False

logger = logging.getLogger(__name__)

class ROKODataProcessor:
    """Processador de dados especializado para ROKO usando AutoFlux."""

    def __init__(self, autoflux_instance):
        """
        Inicializa o processador de dados ROKO.

        Args:
            autoflux_instance: Instância do AutoFluxROKO
        """
        self.autoflux = autoflux_instance
        logger.info("✅ ROKODataProcessor inicializado")

    def process_mathematical_operation(self, data, operation='sqrt_multiply'):
        """
        Processa operações matemáticas usando AutoFlux.

        Args:
            data: Dados para processar
            operation: Tipo de operação ('sqrt_multiply', 'exp_sqrt', etc.)

        Returns:
            Resultado da operação
        """
        @self.autoflux.parallel(strategy='auto')
        def math_operation(batch):
            if operation == 'sqrt_multiply' and HAS_NUMPY:
                return np.sqrt(batch) * 2
            elif operation == 'exp_sqrt' and HAS_NUMPY:
                return np.exp(np.sqrt(batch))
            elif operation == 'sin_exp' and HAS_NUMPY:
                return np.sin(np.exp(batch))
            else:
                # Fallback para operação simples
                if isinstance(batch, list):
                    return [x * 2 for x in batch]
                return batch

        return math_operation(data)

    def process_transformation(self, data, transform_type='group_sum'):
        """
        Processa transformações de dados usando AutoFlux.

        Args:
            data: Dados para transformar
            transform_type: Tipo de transformação

        Returns:
            Dados transformados
        """
        @self.autoflux.parallel(strategy='auto')
        def transform_operation(batch):
            if transform_type == 'group_sum' and hasattr(batch, 'groupby'):
                return batch.groupby("category")["value"].sum()
            elif isinstance(batch, list):
                return [x * 2 for x in batch]
            else:
                return batch

        return transform_operation(data)

    def process_custom_operation(self, data, operation_func, strategy='auto'):
        """
        Processa operação customizada usando AutoFlux.

        Args:
            data: Dados para processar
            operation_func: Função de operação customizada
            strategy: Estratégia de paralelização

        Returns:
            Resultado da operação
        """
        decorated_func = self.autoflux.parallel(strategy=strategy)(operation_func)
        return decorated_func(data)

    @staticmethod
    def process_numpy_operation(batch: 'np.ndarray', operation: str) -> 'np.ndarray':
        """
        Processa operações matemáticas compostas usando numexpr quando disponível.

        Args:
            batch: Array NumPy para processar
            operation: Nome da operação ('exp_sqrt', 'sin_exp', etc.)

        Returns:
            np.ndarray: Resultado da operação
        """
        if not HAS_NUMPY:
            raise ImportError("NumPy não está disponível")

        if not HAS_NUMEXPR:
            # Fallback para numpy puro
            return ROKODataProcessor._numpy_fallback_operation(batch, operation)

        # Usar numexpr para performance
        return ROKODataProcessor._numexpr_operation(batch, operation)

    @staticmethod
    def _numpy_fallback_operation(batch: 'np.ndarray', operation: str) -> 'np.ndarray':
        """Operações NumPy puras como fallback."""
        if operation == "exp_sqrt":
            return np.exp(np.sqrt(batch))
        elif operation == "sin_exp":
            return np.sin(np.exp(batch))
        elif operation == "log_sqrt1":
            return np.log(1 + np.sqrt(batch))
        elif operation == "sin_plus_cos":
            return np.sin(batch) + np.cos(batch)
        elif operation == "normalize":
            return (batch - np.mean(batch)) / np.std(batch)
        elif operation == "sigmoid":
            return 1 / (1 + np.exp(-batch))
        else:
            raise ValueError(f"Operação desconhecida: {operation}")

    @staticmethod
    def _numexpr_operation(batch: 'np.ndarray', operation: str) -> 'np.ndarray':
        """Operações usando numexpr para otimização."""
        if operation == "exp_sqrt":
            return ne.evaluate("exp(sqrt(batch))")
        elif operation == "sin_exp":
            return ne.evaluate("sin(exp(batch))")
        elif operation == "log_sqrt1":
            return ne.evaluate("log(1 + sqrt(batch))")
        elif operation == "sin_plus_cos":
            return ne.evaluate("sin(batch) + cos(batch)")
        elif operation == "normalize":
            mean_val = np.mean(batch)
            std_val = np.std(batch)
            return ne.evaluate("(batch - mean_val) / std_val")
        elif operation == "sigmoid":
            return ne.evaluate("1 / (1 + exp(-batch))")
        else:
            raise ValueError(f"Operação desconhecida para numexpr: {operation}")

    def process_batch_operation(self, data: Any, operation: str, **kwargs) -> Any:
        """
        Processa operação em lote usando AutoFlux se disponível.

        Args:
            data: Dados para processar
            operation: Nome da operação
            **kwargs: Argumentos adicionais

        Returns:
            Any: Dados processados
        """
        if self.autoflux:
            # Usar processamento paralelo
            @self.autoflux.parallel(strategy='auto')
            def parallel_operation(batch):
                return self.process_numpy_operation(batch, operation)

            return parallel_operation(data)
        else:
            # Processamento sequencial
            return self.process_numpy_operation(data, operation)

    def aggregate_statistics(self, data: Any) -> Dict[str, float]:
        """
        Calcula estatísticas agregadas dos dados.

        Args:
            data: Dados para analisar

        Returns:
            Dict[str, float]: Estatísticas calculadas
        """
        if not HAS_NUMPY:
            return {"error": "NumPy não disponível"}

        try:
            if hasattr(data, 'values'):  # DataFrame
                arr = np.array(data.values)
            else:
                arr = np.array(data)

            return {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "median": float(np.median(arr)),
                "count": int(len(arr.flatten()))
            }
        except Exception as e:
            self.logger.error(f"Erro ao calcular estatísticas: {e}")
            return {"error": str(e)}

    def transform_data(self, data: Any, transformation: str, **params) -> Any:
        """
        Aplica transformação aos dados.

        Args:
            data: Dados para transformar
            transformation: Tipo de transformação
            **params: Parâmetros da transformação

        Returns:
            Any: Dados transformados
        """
        transformations = {
            'normalize': self._normalize_data,
            'standardize': self._standardize_data,
            'scale': self._scale_data,
            'log_transform': self._log_transform
        }

        if transformation not in transformations:
            raise ValueError(f"Transformação '{transformation}' não suportada")

        return transformations[transformation](data, **params)

    def _normalize_data(self, data: Any, **params) -> Any:
        """Normaliza dados para o intervalo [0, 1]."""
        if not HAS_NUMPY:
            return data

        arr = np.array(data)
        min_val = np.min(arr)
        max_val = np.max(arr)

        if max_val == min_val:
            return np.zeros_like(arr)

        return (arr - min_val) / (max_val - min_val)

    def _standardize_data(self, data: Any, **params) -> Any:
        """Padroniza dados (Z-score)."""
        if not HAS_NUMPY:
            return data

        arr = np.array(data)
        mean_val = np.mean(arr)
        std_val = np.std(arr)

        if std_val == 0:
            return np.zeros_like(arr)

        return (arr - mean_val) / std_val

    def _scale_data(self, data: Any, scale_factor: float = 1.0, **params) -> Any:
        """Escala dados por um fator."""
        if not HAS_NUMPY:
            return data

        return np.array(data) * scale_factor

    def _log_transform(self, data: Any, base: str = 'natural', **params) -> Any:
        """Aplica transformação logarítmica."""
        if not HAS_NUMPY:
            return data

        arr = np.array(data)

        # Garantir valores positivos
        arr = np.abs(arr) + 1e-8

        if base == 'natural':
            return np.log(arr)
        elif base == '10':
            return np.log10(arr)
        elif base == '2':
            return np.log2(arr)
        else:
            raise ValueError(f"Base logarítmica '{base}' não suportada")

class DataPipelineProcessor:
    """Processador para pipelines de dados complexos."""

    def __init__(self, data_processor: ROKODataProcessor):
        """
        Inicializa o processador de pipeline.

        Args:
            data_processor: Instância do processador de dados
        """
        self.data_processor = data_processor
        self.pipeline_steps = []

    def add_step(self, operation: str, **kwargs):
        """
        Adiciona uma etapa ao pipeline.

        Args:
            operation: Nome da operação
            **kwargs: Parâmetros da operação
        """
        self.pipeline_steps.append({'operation': operation, 'params': kwargs})
        return self

    def execute_pipeline(self, data: Any) -> Any:
        """
        Executa o pipeline completo nos dados.

        Args:
            data: Dados de entrada

        Returns:
            Any: Dados processados pelo pipeline
        """
        result = data

        for step in self.pipeline_steps:
            operation = step['operation']
            params = step.get('params', {})

            if hasattr(self.data_processor, f'transform_data'):
                result = self.data_processor.transform_data(result, operation, **params)
            elif hasattr(self.data_processor, operation):
                method = getattr(self.data_processor, operation)
                result = method(result, **params)
            else:
                logger.warning(f"Operação '{operation}' não encontrada, pulando...")

        return result

    def clear_pipeline(self):
        """Limpa todas as etapas do pipeline."""
        self.pipeline_steps.clear()
        return self