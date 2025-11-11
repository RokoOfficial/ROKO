
"""
Evolution Memory - Memória especializada para rastrear evolução de agentes.
"""

import json
import logging
import sqlite3
import numpy as np
from typing import Dict, Any, List
from datetime import datetime

class EvolutionMemory:
    """
    Sistema de memória especializado para evolução de agentes.
    """
    
    def __init__(self, db_path: str = "roko_nexus.db"):
        self.db_path = db_path
        self._init_evolution_tables()
        logging.info("EvolutionMemory inicializada")
    
    def _init_evolution_tables(self):
        """Inicializa tabelas específicas para evolução."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de agentes criados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    capabilities TEXT,
                    system_prompt TEXT,
                    specification TEXT,
                    code TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    performance_score REAL DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Tabela de evoluções
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_evolutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    evolution_type TEXT NOT NULL,
                    feedback TEXT,
                    improvements TEXT,
                    performance_before REAL,
                    performance_after REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_name) REFERENCES agent_registry (name)
                )
            ''')
            
            # Tabela de métricas de performance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    success_rate REAL,
                    avg_response_time REAL,
                    total_requests INTEGER,
                    error_count INTEGER,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_name) REFERENCES agent_registry (name)
                )
            ''')
            
            conn.commit()
    
    def register_agent(self, agent_data: Dict[str, Any]) -> bool:
        """Registra um novo agente no sistema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO agent_registry 
                    (name, type, capabilities, system_prompt, specification, code, performance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent_data["name"],
                    agent_data["type"],
                    json.dumps(agent_data.get("capabilities", [])),
                    agent_data.get("system_prompt", ""),
                    json.dumps(agent_data.get("specification", {})),
                    agent_data.get("code", ""),
                    0.0
                ))
                
                conn.commit()
                logging.info(f"✅ Agente {agent_data['name']} registrado na EvolutionMemory")
                return True
                
        except Exception as e:
            logging.error(f"Erro ao registrar agente: {e}")
            return False
    
    def record_evolution(self, evolution_data: Dict[str, Any]) -> bool:
        """Registra uma evolução de agente."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO agent_evolutions 
                    (agent_name, evolution_type, feedback, improvements, performance_before, performance_after)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    evolution_data["agent_name"],
                    evolution_data["evolution_type"],
                    json.dumps(evolution_data.get("feedback", {})),
                    json.dumps(evolution_data.get("improvements", {})),
                    evolution_data.get("performance_before", 0.0),
                    evolution_data.get("performance_after", 0.0)
                ))
                
                conn.commit()
                logging.info(f"🧬 Evolução de {evolution_data['agent_name']} registrada")
                return True
                
        except Exception as e:
            logging.error(f"Erro ao registrar evolução: {e}")
            return False
    
    def update_agent_metrics(self, agent_name: str, metrics: Dict[str, Any]) -> bool:
        """Atualiza métricas de performance de um agente."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO agent_metrics 
                    (agent_name, success_rate, avg_response_time, total_requests, error_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    agent_name,
                    metrics.get("success_rate", 0.0),
                    metrics.get("avg_response_time", 0.0),
                    metrics.get("total_requests", 0),
                    metrics.get("error_count", 0)
                ))
                
                # Atualizar score de performance no registro do agente
                performance_score = self._calculate_performance_score(metrics)
                cursor.execute('''
                    UPDATE agent_registry 
                    SET performance_score = ? 
                    WHERE name = ?
                ''', (performance_score, agent_name))
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f"Erro ao atualizar métricas: {e}")
            return False
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calcula score de performance baseado nas métricas."""
        success_rate = metrics.get("success_rate", 0.0)
        response_time = metrics.get("avg_response_time", 1.0)
        total_requests = metrics.get("total_requests", 0)
        
        # Score baseado em sucesso, velocidade e uso
        usage_factor = min(total_requests / 100, 1.0)  # Normalizar uso
        speed_factor = max(0, 1 - (response_time / 10))  # Penalizar lentidão
        
        score = (success_rate / 100) * 0.6 + speed_factor * 0.3 + usage_factor * 0.1
        return round(score * 100, 2)
    
    def get_agent_evolution_history(self, agent_name: str) -> List[Dict]:
        """Recupera histórico de evoluções de um agente."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT evolution_type, feedback, improvements, 
                           performance_before, performance_after, timestamp
                    FROM agent_evolutions 
                    WHERE agent_name = ?
                    ORDER BY timestamp DESC
                ''', (agent_name,))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        "evolution_type": row[0],
                        "feedback": json.loads(row[1]) if row[1] else {},
                        "improvements": json.loads(row[2]) if row[2] else {},
                        "performance_before": row[3],
                        "performance_after": row[4],
                        "timestamp": row[5]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logging.error(f"Erro ao recuperar histórico: {e}")
            return []
    
    def get_top_performing_agents(self, limit: int = 10) -> List[Dict]:
        """Retorna agentes com melhor performance."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT ar.name, ar.type, ar.capabilities, ar.performance_score,
                           am.success_rate, am.total_requests
                    FROM agent_registry ar
                    LEFT JOIN agent_metrics am ON ar.name = am.agent_name
                    WHERE ar.is_active = TRUE
                    ORDER BY ar.performance_score DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        "name": row[0],
                        "type": row[1],
                        "capabilities": json.loads(row[2]) if row[2] else [],
                        "performance_score": row[3],
                        "success_rate": row[4] or 0.0,
                        "total_requests": row[5] or 0
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logging.error(f"Erro ao recuperar top performers: {e}")
            return []
    
    def identify_evolution_candidates(self) -> List[Dict]:
        """Identifica agentes que precisam evoluir."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT ar.name, ar.type, ar.performance_score,
                           am.success_rate, am.error_count, am.total_requests
                    FROM agent_registry ar
                    LEFT JOIN agent_metrics am ON ar.name = am.agent_name
                    WHERE ar.is_active = TRUE
                    AND (ar.performance_score < 70 OR am.success_rate < 80)
                    ORDER BY ar.performance_score ASC
                ''')
                
                rows = cursor.fetchall()
                
                candidates = []
                for row in rows:
                    candidates.append({
                        "name": row[0],
                        "type": row[1],
                        "performance_score": row[2],
                        "success_rate": row[3] or 0.0,
                        "error_count": row[4] or 0,
                        "total_requests": row[5] or 0,
                        "evolution_reason": self._determine_evolution_reason(row)
                    })
                
                return candidates
                
        except Exception as e:
            logging.error(f"Erro ao identificar candidatos: {e}")
            return []
    
    def _determine_evolution_reason(self, metrics_row) -> str:
        """Determina a razão para evolução baseada nas métricas."""
        performance_score = metrics_row[2] or 0
        success_rate = metrics_row[3] or 0
        error_count = metrics_row[4] or 0
        
        reasons = []
        
        if performance_score < 50:
            reasons.append("baixa_performance_geral")
        if success_rate < 70:
            reasons.append("baixa_taxa_sucesso")
        if error_count > 10:
            reasons.append("muitos_erros")
        
        return ", ".join(reasons) if reasons else "melhoria_preventiva"
    
    def get_evolution_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de evolução."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de agentes
                cursor.execute("SELECT COUNT(*) FROM agent_registry WHERE is_active = TRUE")
                total_agents = cursor.fetchone()[0]
                
                # Total de evoluções
                cursor.execute("SELECT COUNT(*) FROM agent_evolutions")
                total_evolutions = cursor.fetchone()[0]
                
                # Performance média
                cursor.execute("SELECT AVG(performance_score) FROM agent_registry WHERE is_active = TRUE")
                avg_performance = cursor.fetchone()[0] or 0.0
                
                # Agentes por tipo
                cursor.execute('''
                    SELECT type, COUNT(*) 
                    FROM agent_registry 
                    WHERE is_active = TRUE 
                    GROUP BY type
                ''')
                agents_by_type = dict(cursor.fetchall())
                
                return {
                    "total_agents": total_agents,
                    "total_evolutions": total_evolutions,
                    "average_performance": round(avg_performance, 2),
                    "agents_by_type": agents_by_type,
                    "evolution_rate": round(total_evolutions / max(total_agents, 1), 2)
                }
                
        except Exception as e:
            logging.error(f"Erro ao calcular estatísticas: {e}")
            return {}
