
# 🤖 ROKO - Sistema de IA Autônoma

**ROKO** é um sistema de IA autônoma avançado com memória cognitiva persistente e capacidades de raciocínio complexo.

## ✨ **Principais Características**

- 🧠 **Memória Cognitiva**: Sistema persistente com busca semântica (FAISS + SQLite)
- 🔧 **Execução Autônoma**: Código Python, comandos shell, pesquisa web
- 🎯 **Agentes Especializados**: Pipeline de orquestração inteligente
- 🌐 **Interface Dupla**: Web (Flask) e CLI (Rich)
- ⚡ **Autocorreção**: Sistema avançado de detecção e correção de erros
- 📊 **Visualizações**: Geração automática de gráficos e relatórios

## 🚀 **Início Rápido**

### 1. Configuração da API Key
```bash
# No Replit Secrets, adicione:
OPENAI_API_KEY=sk-sua-chave-aqui
```

### 2. Execução

**Modo Web (Padrão):**
- Clique no botão **Run** no Replit
- Ou execute: `cd ROKO && python app.py`

**Modo CLI:**
- Execute workflow "CLI Mode"
- Ou execute: `cd ROKO && python app.py cli`

## 🏗️ **Arquitetura Otimizada**

```
ROKO/
├── Pipeline/           # Orquestração principal
│   ├── roko_pipeline.py    # Pipeline principal
│   └── orchestrator.py     # Coordenação de agentes
├── Agents/            # Agentes especializados (5 core)
│   ├── roko_agent.py      # Personalidade principal
│   ├── web_agent.py       # Pesquisa web
│   ├── code_agent.py      # Execução de código
│   ├── planner_agent.py   # Planejamento de tarefas
│   └── error_fix_agent.py # Autocorreção
├── Memory/            # Sistema de memória
│   └── cognitive_memory.py # Memória cognitiva
├── Interface/         # Interfaces de usuário
│   ├── web_interface.py   # Interface web
│   └── cli_interface.py   # Interface CLI
├── HMP/              # Sistema HMP avançado
└── app.py            # Ponto de entrada único
```

## 💡 **Exemplos de Uso**

```python
# Uso programático
from Pipeline import ROKOPipeline

roko = ROKOPipeline()
result = roko.process_request("Crie um gráfico dos dados de vendas")
print(result['final_response'])
```

**Comandos via interface:**
- `"Pesquise informações sobre IA em 2024"`
- `"Crie um gráfico de barras com dados [1,2,3,4,5]"`
- `"Analise o arquivo dados.csv e gere um relatório"`
- `"Execute o comando ls -la e explique o resultado"`

## 🔧 **Resolução de Problemas**

**Erro de API Key:**
```
⚠️ OPENAI_API_KEY não encontrada
```
→ Configure a chave nos Secrets do Replit

**Erro de Memória:**
```
❌ Falha na sincronização do índice
```
→ O sistema recria automaticamente o índice FAISS

**Interface não carrega:**
```
❌ Erro ao importar interface
```
→ Verifique se todas as dependências estão instaladas

## 📊 **Status do Sistema**

Para verificar a saúde da memória cognitiva:

```python
from Pipeline import ROKOPipeline
roko = ROKOPipeline()
stats = roko.get_memory_stats()
print(f"Interações na memória: {stats['total_interactions']}")
```

## 🚀 **Deploy no Replit**

O projeto está pré-configurado para Replit:
- ✅ Workflows otimizados
- ✅ Porta 5000 configurada
- ✅ Dependências automáticas
- ✅ Logs estruturados

**Para deploy em produção:**
1. Clique em "Deploy" no Replit
2. Escolha "Autoscale deployment"  
3. Configure domínio personalizado (opcional)
4. Deploy!

---

**💬 ROKO está pronto para ajudá-lo com tarefas complexas autonomamente!**

Versão: 2.0 (Otimizada)
Última atualização: $(date +%Y-%m-%d)
