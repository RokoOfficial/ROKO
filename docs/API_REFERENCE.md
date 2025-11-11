
# 🔌 Referência da API - ROKO System

## Visão Geral da API

O ROKO expõe várias APIs para interação programática com o sistema. Esta documentação cobre todos os endpoints, métodos e estruturas de dados disponíveis.

## Base URL
```
https://seu-repl.replit.app/api
```

## Autenticação

A API utiliza chaves de autenticação configuradas através de variáveis de ambiente:

```bash
OPENAI_API_KEY=sk-...
ROKO_API_SECRET=seu_secret_aqui  # Opcional para autenticação adicional
```

## Endpoints Principais

### 1. Chat/Conversação

#### POST `/api/chat`
Processa uma solicitação de chat através do pipeline ROKO.

**Request Body:**
```json
{
  "message": "Sua pergunta ou solicitação aqui",
  "user_id": "opcional_user_id",
  "context": {
    "conversation_id": "opcional_conversation_id",
    "preferences": {
      "response_style": "detailed|brief|technical",
      "include_sources": true|false
    }
  }
}
```

**Response:**
```json
{
  "status": "success|error",
  "response": "Resposta do ROKO",
  "metadata": {
    "processing_time": 2.5,
    "agents_used": ["roko", "web", "code"],
    "memory_entries_retrieved": 3,
    "confidence_score": 0.95
  },
  "execution_log": [
    "🎯 Analisando solicitação...",
    "🔍 Buscando informações relevantes...",
    "✅ Resposta gerada com sucesso"
  ],
  "sources": [
    {
      "type": "web_search",
      "url": "https://example.com",
      "title": "Fonte da informação",
      "relevance": 0.87
    }
  ]
}
```

**Códigos de Status:**
- `200`: Sucesso
- `400`: Solicitação inválida
- `401`: Não autorizado
- `429`: Rate limit excedido
- `500`: Erro interno do servidor

---

### 2. Memória

#### GET `/api/memory/search`
Busca na memória cognitiva do ROKO.

**Query Parameters:**
```
?query=texto_da_busca
&limit=10
&category=research|coding|general
&tags=tag1,tag2
&min_importance=5
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "id": 123,
      "timestamp": "2024-01-20T15:30:00Z",
      "user_prompt": "Pergunta original",
      "agent_response": "Resposta do ROKO",
      "category": "research",
      "tags": ["analysis", "data"],
      "importance_score": 8,
      "similarity_score": 0.92
    }
  ],
  "total_found": 25,
  "search_time": 0.15
}
```

#### POST `/api/memory/save`
Salva uma interação na memória (uso interno principalmente).

**Request Body:**
```json
{
  "interaction_type": "pipeline_execution|manual_entry",
  "user_prompt": "Texto da pergunta",
  "agent_thoughts": "Processo de raciocínio",
  "agent_response": "Resposta final",
  "category": "research",
  "tags": ["tag1", "tag2"],
  "importance_score": 7
}
```

#### GET `/api/memory/stats`
Estatísticas da memória cognitiva.

**Response:**
```json
{
  "total_interactions": 1547,
  "faiss_vectors": 1547,
  "categories": {
    "research": 623,
    "coding": 445,
    "general": 479
  },
  "average_importance": 6.2,
  "oldest_entry": "2024-01-01T00:00:00Z",
  "newest_entry": "2024-01-20T15:45:00Z"
}
```

---

### 3. Agentes

#### GET `/api/agents/status`
Status de todos os agentes do sistema.

**Response:**
```json
{
  "agents": {
    "roko": {
      "status": "active",
      "capabilities": ["analysis", "synthesis", "html_rendering"],
      "last_used": "2024-01-20T15:30:00Z",
      "success_rate": 0.98
    },
    "web": {
      "status": "active",
      "capabilities": ["web_search", "url_fetch", "data_extraction"],
      "last_used": "2024-01-20T15:25:00Z",
      "success_rate": 0.95
    },
    "code": {
      "status": "active",
      "capabilities": ["code_generation", "execution", "debugging"],
      "last_used": "2024-01-20T15:20:00Z",
      "success_rate": 0.92
    }
  },
  "orchestrator_status": "healthy"
}
```

#### POST `/api/agents/execute`
Executa um agente específico diretamente.

