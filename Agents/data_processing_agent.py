"""
Agente de Processamento de Dados - Integra AutoFluxROKO ao sistema ROKO.

Este agente é responsável por executar operações de processamento de dados
paralelo de forma segura e eficiente, integrando-se perfeitamente com a
arquitetura existente do ROKO.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from .base_agent import BaseAgent
import os # Import os for os.cpu_count()

# Import local do AutoFluxROKO - Nova arquitetura modular
try:
    from AutoFlux import AutoFluxROKO, ROKODataProcessor
    HAS_AUTOFLUX = True
    logging.info("✅ AutoFluxROKO importado com sucesso!")
except ImportError as e:
    HAS_AUTOFLUX = False
    logging.warning(f"AutoFluxROKO não disponível - funcionalidades limitadas: {e}")

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

# Configurar matplotlib para modo não-interativo
import matplotlib
matplotlib.use('Agg')  # Usar backend não-interativo
import matplotlib.pyplot as plt


class DataProcessingAgent(BaseAgent):
    """
    Agente especializado em processamento paralelo de dados usando AutoFluxROKO.

    Integra-se ao sistema ROKO para executar operações de dados complexas
    de forma eficiente e segura.
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)

        if HAS_AUTOFLUX:
            self.autoflux = AutoFluxROKO(
                max_workers=8,
                memory_safe=True,
                safe_mode=True,
                engine='auto',
                timeout=300.0,  # 5 minutos
                enable_gc=True
            )
            self.processor = ROKODataProcessor(self.autoflux)
            logging.info(f"✅ DataProcessingAgent inicializado com AutoFluxROKO - Workers: {self.autoflux.max_workers}")
        else:
            self.autoflux = None
            self.processor = None
            logging.warning("⚠️ DataProcessingAgent em modo limitado - AutoFluxROKO não disponível")

    def analyze_data_task(self, query: str) -> Dict[str, Any]:
        """Analisa se uma query requer processamento de dados paralelo."""

        system_prompt = """
        Você é um analisador de tarefas de processamento de dados.
        Determine se a query do usuário requer processamento paralelo de dados.

        Responda APENAS com um JSON contendo:
        - "requires_parallel": true/false
        - "data_type": "numpy", "pandas", "polars", "list", "unknown"
        - "operation_type": "mathematical", "transformation", "analysis", "join", "aggregation", "other"
        - "estimated_complexity": "low", "medium", "high"
        - "recommended_strategy": "sequential", "threads", "process", "auto"
        - "safe_mode": true/false
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                temperature=0.3
            )

            analysis = json.loads(response.choices[0].message.content)
            logging.info(f"🧠 Análise de dados: {analysis}")
            return analysis

        except Exception as e:
            logging.error(f"Erro na análise de dados: {e}")
            return {
                "requires_parallel": False,
                "data_type": "unknown",
                "operation_type": "other",
                "estimated_complexity": "low",
                "recommended_strategy": "sequential",
                "safe_mode": True
            }

    def execute_data_operation(self, data_info: Dict[str, Any]) -> Dict[str, Any]:
        """Executa operação de processamento de dados."""

        if not HAS_AUTOFLUX:
            return {
                "result": None,
                "error": "AutoFluxROKO não disponível - processamento limitado",
                "execution_time": 0.0
            }

        start_time = time.time()

        try:
            # Extrair informações da operação
            operation = data_info.get("operation", "unknown")
            data_size = data_info.get("data_size", 1000)
            strategy = data_info.get("strategy", "auto")

            # Gerar dados de exemplo se necessário
            if data_info.get("generate_sample_data", False):
                sample_data = self._generate_sample_data(data_info)
                result = self._process_sample_data(sample_data, operation, strategy)
            else:
                result = f"Operação {operation} configurada para execução com estratégia {strategy}"

            execution_time = time.time() - start_time

            return {
                "result": result,
                "error": None,
                "execution_time": execution_time,
                "strategy_used": strategy,
                "autoflux_enabled": True
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"Erro na execução de dados: {e}")
            return {
                "result": None,
                "error": str(e),
                "execution_time": execution_time
            }

    def _generate_sample_data(self, data_info: Dict[str, Any]) -> Any:
        """Gera dados de exemplo para demonstração."""
        data_type = data_info.get("data_type", "numpy")
        size = min(data_info.get("data_size", 1000), 100_000)  # Limitar para demonstração

        if data_type == "numpy" and HAS_NUMPY:
            return np.random.rand(size) + 1
        elif data_type == "pandas" and HAS_PANDAS:
            return pd.DataFrame({
                "value": np.random.rand(size),
                "category": np.random.choice(["A", "B", "C"], size)
            })
        elif data_type == "polars" and HAS_POLARS:
            return pl.DataFrame({
                "value": np.random.rand(size),
                "category": np.random.choice(["A", "B", "C"], size)
            })
        else:
            return list(range(size))

    def _process_sample_data(self, data: Any, operation: str, strategy: str) -> str:
        """Processa dados de exemplo usando AutoFluxROKO."""

        if operation == "mathematical" and HAS_NUMPY and isinstance(data, np.ndarray):
            # Operação matemática usando AutoFluxROKO
            @self.autoflux.parallel(strategy=strategy)
            def math_operation(batch):
                return np.sqrt(batch) * 2

            result = math_operation(data)
            return f"Operação matemática concluída em {len(result)} elementos"

        elif operation == "transformation":
            # Transformação usando AutoFluxROKO
            @self.autoflux.parallel(strategy=strategy)
            def transform_data(batch):
                if HAS_PANDAS and isinstance(batch, pd.DataFrame):
                    return batch.groupby("category")["value"].sum()
                elif isinstance(batch, list):
                    return [x * 2 for x in batch]
                else:
                    return batch

            result = transform_data(data)
            return f"Transformação concluída: {type(result).__name__}"

        else:
            return f"Operação {operation} simulada com sucesso"

    def generate_data_processing_code(self, requirements: str) -> str:
        """Gera código de processamento de dados baseado nos requisitos."""

        system_prompt = """
        Você é um especialista em AutoFluxROKO e processamento paralelo de dados.
        Gere código Python que use AutoFluxROKO para atender aos requisitos.

        Inclua:
        - Importações necessárias
        - Inicialização do AutoFluxROKO
        - Função decorada com @autoflux.parallel()
        - Tratamento de erros
        - Exemplo de uso

        Use as melhores práticas para performance e segurança.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Requisitos: {requirements}"}
                ],
                temperature=0.4
            )

            code = response.choices[0].message.content
            logging.info("📝 Código de processamento de dados gerado")
            return code

        except Exception as e:
            logging.error(f"Erro na geração de código: {e}")
            return f"# Erro na geração de código: {e}"

    def get_autoflux_status(self) -> Dict[str, Any]:
        """Retorna status e informações do AutoFluxROKO."""

        if not HAS_AUTOFLUX:
            return {
                "available": False,
                "error": "AutoFluxROKO não disponível"
            }

        import psutil

        return {
            "available": True,
            "max_workers": self.autoflux.max_workers,
            "safe_mode": self.autoflux.safe_mode,
            "engine": self.autoflux.engine,
            "timeout": self.autoflux.timeout,
            "memory_info": {
                "total_gb": psutil.virtual_memory().total / (1024**3),
                "available_gb": psutil.virtual_memory().available / (1024**3),
                "cpu_count": os.cpu_count()
            },
            "dependencies": {
                "pandas": HAS_PANDAS,
                "polars": HAS_POLARS,
                "numpy": HAS_NUMPY,
                "autoflux": HAS_AUTOFLUX
            }
        }

    def execute(self, query: str) -> Dict[str, Any]:
        """Método principal para execução de tarefas de processamento de dados."""

        # Análise da query
        analysis = self.analyze_data_task(query)

        if not analysis.get("requires_parallel", False):
            return {
                "result": "Query não requer processamento paralelo especializado",
                "error": None,
                "analysis": analysis
            }

        # Configurar operação de dados
        data_operation = {
            "operation": analysis.get("operation_type", "other"),
            "strategy": analysis.get("recommended_strategy", "auto"),
            "data_type": analysis.get("data_type", "unknown"),
            "data_size": 10000,  # Tamanho padrão para demonstração
            "generate_sample_data": True
        }

        # Executar operação
        result = self.execute_data_operation(data_operation)

        return {
            "result": result.get("result"),
            "error": result.get("error"),
            "analysis": analysis,
            "execution_time": result.get("execution_time", 0.0),
            "autoflux_status": self.get_autoflux_status()
        }