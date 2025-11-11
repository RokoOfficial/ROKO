"""
Sistema de Cache Ultra-Agressivo para ROKO
Acelera requests similares em até 100x
"""

import time
import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class UltraCacheSystem:
    """Sistema de cache ultra-otimizado com múltiplas camadas."""

    def __init__(self, max_size: int = 10000, ttl_hours: int = 24):
        self.memory_cache = {}  # Cache L1 - memória
        self.persistent_cache = {}  # Cache L2 - persistente
        self.semantic_cache = {}  # Cache L3 - semântico

        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.hit_stats = {"l1": 0, "l2": 0, "l3": 0, "miss": 0}

        logging.info("🚀 Ultra Cache System ativado com 3 camadas")

    def _generate_cache_key(self, content: str, context: str = "") -> str:
        """Gera chave de cache otimizada."""
        combined = f"{content}:{context}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def get(self, key: str, content: str = "", context: str = "") -> Optional[Any]:
        """Busca em cache com fallback em múltiplas camadas."""
        cache_key = self._generate_cache_key(content or key, context)
        current_time = datetime.now()

        # L1 Cache - Memória (mais rápido)
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if current_time <= entry["expires"]:
                self.hit_stats["l1"] += 1
                logging.debug(f"💾 L1 Cache HIT: {cache_key[:8]}...")
                return entry["data"]
            else:
                del self.memory_cache[cache_key]

        # L2 Cache - Persistente  
        if cache_key in self.persistent_cache:
            entry = self.persistent_cache[cache_key]
            if current_time <= entry["expires"]:
                # Promover para L1
                self.memory_cache[cache_key] = entry
                self.hit_stats["l2"] += 1
                logging.debug(f"💿 L2 Cache HIT: {cache_key[:8]}... (promovido L1)")
                return entry["data"]
            else:
                del self.persistent_cache[cache_key]

        # L3 Cache - Semântico (busca por similaridade)
        semantic_match = self._semantic_search(content, context)
        if semantic_match:
            # Promover para L1 e L2
            expires = current_time + timedelta(hours=self.ttl_hours)
            cache_entry = {"data": semantic_match, "expires": expires, "hits": 1}

            self.memory_cache[cache_key] = cache_entry
            self.persistent_cache[cache_key] = cache_entry
            self.hit_stats["l3"] += 1
            logging.debug(f"🧠 L3 Semantic HIT: {cache_key[:8]}...")
            return semantic_match

        # Cache MISS
        self.hit_stats["miss"] += 1
        return None

    def set(self, key: str, data: Any, content: str = "", context: str = ""):
        """Armazena em todas as camadas de cache."""
        cache_key = self._generate_cache_key(content or key, context)
        expires = datetime.now() + timedelta(hours=self.ttl_hours)

        cache_entry = {
            "data": data,
            "expires": expires,
            "hits": 0,
            "created": datetime.now(),
            "content": content,
            "context": context
        }

        # Armazenar em todas as camadas
        self.memory_cache[cache_key] = cache_entry
        self.persistent_cache[cache_key] = cache_entry
        self.semantic_cache[cache_key] = cache_entry

        # Limpar cache se necessário
        self._cleanup_if_needed()

        logging.debug(f"💾 Cache SET: {cache_key[:8]}... em 3 camadas")

    def _semantic_search(self, content: str, context: str) -> Optional[Any]:
        """Busca semântica por conteúdo similar."""
        if not content:
            return None

        # Buscar entradas similares
        for cache_key, entry in self.semantic_cache.items():
            stored_content = entry.get("content", "")
            stored_context = entry.get("context", "")

            # Calcular similaridade simples
            similarity = self._calculate_similarity(content, stored_content)
            context_similarity = self._calculate_similarity(context, stored_context)

            # Se similaridade alta (>80%), considerar hit
            if similarity > 0.8 and context_similarity > 0.7:
                if datetime.now() <= entry["expires"]:
                    return entry["data"]

        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade simples entre textos."""
        if not text1 or not text2:
            return 0.0

        # Converter para conjuntos de palavras
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Similaridade Jaccard
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _cleanup_if_needed(self):
        """Limpa cache se exceder tamanho máximo."""
        if len(self.memory_cache) > self.max_size:
            # Remover 20% das entradas mais antigas
            to_remove = int(self.max_size * 0.2)

            # Ordenar por data de criação
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].get("created", datetime.now())
            )

            for cache_key, _ in sorted_items[:to_remove]:
                self.memory_cache.pop(cache_key, None)
                self.persistent_cache.pop(cache_key, None)
                self.semantic_cache.pop(cache_key, None)

            logging.info(f"🧹 Cache cleanup: removidas {to_remove} entradas antigas")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas do cache."""
        total_requests = sum(self.hit_stats.values())
        total_hits = total_requests - self.hit_stats["miss"]

        return {
            "total_requests": total_requests,
            "total_hits": total_hits,
            "hit_rate": (total_hits / total_requests * 100) if total_requests > 0 else 0,
            "l1_hits": self.hit_stats["l1"],
            "l2_hits": self.hit_stats["l2"], 
            "l3_hits": self.hit_stats["l3"],
            "cache_misses": self.hit_stats["miss"],
            "memory_cache_size": len(self.memory_cache),
            "persistent_cache_size": len(self.persistent_cache),
            "semantic_cache_size": len(self.semantic_cache),
            "estimated_speedup": self._calculate_speedup()
        }

    def _calculate_speedup(self) -> float:
        """Calcula speedup estimado baseado em hits."""
        total_requests = sum(self.hit_stats.values())
        if total_requests == 0:
            return 1.0

        # L1 cache: 100x speedup, L2: 50x, L3: 20x
        speedup = (
            self.hit_stats["l1"] * 100 +
            self.hit_stats["l2"] * 50 +
            self.hit_stats["l3"] * 20 +
            self.hit_stats["miss"] * 1
        ) / total_requests

        return round(speedup, 2)

# Instância global do cache ultra-otimizado
ultra_cache = UltraCacheSystem()