**Request Body:**
```json
{
  "agent": "web|code|shell|planner",
  "task": "Descrição da tarefa",
  "parameters": {
    "search_query": "termo de busca",
    "num_results": 5,
    "code_language": "python"
  }
}
```

---

### 4. Sistema

#### GET `/api/system/health`
Verificação de saúde do sistema.

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "components": {
    "database": "connected",
    "faiss_index": "loaded",
    "openai_api": "connected",
    "memory_system": "operational"
  },
  "performance": {
    "avg_response_time": 2.3,
    "requests_per_minute": 15,
    "error_rate": 0.02
  },
  "version": "2024.1.0",
  "uptime": "5d 12h 30m"
}
```

#### GET `/api/system/metrics`
Métricas detalhadas do sistema.

**Response:**
```json
{
  "requests": {
    "total": 15847,
    "success": 15522,
    "errors": 325,
    "avg_processing_time": 2.8
  },
  "memory": {
    "total_size_mb": 245,
    "entries": 1547,
    "avg_retrieval_time": 0.12
  },
  "agents": {
    "total_executions": 8765,
    "success_rate": 0.94,
    "avg_execution_time": 1.2
  }
}
```

---

## Estruturas de Dados

### Interaction Object
```json
{
  "id": 123,
  "timestamp": "2024-01-20T15:30:00Z",
  "interaction_type": "pipeline_execution",
  "user_prompt": "Pergunta do usuário",
  "agent_thoughts": "Processo de raciocínio",
  "agent_response": "Resposta final",
  "category": "research|coding|general",
  "tags": ["tag1", "tag2"],
  "importance_score": 8,
  "metadata": {
    "processing_time": 2.5,
    "agents_used": ["roko", "web"],
    "sources_count": 3
  }
}
```

### Agent Capability
```json
{
  "name": "web_search",
  "description": "Busca informações na web",
  "parameters": {
    "query": {
      "type": "string",
      "required": true,
      "description": "Termo de busca"
    },
    "num_results": {
      "type": "integer",
      "default": 5,
      "max": 20
    }
  }
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Descrição do erro",
    "details": {
      "field": "message",
      "issue": "Campo obrigatório não fornecido"
    }
  },
  "request_id": "req_123456789"
}
```

---

## Códigos de Erro

| Código | Descrição | Ação Sugerida |
|--------|-----------|---------------|
| `INVALID_REQUEST` | Solicitação mal formada | Verificar estrutura JSON |
| `MISSING_PARAMETER` | Parâmetro obrigatório ausente | Adicionar parâmetro necessário |
| `AGENT_UNAVAILABLE` | Agente não disponível | Tentar novamente mais tarde |
| `MEMORY_ERROR` | Erro no sistema de memória | Reportar para administrador |
| `RATE_LIMIT_EXCEEDED` | Limite de taxa excedido | Aguardar antes de nova requisição |
| `INTERNAL_ERROR` | Erro interno do servidor | Reportar para suporte |

---

## Rate Limiting

### Limites Padrão
- **Chat API**: 60 requisições por minuto por usuário
- **Memory API**: 120 requisições por minuto por usuário
- **System API**: 30 requisições por minuto por usuário

### Headers de Rate Limit
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642694400
```

---

## Webhooks

### Configuração
```json
{
  "url": "https://sua-app.com/webhook",
  "events": ["interaction_completed", "error_occurred"],
  "secret": "webhook_secret_key"
}
```

### Payload de Exemplo
```json
{
  "event": "interaction_completed",
  "timestamp": "2024-01-20T15:30:00Z",
  "data": {
    "interaction_id": 123,
    "user_prompt": "Pergunta do usuário",
    "response_preview": "Primeiras 100 palavras da resposta...",
    "processing_time": 2.5,
    "success": true
  },
  "signature": "sha256=..."
}
```

---

## SDKs e Bibliotecas

### Python SDK
```python
from roko_client import ROKOClient

client = ROKOClient(api_key="your_api_key")

# Chat simples
response = client.chat("Qual é a temperatura hoje?")
print(response.text)

# Busca na memória
memories = client.memory.search("Python programming", limit=5)
for memory in memories:
    print(memory.user_prompt)

# Status do sistema
health = client.system.health()
print(f"Status: {health.status}")
```

