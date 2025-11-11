
"""
Sistema de Re-ranking Contextual para melhorar relevância das buscas.
"""

import numpy as np
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sqlite3

class ContextualReranker:
    """
    Sistema de re-ranking que considera múltiplos fatores contextuais.
    """
    
    def __init__(self, db_path: str = "roko_nexus.db"):
        self.db_path = db_path
        
        # Pesos para diferentes fatores de ranking
        self.weights = {
            "semantic_similarity": 0.4,    # Similaridade semântica base
            "temporal_relevance": 0.25,    # Quão recente é a interação
            "importance_score": 0.15,      # Score de importância manual
            "interaction_frequency": 0.10, # Frequência de acesso
            "contextual_match": 0.10       # Match com contexto atual
        }
    
    def rerank_results(self, 
                      initial_results: List[Dict[str, Any]], 
                      query_context: Dict[str, Any] = None,
                      current_session_context: List[str] = None) -> List[Dict[str, Any]]:
        """
        Re-rankeia resultados considerando múltiplos fatores contextuais.
        """
        if not initial_results:
            return initial_results
        
        # Calcular scores para cada resultado
        scored_results = []
        for result in initial_results:
            total_score = self._calculate_comprehensive_score(
                result, query_context, current_session_context
            )
            result_copy = result.copy()
            result_copy['rerank_score'] = total_score
            result_copy['score_breakdown'] = self._get_score_breakdown(result, query_context)
            scored_results.append(result_copy)
        
        # Ordenar por score total
        ranked_results = sorted(scored_results, key=lambda x: x['rerank_score'], reverse=True)
        
        logging.info(f"Re-ranking concluído: {len(ranked_results)} resultados processados")
        return ranked_results
    
    def _calculate_comprehensive_score(self, 
                                     result: Dict[str, Any], 
                                     query_context: Dict[str, Any] = None,
                                     session_context: List[str] = None) -> float:
        """Calcula score total considerando todos os fatores."""
        
        # 1. Similaridade semântica (base do FAISS)
        semantic_score = 1.0  # Normalizado, pois vem da busca FAISS
        
        # 2. Relevância temporal
        temporal_score = self._calculate_temporal_score(result)
        
        # 3. Score de importância
        importance_score = self._normalize_importance_score(result)
        
        # 4. Frequência de interação
        frequency_score = self._calculate_frequency_score(result)
        
        # 5. Match contextual
        contextual_score = self._calculate_contextual_match(result, query_context, session_context)
        
        # Calcular score final ponderado
        total_score = (
            semantic_score * self.weights["semantic_similarity"] +
            temporal_score * self.weights["temporal_relevance"] +
            importance_score * self.weights["importance_score"] +
            frequency_score * self.weights["interaction_frequency"] +
            contextual_score * self.weights["contextual_match"]
        )
        
        return total_score
    
    def _calculate_temporal_score(self, result: Dict[str, Any]) -> float:
        """Calcula score baseado na recência da interação."""
        try:
            # Assumir que timestamp está disponível
            timestamp_str = result.get('timestamp', datetime.now().isoformat())
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str
            
            # Calcular diferença em dias
            days_ago = (datetime.now() - timestamp).days
            
            # Score decai exponencialmente com o tempo
            # Interações recentes (< 1 dia) = score alto
            # Interações antigas (> 30 dias) = score baixo
            if days_ago <= 1:
                return 1.0
            elif days_ago <= 7:
                return 0.8
            elif days_ago <= 30:
                return 0.5
            else:
                return 0.2
                
        except Exception as e:
            logging.warning(f"Erro no cálculo temporal: {e}")
            return 0.5  # Score neutro
    
    def _normalize_importance_score(self, result: Dict[str, Any]) -> float:
        """Normaliza score de importância para 0-1."""
        importance = result.get('importance_score', 5)
        return min(max(importance / 10.0, 0.0), 1.0)
    
    def _calculate_frequency_score(self, result: Dict[str, Any]) -> float:
        """Calcula score baseado na frequência de acesso."""
        try:
            interaction_id = result.get('id')
            if not interaction_id:
                return 0.5
            
            # Contar quantas vezes esta interação foi recuperada
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as access_count 
                    FROM interaction_access_log 
                    WHERE interaction_id = ? 
                    AND accessed_at > datetime('now', '-30 days')
                """, (interaction_id,))
                
                result_count = cursor.fetchone()
                access_count = result_count[0] if result_count else 0
                
                # Normalizar: 0 acessos = 0.0, 10+ acessos = 1.0
                return min(access_count / 10.0, 1.0)
                
        except Exception as e:
            # Tabela pode não existir ainda
            return 0.5
    
    def _calculate_contextual_match(self, 
                                  result: Dict[str, Any], 
                                  query_context: Dict[str, Any] = None,
                                  session_context: List[str] = None) -> float:
        """Calcula match com contexto atual da sessão."""
        
        contextual_score = 0.0
        
        # Match com categoria/tags do contexto
        if query_context:
            result_category = result.get('category', '').lower()
            result_tags = result.get('tags', '').lower()
            query_category = query_context.get('category', '').lower()
            
            if result_category and query_category and result_category == query_category:
                contextual_score += 0.5
            
            if result_tags and query_category and query_category in result_tags:
                contextual_score += 0.3
        
        # Match com contexto da sessão atual
        if session_context:
            result_text = (
                result.get('user_prompt', '') + ' ' + 
                result.get('agent_response', '')
            ).lower()
            
            # Verificar overlap de palavras-chave
            session_keywords = set()
            for context in session_context:
                session_keywords.update(context.lower().split())
            
            result_keywords = set(result_text.split())
            overlap = len(session_keywords.intersection(result_keywords))
            
            if overlap > 0:
                contextual_score += min(overlap / 20.0, 0.5)  # Max 0.5 do overlap
        
        return min(contextual_score, 1.0)
    
    def _get_score_breakdown(self, result: Dict[str, Any], query_context: Dict[str, Any] = None) -> Dict[str, float]:
        """Retorna breakdown detalhado dos scores para debugging."""
        return {
            "temporal": self._calculate_temporal_score(result),
            "importance": self._normalize_importance_score(result),
            "frequency": self._calculate_frequency_score(result),
            "contextual": self._calculate_contextual_match(result, query_context)
        }
    
    def log_interaction_access(self, interaction_id: int):
        """Registra acesso para cálculo de frequência futura."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Criar tabela se não existir
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interaction_access_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        interaction_id INTEGER,
                        accessed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (interaction_id) REFERENCES interactions (id)
                    )
                """)
                
                # Registrar acesso
                cursor.execute("""
                    INSERT INTO interaction_access_log (interaction_id)
                    VALUES (?)
                """, (interaction_id,))
                
                conn.commit()
                
        except Exception as e:
            logging.warning(f"Erro ao registrar acesso: {e}")
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Atualiza pesos do sistema de ranking."""
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logging.warning(f"Pesos não somam 1.0: {total_weight}")
        
        self.weights.update(new_weights)
        logging.info(f"Pesos atualizados: {self.weights}")
    
    def get_ranking_explanation(self, result: Dict[str, Any]) -> str:
        """Gera explicação legível do ranking."""
        breakdown = result.get('score_breakdown', {})
        total_score = result.get('rerank_score', 0)
        
        explanation = f"Score Total: {total_score:.3f}\n"
        explanation += f"  • Temporal: {breakdown.get('temporal', 0):.3f}\n"
        explanation += f"  • Importância: {breakdown.get('importance', 0):.3f}\n"
        explanation += f"  • Frequência: {breakdown.get('frequency', 0):.3f}\n"
        explanation += f"  • Contextual: {breakdown.get('contextual', 0):.3f}"
        
        return explanation
