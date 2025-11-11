
"""
Sistema de Cache Inteligente para Embeddings ROKO.
"""

import hashlib
import pickle
import os
import time
import numpy as np
from typing import Dict, Optional, Any
import logging

class EmbeddingCache:
    """
    Cache inteligente para embeddings com TTL e compressão.
    """
    
    def __init__(self, cache_dir: str = "embedding_cache", max_size: int = 1000, ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self.memory_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "size": 0
        }
        
        # Criar diretório se não existir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Carregar cache existente
        self._load_cache_index()
    
    def _get_cache_key(self, text: str) -> str:
        """Gera chave única para o texto."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    def _load_cache_index(self):
        """Carrega índice do cache do disco."""
        index_path = os.path.join(self.cache_dir, "cache_index.pkl")
        if os.path.exists(index_path):
            try:
                with open(index_path, 'rb') as f:
                    self.cache_index = pickle.load(f)
            except:
                self.cache_index = {}
        else:
            self.cache_index = {}
    
    def _save_cache_index(self):
        """Salva índice do cache no disco."""
        index_path = os.path.join(self.cache_dir, "cache_index.pkl")
        try:
            with open(index_path, 'wb') as f:
                pickle.dump(self.cache_index, f)
        except Exception as e:
            logging.warning(f"Erro ao salvar índice do cache: {e}")
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """Recupera embedding do cache."""
        cache_key = self._get_cache_key(text)
        
        # Verificar cache em memória primeiro
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                self.cache_stats["hits"] += 1
                return entry['embedding']
            else:
                # Remover entrada expirada
                del self.memory_cache[cache_key]
        
        # Verificar cache em disco
        if cache_key in self.cache_index:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.npy")
            if os.path.exists(cache_file):
                try:
                    # Verificar TTL
                    file_time = os.path.getmtime(cache_file)
                    if time.time() - file_time < self.ttl_seconds:
                        embedding = np.load(cache_file)
                        
                        # Adicionar ao cache em memória
                        self.memory_cache[cache_key] = {
                            'embedding': embedding,
                            'timestamp': time.time()
                        }
                        
                        self.cache_stats["hits"] += 1
                        return embedding
                    else:
                        # Remover arquivo expirado
                        os.remove(cache_file)
                        del self.cache_index[cache_key]
                except Exception as e:
                    logging.warning(f"Erro ao carregar cache {cache_key}: {e}")
        
        self.cache_stats["misses"] += 1
        return None
    
    def put(self, text: str, embedding: np.ndarray):
        """Armazena embedding no cache."""
        cache_key = self._get_cache_key(text)
        
        # Adicionar ao cache em memória
        self.memory_cache[cache_key] = {
            'embedding': embedding.copy(),
            'timestamp': time.time()
        }
        
        # Salvar no disco (async)
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.npy")
            np.save(cache_file, embedding)
            self.cache_index[cache_key] = {
                'timestamp': time.time(),
                'text_hash': cache_key
            }
            
            # Limitar tamanho do cache
            if len(self.cache_index) > self.max_size:
                self._cleanup_old_entries()
                
            # Salvar índice
            self._save_cache_index()
            
        except Exception as e:
            logging.warning(f"Erro ao salvar no cache: {e}")
    
    def _cleanup_old_entries(self):
        """Remove entradas antigas do cache."""
        # Ordenar por timestamp e remover as mais antigas
        sorted_entries = sorted(
            self.cache_index.items(),
            key=lambda x: x[1]['timestamp']
        )
        
        # Remover 20% das entradas mais antigas
        remove_count = len(sorted_entries) // 5
        for cache_key, _ in sorted_entries[:remove_count]:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.npy")
            if os.path.exists(cache_file):
                os.remove(cache_file)
            del self.cache_index[cache_key]
            
            # Remover do cache em memória também
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_rate": f"{hit_rate:.2f}%",
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "memory_entries": len(self.memory_cache),
            "disk_entries": len(self.cache_index),
            "cache_size_mb": self._get_cache_size()
        }
    
    def _get_cache_size(self) -> float:
        """Calcula tamanho do cache em MB."""
        total_size = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.npy'):
                file_path = os.path.join(self.cache_dir, filename)
                total_size += os.path.getsize(file_path)
        return total_size / (1024 * 1024)  # MB
    
    def clear(self):
        """Limpa todo o cache."""
        # Limpar memória
        self.memory_cache.clear()
        
        # Limpar disco
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            os.remove(file_path)
        
        self.cache_index.clear()
        self.cache_stats = {"hits": 0, "misses": 0, "size": 0}
        logging.info("Cache de embeddings limpo completamente")