### JavaScript SDK
```javascript
import { ROKOClient } from 'roko-js-client';

const client = new ROKOClient({ apiKey: 'your_api_key' });

// Chat assíncrono
const response = await client.chat({
  message: "Explique machine learning",
  preferences: { style: 'detailed' }
});

console.log(response.text);

// Stream de resposta
client.chatStream("Conte uma história", (chunk) => {
  console.log(chunk.text);
});
```

---

## Exemplos de Uso

### 1. Chat Simples
```bash
curl -X POST https://seu-repl.replit.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explique o que é inteligência artificial"
  }'
```

### 2. Busca na Memória
```bash
curl -X GET "https://seu-repl.replit.app/api/memory/search?query=machine learning&limit=5"
```

### 3. Status do Sistema
```bash
curl -X GET https://seu-repl.replit.app/api/system/health
```

---

## Configuração para Desenvolvimento

### Variáveis de Ambiente
```bash
# Obrigatórias
OPENAI_API_KEY=sk-...

# Opcionais
ROKO_DEBUG=true
ROKO_LOG_LEVEL=INFO
ROKO_RATE_LIMIT=100
ROKO_MEMORY_CLEANUP_DAYS=30
```

### Inicialização Local
```python
from ROKO import ROKOPipeline

# Configuração para desenvolvimento
pipeline = ROKOPipeline(
    debug=True,
    log_level="DEBUG",
    memory_path=":memory:"  # Memória temporária
)

# Processamento de teste
result = pipeline.process_request("Teste de funcionamento")
print(result["final_response"])
```

## 🗃️ Sistema de Banco de Dados

### Arquitetura Híbrida
O ROKO utiliza uma arquitetura inovadora combinando:
- **SQLite** para dados estruturados
- **FAISS IndexHNSW** para busca semântica
- **Cache Triplo** (L1/L2/L3) para performance

### APIs de Memória Cognitiva

#### Gestão de Usuários
```python
from Memory import CognitiveMemory

memory = CognitiveMemory()

# Criar usuário
user_id = memory.create_user(
    username="alice",
    email="alice@example.com",
    password_hash="hashed_password"
)

# Buscar usuário
user = memory.get_user_by_username("alice")

# Atualizar último login
memory.update_last_login(user_id)
```

#### Interações e Contexto
```python
# Salvar interação
memory.save_interaction(
    user_id=1,
    interaction_type="pipeline_execution",
    user_prompt="Analise estes dados",
    agent_thoughts="Processando...",
    agent_response="Análise concluída",
    embedding=embedding_vector,
    category="analytics",
    tags="data,analysis",
    importance_score=8
)

# Buscar contexto relevante
context = memory.retrieve_context(
    query_embedding=query_vector,
    top_k=5,
    query_context={"category": "analytics"},
    use_reranking=True,
    user_id=1
)
```

#### Cache Ultra-Otimizado
```python
from Memory import UltraCacheSystem

cache = UltraCacheSystem()

# Buscar em cache (com fallback automático L1→L2→L3)
result = cache.get(
    key="analysis_query",
    content="Como analisar dados?",
    context="analytics"
)

# Armazenar em todas as camadas
cache.set(
    key="analysis_query",
    data=processed_result,
    content="Como analisar dados?",
    context="analytics"
)

# Estatísticas de performance
stats = cache.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']}")
print(f"Speedup: {stats['estimated_speedup']}x")
```

#### Busca e Filtragem
```python
# Buscar por categoria
results = memory.search_by_category("analytics", limit=10)

# Buscar por tags
results = memory.search_by_tags(["data", "ai"], limit=10)

# Últimos chats para contexto
chats = memory.get_last_chats(limit=3, user_id=1)
```

#### Manutenção e Estatísticas
```python
# Validar integridade do sistema
health = memory.validate_system_integrity()
print(f"Status: {health['status']}")

# Estatísticas detalhadas
stats = memory.get_memory_stats()
print(f"Total interactions: {stats['total_interactions']}")
print(f"Cache performance: {stats['cache_performance']}")

# Limpeza de dados antigos
deleted = memory.cleanup_old_memories(
    days_old=30,
    keep_important=True
)
```

### Performance Esperada
- **Query Time**: <50ms para busca semântica
- **Cache Hit Rate**: 85-95%
- **Speedup**: Até 100x com cache L1
- **Throughput**: ~1000 interações/segundo

📖 **Documentação Completa**: Veja [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) para detalhes técnicos completos.

---

Esta referência da API fornece todas as informações necessárias para integrar e utilizar o sistema ROKO programaticamente.
