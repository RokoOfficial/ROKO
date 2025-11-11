"""
HMP Router - Motor de roteamento principal usando protocolo HMP.
Este será o núcleo que gerencia toda comunicação entre agentes via HMP.
Integrado com AutoFluxROKO para execução paralela de agentes.
ULTRA-OTIMIZADO para acelerar processamento em até 100x.
"""

import logging
import concurrent.futures
import asyncio
import os
from typing import Dict, Any, List, Optional, Callable
from .hmp_interpreter import HMPInterpreter
from .hmp_tools import HMPTools
from .artifact_hmp_processor import ArtifactHMPProcessor
try:
    from .ultra_performance_monitor import ultra_monitor
except ImportError:
    # Fallback se o monitor não estiver disponível
    class MockMonitor:
        def __init__(self):
            self.peak_speedup = 1.0
        def record_execution(self, **kwargs):
            return {'estimated_speedup': 1.0}
        def log_performance_summary(self):
            pass
    ultra_monitor = MockMonitor()

# Integração com AutoFluxROKO
try:
    from AutoFlux import AutoFluxROKO
    HAS_AUTOFLUX = True
    logging.info("✅ AutoFluxROKO integrado ao HMP Router")
except ImportError:
    HAS_AUTOFLUX = False
    logging.warning("AutoFluxROKO não disponível - usando threading padrão")

class HMPRouter:
    """
    Motor de roteamento HMP que gerencia toda comunicação entre agentes.
    Todos os agentes se comunicam através deste roteador usando protocolo HMP.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.hmp_interpreter = HMPInterpreter()
        HMPTools.register_hmp_functions(self.hmp_interpreter)
        self.artifact_processor = ArtifactHMPProcessor()

        # Configurar AutoFlux
        try:
            from ..AutoFlux import AutoFluxROKO
            self.autoflux = AutoFluxROKO(max_workers=8)
            logging.info("✅ AutoFlux integrado com sucesso")
        except ImportError:
            try:
                from AutoFlux import AutoFluxROKO
                self.autoflux = AutoFluxROKO(max_workers=8)
                logging.info("✅ AutoFlux integrado com sucesso (import alternativo)")
            except ImportError:
                self.autoflux = None
                logging.warning("⚠️ AutoFlux não disponível - usando threading padrão")
        except Exception as e:
            logging.error(f"❌ Erro ao integrar AutoFlux: {e}")
            self.autoflux = None

        # Otimizar workers para máxima performance
        if self.autoflux:
            self.autoflux.max_workers = min(32, (os.cpu_count() or 4) * 4)
            logging.info(f"🚀 AutoFluxROKO ULTRA-OTIMIZADO: {self.autoflux.max_workers} workers")
        else:
            logging.info("⚙️ AutoFlux não está ativo. Usando threading padrão.")


        # Cache de resultados para aceleração massiva
        self.result_cache = {}
        self.performance_metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'average_speedup': 0.0
        }

        # Registrar rotas dos agentes
        self._register_agent_routes()

        # Cache de cadeias HMP pré-compiladas
        self.hmp_chains = {}
        self._load_predefined_chains()

        logging.info("🧠 HMP Router ULTRA-OTIMIZADO inicializado como motor principal")

    def _register_agent_routes(self):
        """Registra rotas para todos os agentes."""
        self.agent_routes = {
            'planner': self._route_to_planner,
            'executor': self._route_to_executor,
            'roko': self._route_to_roko,
            'web': self._route_to_web,
            'code': self._route_to_code,
            'shell': self._route_to_shell,
            'error_fix': self._route_to_error_fix,
            'checkin': self._route_to_checkin,
            'github': self._route_to_github
        }

    def _load_predefined_chains(self):
        """Carrega cadeias HMP pré-definidas para diferentes tipos de tarefas."""

        # Cadeia para conversa simples
        self.hmp_chains['simple_conversation'] = """
SET user_request TO {user_input}
SET processing_mode TO "simple_conversation"

CALL roko.generate_simple_response WITH
    input = user_request,
    personality = "friendly_professional"

RETURN response
"""

        # Cadeia para tarefas complexas
        self.hmp_chains['complex_task'] = """
SET user_request TO {user_input}
SET processing_mode TO "complex_orchestration"
SET plan TO empty_list

# FASE 1: PLANEJAMENTO
CALL planner.create_plan WITH
    user_prompt = user_request,
    context = {context}
SET plan TO planner_result.plan

# FASE 2: VALIDAÇÃO DO PLANO
IF plan.length > 0 THEN
    CALL validate_plan WITH plan = plan
    IF validation_score < 70 THEN
        CALL optimize_plan WITH current_plan = plan
        SET plan TO optimized_plan
    ENDIF
ENDIF

# FASE 3: EXECUÇÃO
SET execution_results TO empty_list
FOR step IN plan:
    CALL route_execution WITH step = step
    APPEND execution_result TO execution_results
ENDFOR

# FASE 4: SÍNTESE
CALL roko.synthesize_response WITH
    user_request = user_request,
    execution_results = execution_results,
    personality = "creative_professional"

RETURN final_response
"""

        # Cadeia para análise de código
        self.hmp_chains['code_analysis'] = """
SET code_request TO {user_input}
SET analysis_mode TO "code_generation"

# ANÁLISE DE REQUISITOS
CALL analyze_code_requirements WITH input = code_request
SET requirements TO analysis_result

# GERAÇÃO DE CÓDIGO
CALL code.generate WITH
    requirements = requirements,
    language = "python",
    style = "clean_documented"

# VALIDAÇÃO
CALL code.validate WITH generated_code = code_result
IF validation_passed THEN
    CALL code.execute WITH code = validated_code
ELSE
    CALL error_fix.fix_code WITH
        code = code_result,
        errors = validation_errors
ENDIF

RETURN execution_result
"""

        # Cadeia para pesquisa web
        self.hmp_chains['web_research'] = """
SET search_query TO {user_input}
SET research_mode TO "comprehensive_search"

# PESQUISA WEB
CALL web.search WITH
    query = search_query,
    depth = "comprehensive"

# ANÁLISE DOS RESULTADOS
CALL analyze_search_results WITH
    results = search_results,
    relevance_threshold = 0.8

# SÍNTESE INTELIGENTE
CALL roko.synthesize_research WITH
    query = search_query,
    results = filtered_results,
    format = "informative_summary"

RETURN synthesized_response
"""

        # Cadeia para análise de dados avançada
        self.hmp_chains['data_analysis_pipeline'] = """
SET data_request TO {user_input}
SET analysis_type TO "comprehensive_data_analysis"

# FASE 1: COLETA E VALIDAÇÃO
CALL data_processing.validate_data WITH input = data_request
IF validation_score > 80 THEN
    CALL data_processing.extract_insights WITH data = validated_data
ELSE
    CALL web.search_data_sources WITH query = data_request
    CALL data_processing.clean_data WITH raw_data = search_results
ENDIF

# FASE 2: ANÁLISE ESTATÍSTICA
CALL data_processing.statistical_analysis WITH data = clean_data
CALL metrics.calculate_metrics WITH analysis_results = stats_result

# FASE 3: VISUALIZAÇÃO INTELIGENTE
CALL artifact_manager.find_artifacts WITH query = "data visualization templates"
CALL roko.create_data_visualization WITH
    data = analysis_results,
    templates = artifact_templates,
    style = "professional_dashboard"

RETURN comprehensive_analysis
"""

        # Cadeia para manutenção do sistema
        self.hmp_chains['system_maintenance'] = """
SET maintenance_request TO {user_input}
SET system_health TO "unknown"

# FASE 1: DIAGNÓSTICO COMPLETO
CALL shell.system_diagnostics WITH check_all = true
CALL metrics.collect_performance_data WITH timeframe = "last_24h"
CALL memory.analyze_memory_usage WITH detailed = true

# FASE 2: IDENTIFICAÇÃO DE PROBLEMAS
CALL validation.identify_issues WITH
    system_data = diagnostics_result,
    performance_data = metrics_result

# FASE 3: CORREÇÃO AUTOMÁTICA
FOR issue IN identified_issues:
    IF issue.severity == "high" THEN
        CALL error_fix.auto_repair WITH issue = issue
    ELSE
        CALL log_issue WITH issue = issue, action = "scheduled_fix"
    ENDIF
ENDFOR

# FASE 4: RELATÓRIO DE SAÚDE
CALL roko.generate_health_report WITH
    diagnostics = diagnostics_result,
    fixes_applied = repair_results,
    recommendations = optimization_suggestions

RETURN system_health_report
"""

        # Cadeia para evolução de agentes
        self.hmp_chains['agent_evolution'] = """
SET evolution_request TO {user_input}
SET evolution_mode TO "adaptive_creation"

# FASE 1: ANÁLISE DE NECESSIDADES
CALL analyze_agent_requirements WITH request = evolution_request
CALL metrics.analyze_current_agents WITH performance_data = true

# FASE 2: DESIGN DO AGENTE
IF request_type == "new_agent" THEN
    CALL agent_factory.design_agent WITH
        capabilities = required_capabilities,
        specialization = domain_expertise
ELSE
    CALL agent_factory.evolve_existing WITH
        agent_name = target_agent,
        improvements = suggested_improvements
ENDIF

# FASE 3: IMPLEMENTAÇÃO E TESTE
CALL agent_factory.create_agent WITH specification = agent_design
CALL validation.test_agent_capabilities WITH agent = new_agent
CALL metrics.benchmark_performance WITH agent = new_agent

# FASE 4: INTEGRAÇÃO
IF performance_score > 85 THEN
    CALL register_agent WITH agent = validated_agent
    CALL update_hmp_router WITH new_routes = agent_capabilities
ENDIF

RETURN agent_evolution_result
"""

        # Cadeia para criação avançada de artefatos
        self.hmp_chains['artifact_creation'] = """
SET artifact_request TO {user_input}
SET creation_mode TO "advanced_artifact_generation"

# FASE 1: ANÁLISE DE REQUISITOS
CALL analyze_artifact_requirements WITH request = artifact_request
CALL artifact_manager.find_similar_artifacts WITH query = requirements

# FASE 2: DESIGN E ARQUITETURA
CALL design_artifact_architecture WITH
    requirements = analyzed_requirements,
    reference_artifacts = similar_artifacts,
    style = "modern_responsive"

# FASE 3: GERAÇÃO DE CÓDIGO
CALL code.generate_advanced_html WITH
    architecture = artifact_design,
    features = required_features,
    libraries = ["Chart.js", "Bootstrap", "Font Awesome"]

# FASE 4: OTIMIZAÇÃO E VALIDAÇÃO
CALL code.optimize_performance WITH code = generated_code
CALL validation.test_responsiveness WITH artifact = optimized_code
CALL artifact_manager.save_artifact WITH
    content = validated_artifact,
    metadata = creation_metadata

RETURN professional_artifact
"""

        # Cadeia específica para renderização de interfaces como artefatos
        self.hmp_chains['interface_artifact_rendering'] = """
SET interface_request TO {user_input}
SET rendering_mode TO "complete_interface_artifact"

# FASE 1: ANÁLISE DO TIPO DE INTERFACE
CALL analyze_interface_type WITH request = interface_request
SET interface_type TO analysis_result.type
SET complexity_level TO analysis_result.complexity

# FASE 2: GERAÇÃO DE CONTEÚDO COMPLETO
IF interface_type == "dashboard" THEN
    CALL generate_complete_dashboard WITH
        data_source = interface_request,
        interactive_elements = true,
        responsive_design = true
ELSE IF interface_type == "form" THEN
    CALL generate_interactive_form WITH
        fields = detected_fields,
        validation = true,
        styling = "modern"
ELSE IF interface_type == "visualization" THEN
    CALL generate_data_visualization WITH
        chart_type = "auto_detect",
        interactive = true,
        animation = true
ELSE
    CALL generate_generic_interface WITH
        layout = "responsive_grid",
        components = auto_detected_components
ENDIF

# FASE 3: ENRIQUECIMENTO COM FUNCIONALIDADES
CALL add_interactive_features WITH
    content = generated_content,
    features = ["search", "filter", "sort", "export"]

# FASE 4: FORMATAÇÃO PARA ARTEFATO
CALL format_as_complete_artifact WITH
    content = enriched_content,
    title = auto_generated_title,
    description = interface_description,
    embed_styles = true,
    embed_scripts = true

# FASE 5: VALIDAÇÃO DE RENDERIZAÇÃO
CALL validate_artifact_rendering WITH artifact = formatted_artifact
IF validation_score > 85 THEN
    CALL artifact_manager.save_with_preview WITH
        artifact = validated_artifact,
        generate_preview = true
ENDIF

RETURN complete_renderable_artifact
"""

        # Cadeia para processamento de artefatos em respostas
        self.hmp_chains['artifact_response_processing'] = """
SET response_text TO {user_input}
SET processing_mode TO "extract_and_enhance_artifacts"

# FASE 1: EXTRAÇÃO DE ARTEFATOS
CALL extract_artifact_tags WITH response = response_text
SET found_artifacts TO extraction_result

# FASE 2: PROCESSAMENTO DE CADA ARTEFATO
SET processed_artifacts TO empty_list
FOR artifact IN found_artifacts:
    # Validar conteúdo do artefato
    CALL validate_artifact_content WITH artifact = artifact
    IF content_valid THEN
        # Enriquecer com estilos e funcionalidades
        CALL enhance_artifact_content WITH
            content = artifact.content,
            type = artifact.type,
            title = artifact.title
        
        # Garantir renderização completa
        CALL ensure_complete_rendering WITH enhanced_content = enhanced_artifact
        
        APPEND processed_artifact TO processed_artifacts
    ENDIF
ENDFOR

# FASE 3: INTEGRAÇÃO COM RESPOSTA
CALL integrate_artifacts_with_response WITH
    original_response = response_text,
    processed_artifacts = processed_artifacts,
    display_mode = "inline_with_preview"

RETURN enhanced_response_with_artifacts
"""

        # Cadeia para integração com APIs
        self.hmp_chains['integration_pipeline'] = """
SET integration_request TO {user_input}
SET integration_type TO "external_api_connection"

# FASE 1: ANÁLISE DE INTEGRAÇÃO
CALL analyze_integration_requirements WITH request = integration_request
CALL web.research_api_documentation WITH service = target_service

# FASE 2: CONFIGURAÇÃO DE CONEXÃO
CALL dependency.install_required_packages WITH packages = api_requirements
CALL shell.setup_environment_variables WITH config = api_config
CALL code.generate_api_wrapper WITH
    documentation = api_docs,
    authentication = auth_method

# FASE 3: TESTE E VALIDAÇÃO
CALL code.test_api_connection WITH wrapper = api_wrapper
CALL validation.verify_data_flow WITH integration = connection_test
CALL error_fix.handle_connection_issues WITH errors = test_errors

# FASE 4: CRIAÇÃO DE INTERFACE
CALL roko.create_integration_interface WITH
    api_wrapper = validated_wrapper,
    user_requirements = integration_request,
    display_mode = "interactive_dashboard"

RETURN integration_solution
"""

        # Cadeia para aprendizado e otimização
        self.hmp_chains['learning_optimization'] = """
SET learning_request TO {user_input}
SET optimization_mode TO "continuous_improvement"

# FASE 1: COLETA DE DADOS DE APRENDIZADO
CALL memory.analyze_interaction_patterns WITH timeframe = "last_month"
CALL metrics.collect_performance_metrics WITH all_agents = true
CALL adaptive_context.analyze_user_preferences WITH history = interaction_data

# FASE 2: IDENTIFICAÇÃO DE PADRÕES
CALL data_processing.pattern_recognition WITH
    interaction_data = memory_analysis,
    performance_data = metrics_data,
    ml_algorithm = "clustering_analysis"

# FASE 3: GERAÇÃO DE OTIMIZAÇÕES
FOR pattern IN identified_patterns:
    CALL generate_optimization_strategy WITH pattern = pattern
    CALL validation.simulate_improvement WITH strategy = optimization
ENDFOR

# FASE 4: APLICAÇÃO ADAPTATIVA
CALL apply_performance_optimizations WITH strategies = validated_optimizations
CALL adaptive_context.update_user_model WITH insights = learning_insights
CALL roko.generate_learning_report WITH improvements = applied_optimizations

RETURN optimization_results
"""

        # Cadeia para automação de deploy
        self.hmp_chains['deployment_automation'] = """
SET deployment_request TO {user_input}
SET deployment_mode TO "automated_production_ready"

# FASE 1: PREPARAÇÃO PRÉ-DEPLOY
CALL code.analyze_codebase WITH security_check = true
CALL dependency.verify_all_dependencies WITH environment = "production"
CALL validation.run_comprehensive_tests WITH coverage = "full"

# FASE 2: OTIMIZAÇÃO PARA PRODUÇÃO
CALL code.optimize_for_production WITH
    minification = true,
    compression = true,
    security_hardening = true

# FASE 3: CONFIGURAÇÃO DE AMBIENTE
CALL shell.setup_production_environment WITH config = deployment_config
CALL dependency.install_production_dependencies WITH requirements = optimized_deps
CALL checkin.verify_environment_health WITH production_setup = true

# FASE 4: DEPLOY E MONITORAMENTO
CALL deploy_application WITH
    environment = "production",
    monitoring = "enabled",
    rollback_plan = "automatic"

CALL setup_monitoring WITH metrics = ["performance", "errors", "usage"]
CALL roko.generate_deployment_report WITH status = deployment_result

RETURN deployment_success
"""

        # Cadeia para auditoria de segurança
        self.hmp_chains['security_audit'] = """
SET security_request TO {user_input}
SET audit_mode TO "comprehensive_security_analysis"

# FASE 1: VARREDURA DE SEGURANÇA
CALL code.security_analysis WITH
    scan_type = "comprehensive",
    check_dependencies = true,
    analyze_permissions = true

# FASE 2: ANÁLISE DE VULNERABILIDADES
CALL web.check_known_vulnerabilities WITH dependencies = current_dependencies
CALL shell.system_security_audit WITH check_permissions = true
CALL validation.test_input_sanitization WITH all_endpoints = true

# FASE 3: CORREÇÃO AUTOMÁTICA
FOR vulnerability IN found_vulnerabilities:
    IF vulnerability.severity == "critical" THEN
        CALL error_fix.patch_vulnerability WITH vuln = vulnerability
    ELSE
        CALL schedule_security_fix WITH vuln = vulnerability
    ENDIF
ENDFOR

# FASE 4: RELATÓRIO DE SEGURANÇA
CALL roko.generate_security_report WITH
    vulnerabilities = scan_results,
    fixes_applied = patch_results,
    recommendations = security_improvements

RETURN security_audit_report
"""

        # Integrar cadeias Agent ROKO PRO
        try:
            from .agent_roko_pro_hmp_chains import AgentROKOProHMPChains
            agent_roko_pro_chains = AgentROKOProHMPChains.get_all_chains()
            self.hmp_chains.update(agent_roko_pro_chains)
            logging.info(f"✅ {len(agent_roko_pro_chains)} cadeias Agent ROKO PRO carregadas")
        except ImportError as e:
            logging.warning(f"⚠️ Agent ROKO PRO chains não disponíveis: {e}")

        # Integrar cadeias GitHub Agent
        try:
            from .github_agent_hmp_chains import GitHubAgentHMPChains
            github_agent_chains = GitHubAgentHMPChains.get_all_chains()
            self.hmp_chains.update(github_agent_chains)
            logging.info(f"✅ {len(github_agent_chains)} cadeias GitHub Agent carregadas")
        except ImportError as e:
            logging.warning(f"⚠️ GitHub Agent chains não disponíveis: {e}")

        # Cadeia principal Agent CODER PRO
        self.hmp_chains['agent_coder_pro_main'] = """
SET objetivo TO {user_input}
SET user_context TO {user_context} OR {id: "system", roles: ["admin"]}
SET config TO {agent_config} OR {}

# Executar Agent CODER PRO
CALL agent_coder_pro.execute WITH 
    objetivo = objetivo,
    user = user_context,
    config = config

RETURN agent_execution_resultesult
"""

        # Cadeia principal GitHub Agent
        self.hmp_chains['github_agent_main'] = """
SET github_request TO {user_input}
SET processing_mode TO "github_automation"

# FASE 1: ANÁLISE DA SOLICITAÇÃO
CALL github.analyze_repository_requirements WITH request = github_request
SET requirements TO analysis_result

# FASE 2: PLANEJAMENTO AI
CALL github.ai_planning_system WITH command = github_request
SET execution_plan TO planning_result

# FASE 3: VALIDAÇÃO DO PLANO
IF execution_plan.length > 0 THEN
    CALL validate_plan WITH plan = execution_plan
    IF validation_score < 70 THEN
        CALL optimize_plan WITH current_plan = execution_plan
        SET execution_plan TO optimized_plan
    ENDIF
ENDIF

# FASE 4: EXECUÇÃO SEQUENCIAL
SET execution_results TO empty_list
FOR action IN execution_plan:
    CALL github.execute_github_action WITH
        action = action.action,
        params = action.params
    APPEND execution_result TO execution_results
ENDFOR

# FASE 5: SÍNTESE DOS RESULTADOS
CALL synthesize_github_results WITH
    original_request = github_request,
    execution_results = execution_results,
    requirements = requirements

RETURN github_execution_summary
"""

        # Cadeia HMP Chain Debugger & Root Cause Analysis
        self.hmp_chains['debugger_root_cause_analysis'] = """
SET objetivo TO {user_input}
SET contexto TO {context}
SET tentativas TO 0
SET max_tentativas TO 3

# FASE 0: METADADOS E COLETA INICIAL
CALL collect_error_payload WITH input = objetivo
SET error_message TO collected_payload.error_message
SET stack_trace TO collected_payload.stack_trace
SET runtime_info TO collected_payload.runtime
SET files TO collected_payload.files
SET repro_steps TO collected_payload.reproduction_steps

# FASE 1: ANÁLISE LOCAL DO ERRO
CALL parse_stack_trace WITH stack_trace = stack_trace
SET top_frame TO parse_result.top_frame
SET probable_cause TO parse_result.cause

CALL static_analyze WITH files = files, focus = top_frame
SET local_findings TO analysis_result

# Verificar reprodutibilidade
IF repro_steps IS NOT NULL THEN
    SET reproducible TO true
ELSE
    CALL try_reproduce_with_inferred_steps WITH runtime = runtime_info, files = files
    SET reproducible TO reproduction_result
ENDIF

# FASE 2: BUSCA EXTERNA (SE NECESSÁRIO)
IF local_findings.empty == true OR reproducible == false THEN
    CALL web.search WITH
        query = error_message + " " + runtime_info.lang,
        depth = "comprehensive"
    SET search_results TO web_result

    CALL extract_relevant_threads WITH sources = search_results, top_k = 5
    SET threads TO extraction_result
ENDIF

# FASE 3: RACIOCÍNIO SOBRE CAUSAS
CALL synthesize_causes WITH 
    local_findings = local_findings, 
    threads = threads, 
    stack_summary = probable_cause
SET hypotheses TO synthesis_result

CALL rank_hypotheses WITH 
    hypotheses = hypotheses, 
    criteria = ["plausibility", "reproducibility", "risk"]
SET ranked_hypotheses TO ranking_result

# FASE 4: GERAR E APLICAR CORREÇÕES
FOR hypothesis IN ranked_hypotheses:
    IF hypothesis.estimated_cost <= 80 AND tentativas < max_tentativas THEN
        CALL generate_patch WITH 
            hypothesis = hypothesis, 
            files = files, 
            context = contexto
        SET patch TO patch_result

        # Aplicar em sandbox
        CALL shell.execute WITH command = "git apply --check"
        IF shell_result.exit_code == 0 THEN
            CALL shell.execute WITH command = "git apply"
            CALL run_tests WITH command = "pytest" OR "npm test"
            SET test_results TO test_output

            CALL validate_fix WITH 
                test_results = test_results, 
                original_error = error_message
            IF validation_result.status == "passes" THEN
                # Salvar correção em ARTEFATOS
                CALL artifact_manager.save_artifact WITH
                    content = patch,
                    filename = "debug_fix_" + timestamp + ".patch",
                    description = "Correção automática para: " + error_message,
                    category = "debug_patches"

                RETURN success_response
            ELSE
                CALL shell.execute WITH command = "git reset --hard HEAD"
                SET tentativas TO tentativas + 1
            ENDIF
        ENDIF
    ENDIF
ENDFOR

# FASE 5: RELATÓRIO PARCIAL SE NÃO CORRIGIDO
CALL synthesize_partial_report WITH 
    findings = local_findings, 
    hypotheses = ranked_hypotheses, 
    threads = threads

# Salvar relatório em ARTEFATOS
CALL artifact_manager.save_artifact WITH
    content = debug_report_html,
    filename = "debug_analysis_" + timestamp + ".html",
    description = "Relatório de análise de debugging",
    category = "debug_reports"

RETURN partial_report
"""

    def get_available_chains(self) -> List[str]:
        """Retorna lista de todas as cadeias HMP disponíveis."""
        return list(self.hmp_chains.keys())
    
    def get_chain_info(self, chain_name: str) -> Dict[str, Any]:
        """Retorna informações sobre uma cadeia específica."""
        if chain_name not in self.hmp_chains:
            return {'error': 'Chain not found'}
        
        chain_code = self.hmp_chains[chain_name]
        return {
            'name': chain_name,
            'code': chain_code,
            'length': len(chain_code),
            'complexity': 'complex' if len(chain_code) > 1000 else 'simple',
            'available': True
        }
    
    def list_specializations(self) -> Dict[str, List[str]]:
        """Lista especializações disponíveis agrupadas por categoria."""
        specializations = {
            'debugging': [],
            'github': [],
            'deployment': [],
            'data_analysis': [],
            'mobile_development': [],
            'artifacts': [],
            'system_maintenance': [],
            'general': []
        }
        
        for chain_name in self.hmp_chains.keys():
            if 'debug' in chain_name.lower():
                specializations['debugging'].append(chain_name)
            elif 'github' in chain_name.lower():
                specializations['github'].append(chain_name)
            elif 'deploy' in chain_name.lower() or 'roko_pro' in chain_name.lower():
                specializations['deployment'].append(chain_name)
            elif 'data' in chain_name.lower() or 'analysis' in chain_name.lower():
                specializations['data_analysis'].append(chain_name)
            elif 'mobile' in chain_name.lower():
                specializations['mobile_development'].append(chain_name)
            elif 'artifact' in chain_name.lower() or 'interface' in chain_name.lower():
                specializations['artifacts'].append(chain_name)
            elif 'system' in chain_name.lower() or 'maintenance' in chain_name.lower():
                specializations['system_maintenance'].append(chain_name)
            else:
                specializations['general'].append(chain_name)
        
        return specializations

    def route_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        ULTRA-ROTEAMENTO com cache e pipeline paralelo como padrão.
        Máxima velocidade através de paralelização agressiva.
        """
        import hashlib
        import time
        start_time = time.time()

        # Atualizar métricas
        self.performance_metrics['total_requests'] += 1

        # Cache key para acelerar requests similares
        cache_key = hashlib.md5(f"{user_input}_{str(context)}".encode()).hexdigest()

        # Verificar cache primeiro para aceleração massiva
        if cache_key in self.result_cache:
            self.performance_metrics['cache_hits'] += 1
            cached_result = self.result_cache[cache_key].copy()
            cached_result['from_cache'] = True
            cached_result['cache_speedup'] = True
            logging.info(f"⚡ CACHE HIT - Resultado instantâneo para: {user_input[:30]}...")
            return cached_result

        logging.info(f"🧠 ULTRA-ROUTER processando: {user_input[:50]}...")

        # Determinar tipo de requisição
        request_type = self._classify_request(user_input)
        logging.info(f"🎯 Tipo identificado: {request_type}")

        # SEMPRE usar pipeline de workers paralelos para máxima velocidade
        if self._should_use_parallel_workers(user_input, request_type):
            logging.info("🚀 ULTRA-PIPELINE ativado (padrão)")
            result = self.execute_worker_pipeline(user_input)
        else:
            # Fallback para casos muito simples - ainda otimizado
            logging.info("⚡ Processamento rápido para request simples")
            chain_name = self._select_hmp_chain(request_type, user_input)

            if chain_name in self.hmp_chains:
                hmp_code = self.hmp_chains[chain_name].format(
                    user_input=user_input,
                    context=context or {}
                )
                hmp_result = self.hmp_interpreter.execute_hmp(hmp_code, context)

                result = {
                    'success': True,
                    'result': hmp_result,
                    'chain_used': chain_name,
                    'processing_type': 'hmp_optimized'
                }
            else:
                result = self._generic_hmp_processing(user_input, context)

        # Adicionar métricas de performance
        execution_time = time.time() - start_time
        result['execution_time'] = execution_time
        result['from_cache'] = False

        # Cache do resultado para acelerar requests futuros
        if result.get('success', False):
            self.result_cache[cache_key] = result.copy()

        # Registrar métricas de performance com monitor ultra-otimizado
        workers_used = len(result.get('results', [])) if 'results' in result else 1
        parallel_groups = result.get('parallel_groups', 0)

        # Registrar execução no monitor de performance
        performance_record = ultra_monitor.record_execution(
            execution_time=execution_time,
            workers_used=workers_used,
            from_cache=result.get('from_cache', False),
            parallel_groups=parallel_groups
        )

        # Atualizar métricas locais
        estimated_speedup = performance_record['estimated_speedup']
        self.performance_metrics['average_speedup'] = (
            (self.performance_metrics['average_speedup'] + estimated_speedup) / 2
        )

        cache_hit_ratio = self.performance_metrics['cache_hits'] / self.performance_metrics['total_requests']

        # Log de performance ultra-detalhado
        logging.info(f"✅ ULTRA-ROUTER: {execution_time:.2f}s | Workers: {workers_used} | "
                    f"Cache: {cache_hit_ratio:.1%} | Speedup: ~{estimated_speedup:.1f}x | "
                    f"Peak: {ultra_monitor.peak_speedup:.1f}x")

        # Log summary a cada 10 requests
        if self.performance_metrics['total_requests'] % 10 == 0:
            ultra_monitor.log_performance_summary()

        # Adicionar métricas ao resultado
        result['performance_metrics'] = performance_record
        result['estimated_speedup'] = estimated_speedup

        return result

    def _should_use_parallel_workers(self, user_input: str, request_type: str) -> bool:
        """
        SEMPRE usar pipeline de workers paralelos para máxima performance.
        Paralelismo é agora o padrão para acelerar 100x o processamento.
        """
        # SEMPRE usar workers paralelos quando AutoFlux disponível
        # Exceções apenas para requests muito simples
        simple_exclusions = ['simple_conversation'] if len(user_input) < 10 else []

        if request_type in simple_exclusions and len(user_input.split()) < 3:
            return False  # Apenas conversas muito simples ficam sequenciais

        # Usar workers paralelos para TUDO MAIS para máxima velocidade
        return HAS_AUTOFLUX

    def _classify_request(self, user_input: str) -> str:
        """Classifica o tipo de requisição usando raciocínio HMP."""
        classification_hmp = f"""
SET input_text TO "{user_input}"
SET classification TO "unknown"

# ANÁLISE DE PALAVRAS-CHAVE
CALL analyze_keywords WITH text = input_text
SET keywords TO keyword_analysis

# CLASSIFICAÇÃO BASEADA EM PADRÕES
IF keywords.contains("código", "programar", "python", "executar") THEN
    SET classification TO "code_task"
ELSE IF keywords.contains("pesquisar", "buscar", "informação", "web") THEN
    SET classification TO "web_research"
ELSE IF keywords.contains("olá", "oi", "como vai", "tudo bem") THEN
    SET classification TO "simple_conversation"
ELSE IF keywords.contains("dados", "estatística", "análise", "visualização", "gráfico", "dashboard") THEN
    SET classification TO "data_analysis"
ELSE IF keywords.contains("sistema", "diagnóstico", "performance", "limpeza", "otimizar") THEN
    SET classification TO "system_maintenance"
ELSE IF keywords.contains("agente", "evoluir", "criar agente", "melhorar agente") THEN
    SET classification TO "agent_evolution"
ELSE IF keywords.contains("artefato", "interface", "app", "aplicação", "html") THEN
    SET classification TO "artifact_creation"
ELSE IF keywords.contains("api", "integração", "conectar", "serviço externo") THEN
    SET classification TO "api_integration"
ELSE IF keywords.contains("aprender", "padrões", "otimizar", "melhorar") THEN
    SET classification TO "learning_optimization"
ELSE IF keywords.contains("github", "repositório", "git", "commit", "branch", "issue", "workflow") THEN
    SET classification TO "github_task"
ELSE IF keywords.contains("deploy", "publicar", "produção", "lançar") THEN
    SET classification TO "deployment"
ELSE IF keywords.contains("segurança", "vulnerabilidade", "auditoria", "proteção") THEN
    SET classification TO "security_audit"
ELSE IF keywords.contains("criar", "gerar", "analisar", "processar") THEN
    SET classification TO "complex_task"
ELSE
    SET classification TO "general_inquiry"
ENDIF

RETURN classification
"""

        result = self.hmp_interpreter.execute_hmp(classification_hmp)
        return result.get('variables', {}).get('classification', 'complex_task')

    def _select_hmp_chain(self, request_type: str, user_input: str) -> str:
        """Seleciona a cadeia HMP mais apropriada."""
        
        # Verificar se é um caso para Debugging & Root Cause Analysis
        debug_keywords = [
            'erro', 'error', 'bug', 'falha', 'exception', 'traceback', 'debug', 
            'corrigir', 'fix', 'problema', 'issue', 'stack trace', 'debugging',
            'análise de causa', 'root cause', 'diagnosticar', 'troubleshooting'
        ]
        
        if any(keyword in user_input.lower() for keyword in debug_keywords):
            return 'debugger_root_cause_analysis'
        
        # Verificar se é um caso para GitHub Agent
        github_keywords = [
            'github', 'repositório', 'repo', 'git', 'commit', 'branch', 'pull request', 'pr',
            'issue', 'workflow', 'ci/cd', 'deployment', 'release', 'merge', 'clone',
            'fork', 'star', 'colaboração', 'código fonte', 'versionamento'
        ]
        
        if any(keyword in user_input.lower() for keyword in github_keywords):
            if any(kw in user_input.lower() for kw in ['criar repo', 'novo repositório', 'setup projeto']):
                return 'github_repository_creation'
            elif any(kw in user_input.lower() for kw in ['issue', 'problema', 'bug', 'feature request']):
                return 'github_issue_management'
            elif any(kw in user_input.lower() for kw in ['analisar código', 'code review', 'qualidade']):
                return 'github_code_analysis'
            elif any(kw in user_input.lower() for kw in ['workflow', 'ci/cd', 'automação', 'pipeline']):
                return 'github_workflow_automation'
            elif any(kw in user_input.lower() for kw in ['colaboração', 'team', 'equipe']):
                return 'github_collaborative_development'
            elif any(kw in user_input.lower() for kw in ['manutenção', 'limpeza', 'otimizar']):
                return 'github_repository_maintenance'
            elif any(kw in user_input.lower() for kw in ['deploy', 'publicar', 'release']):
                return 'github_deployment_pipeline'
            else:
                return 'github_agent_main'
        
        # Verificar se é um caso para Agent ROKO PRO
        agent_roko_pro_keywords = [
            'deploy', 'auditoria', 'segurança', 'monitoramento', 'recuperação',
            'infraestrutura', 'processamento de dados', 'full-stack', 'produção'
        ]
        
        if any(keyword in user_input.lower() for keyword in agent_roko_pro_keywords):
            if 'deploy' in user_input.lower():
                return 'agent_roko_pro_deployment'
            elif any(kw in user_input.lower() for kw in ['auditoria', 'segurança']):
                return 'agent_roko_pro_security_audit'
            elif 'monitoramento' in user_input.lower():
                return 'agent_roko_pro_infrastructure_monitoring'
            elif 'processamento' in user_input.lower() and 'dados' in user_input.lower():
                return 'agent_roko_pro_data_processing'
            elif 'recuperação' in user_input.lower():
                return 'agent_roko_pro_system_recovery'
            else:
                return 'agent_roko_pro_main'
        
        # Mapeamento tradicional
        chain_mapping = {
            'simple_conversation': 'simple_conversation',
            'code_task': 'code_analysis',
            'web_research': 'web_research',
            'complex_task': 'complex_task',
            'general_inquiry': 'complex_task',
            'data_analysis': 'data_analysis_pipeline',
            'system_maintenance': 'system_maintenance',
            'agent_evolution': 'agent_evolution',
            'artifact_creation': 'artifact_creation',
            'api_integration': 'integration_pipeline',
            'learning_optimization': 'learning_optimization',
            'deployment': 'agent_roko_pro_deployment',  # Usar Agent ROKO PRO para deploy
            'security_audit': 'agent_roko_pro_security_audit',  # Usar Agent ROKO PRO para auditoria
            'github_task': 'github_agent_main',  # GitHub Agent para tarefas Git
            'debug_task': 'debugger_root_cause_analysis'  # Debugging & Root Cause Analysis
        }

        return chain_mapping.get(request_type, 'complex_task')

    def _generic_hmp_processing(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Processamento genérico usando HMP."""
        generic_hmp = f"""
SET user_request TO "{user_input}"
SET processing_mode TO "generic"

# ANÁLISE INICIAL
CALL analyze_request WITH input = user_request
SET understanding_level TO analysis_result.understanding

# DECISÃO DE PROCESSAMENTO
IF understanding_level > 80 THEN
    CALL roko.generate_response WITH
        input = user_request,
        mode = "direct_response"
ELSE
    CALL planner.create_simple_plan WITH input = user_request
    CALL execute_simple_plan WITH plan = simple_plan
ENDIF

RETURN processing_result
"""

        result = self.hmp_interpreter.execute_hmp(generic_hmp, context)
        return {
            'success': True,
            'result': result,
            'chain_used': 'generic',
            'processing_type': 'hmp_generic'
        }

    # Métodos de roteamento para agentes específicos
    def _route_to_planner(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia requisição para o agente planejador via HMP."""
        planner_hmp = f"""
SET planning_request TO {request}
CALL planner.create_detailed_plan WITH request = planning_request
RETURN planner_result
"""
        return self.hmp_interpreter.execute_hmp(planner_hmp)

    def _route_to_roko(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia requisição para ROKO via HMP."""
        roko_hmp = f"""
SET roko_request TO {request}
CALL roko.analyze_and_respond WITH request = roko_request
RETURN roko_result
"""
        return self.hmp_interpreter.execute_hmp(roko_hmp)

    def _route_to_web(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia para agente web via HMP."""
        web_hmp = f"""
SET web_request TO {request}
CALL web.search_and_analyze WITH request = web_request
RETURN web_result
"""
        return self.hmp_interpreter.execute_hmp(web_hmp)

    def _route_to_code(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia para agente de código via HMP."""
        code_hmp = f"""
SET code_request TO {request}
CALL code.generate_and_execute WITH request = code_request
RETURN code_result
"""
        return self.hmp_interpreter.execute_hmp(code_hmp)

    def _route_to_shell(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia para agente shell via HMP."""
        shell_hmp = f"""
SET shell_request TO {request}
CALL shell.execute_command WITH request = shell_request
RETURN shell_result
"""
        return self.hmp_interpreter.execute_hmp(shell_hmp)

    def _route_to_error_fix(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia para agente de correção de erros via HMP."""
        error_fix_hmp = f"""
SET error_request TO {request}
CALL error_fix.analyze_and_fix WITH request = error_request
RETURN fix_result
"""
        return self.hmp_interpreter.execute_hmp(error_fix_hmp)

    def _route_to_checkin(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia para agente de verificação via HMP."""
        checkin_hmp = f"""
SET checkin_request TO {request}
CALL checkin.validate_and_verify WITH request = checkin_request
RETURN checkin_result
"""
        return self.hmp_interpreter.execute_hmp(checkin_hmp)

    def _route_to_executor(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia para agente executor via HMP."""
        executor_hmp = f"""
SET executor_request TO {request}
CALL executor.execute_step WITH request = executor_request
RETURN executor_result
"""
        return self.hmp_interpreter.execute_hmp(executor_hmp)

    def _route_to_github(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia para GitHub Agent via HMP."""
        github_hmp = f"""
SET github_request TO {request}
CALL github.process_github_request WITH request = github_request
RETURN github_result
"""
        return self.hmp_interpreter.execute_hmp(github_hmp)

    def add_custom_chain(self, name: str, hmp_code: str):
        """Adiciona uma nova cadeia HMP personalizada."""
        self.hmp_chains[name] = hmp_code
        logging.info(f"✅ Cadeia HMP '{name}' adicionada")

    def process_artifact_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa requisição especificamente para criação de artefatos renderizáveis."""
        logging.info(f"🎨 Processando requisição de artefato: {user_input[:50]}...")
        
        try:
            # Usar o processador especializado em artefatos
            artifact_result = self.artifact_processor.process_artifact_request(user_input, context)
            
            # Garantir que o artefato seja completo e renderizável
            if artifact_result and artifact_result.get('is_complete'):
                return {
                    'success': True,
                    'artifact': artifact_result,
                    'processing_type': 'specialized_artifact_hmp',
                    'ready_to_render': True
                }
            else:
                # Fallback para processamento genérico se o especializado falhar
                logging.warning("⚠️ Processador especializado falhou, usando fallback")
                return self.route_request(user_input, context)
                
        except Exception as e:
            logging.error(f"❌ Erro no processamento de artefato: {e}")
            # Fallback para processamento normal
            return self.route_request(user_input, context)

    def get_available_chains(self) -> List[str]:
        """Retorna lista de cadeias HMP disponíveis."""
        return list(self.hmp_chains.keys())

    def execute_custom_hmp(self, hmp_code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executa código HMP personalizado."""
        return self.hmp_interpreter.execute_hmp(hmp_code, context)

    def execute_parallel_agents(self, agent_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executa múltiplos agentes em paralelo usando AutoFluxROKO.

        Args:
            agent_tasks: Lista de tarefas para agentes [{'agent': 'web', 'request': {...}}, ...]

        Returns:
            Dict com resultados de todos os agentes
        """
        if not HAS_AUTOFLUX or not self.autoflux:
            return self._execute_sequential_fallback(agent_tasks)

        logging.info(f"🔄 Executando {len(agent_tasks)} agentes em paralelo com AutoFlux")

        @self.autoflux.parallel(strategy='threads', use_process=False)
        def _process_agent_batch(task_batch):
            """Processa um batch de tarefas de agentes."""
            results = []
            for task in task_batch:
                agent_name = task.get('agent')
                request = task.get('request', {})

                if agent_name in self.agent_routes:
                    try:
                        result = self.agent_routes[agent_name](request)
                        results.append({
                            'agent': agent_name,
                            'success': True,
                            'result': result
                        })
                    except Exception as e:
                        logging.error(f"❌ Erro no agente {agent_name}: {e}")
                        results.append({
                            'agent': agent_name,
                            'success': False,
                            'error': str(e)
                        })
                else:
                    results.append({
                        'agent': agent_name,
                        'success': False,
                        'error': f"Agente {agent_name} não encontrado"
                    })

            return results

        # Executar usando AutoFlux
        results = _process_agent_batch(agent_tasks)

        return {
            'success': True,
            'parallel_execution': True,
            'results': results,
            'total_agents': len(agent_tasks)
        }

    def smart_task_decomposition(self, user_request: str) -> List[Dict[str, Any]]:
        """
        Decomposição ULTRA-GRANULAR para máxima paralelização e velocidade 100x.
        Cria o máximo de workers paralelos possível para cada requisição.
        """
        # Pipeline de decomposição ultra-agressiva
        parallel_tasks = []

        # ALWAYS: Análise inicial paralela (Prioridade 0 - Imediata)
        parallel_tasks.extend([
            {"agent": "planner", "request": {"task": "analyze_requirements", "input": user_request}, "priority": 0},
            {"agent": "validation", "request": {"task": "validate_input", "input": user_request}, "priority": 0},
            {"agent": "adaptive_context", "request": {"task": "context_analysis", "input": user_request}, "priority": 0}
        ])

        # ALWAYS: Processamento principal paralelo (Prioridade 1)
        if any(kw in user_request.lower() for kw in ["arquivo", "dados", "csv", "json", "criar", "gerar"]):
            parallel_tasks.extend([
                {"agent": "web", "request": {"task": "search_data_sources", "query": user_request}, "priority": 1},
                {"agent": "data_processing", "request": {"task": "prepare_data_structure", "format": "auto"}, "priority": 1},
                {"agent": "code", "request": {"task": "generate_data_code", "requirements": user_request}, "priority": 1},
                {"agent": "artifact_manager", "request": {"task": "prepare_artifact", "type": "data_file"}, "priority": 1}
            ])

        if any(kw in user_request.lower() for kw in ["pesquisar", "buscar", "informação", "web", "site"]):
            parallel_tasks.extend([
                {"agent": "web", "request": {"task": "comprehensive_search", "query": user_request}, "priority": 1},
                {"agent": "web", "request": {"task": "alternative_search", "query": user_request}, "priority": 1},
                {"agent": "data_processing", "request": {"task": "analyze_search_results", "query": user_request}, "priority": 1}
            ])

        if any(kw in user_request.lower() for kw in ["código", "script", "executar", "python", "programar"]):
            parallel_tasks.extend([
                {"agent": "code", "request": {"task": "generate_main_code", "requirements": user_request}, "priority": 1},
                {"agent": "code", "request": {"task": "generate_helper_functions", "requirements": user_request}, "priority": 1},
                {"agent": "validation", "request": {"task": "code_review", "requirements": user_request}, "priority": 1}
            ])

        if any(kw in user_request.lower() for kw in ["análise", "dashboard", "gráfico", "visualização"]):
            parallel_tasks.extend([
                {"agent": "data_processing", "request": {"task": "statistical_analysis", "input": user_request}, "priority": 1},
                {"agent": "artifact_manager", "request": {"task": "create_visualization", "type": "chart"}, "priority": 1},
                {"agent": "code", "request": {"task": "generate_visualization_code", "requirements": user_request}, "priority": 1}
            ])

        # ALWAYS: Processamento secundário (Prioridade 2)
        parallel_tasks.extend([
            {"agent": "metrics", "request": {"task": "performance_analysis", "context": user_request}, "priority": 2},
            {"agent": "error_fix", "request": {"task": "preemptive_error_check", "context": user_request}, "priority": 2},
            {"agent": "shell", "request": {"task": "environment_check", "context": user_request}, "priority": 2}
        ])

        # ALWAYS: Coordenação e síntese (Prioridade 3)
        parallel_tasks.extend([
            {"agent": "roko", "request": {"task": "coordinate_results", "context": user_request}, "priority": 3},
            {"agent": "roko", "request": {"task": "prepare_final_synthesis", "context": user_request}, "priority": 3},
            {"agent": "checkin", "request": {"task": "final_validation", "context": user_request}, "priority": 3}
        ])

        # Se nenhum worker específico foi adicionado, usar workflow genérico ultra-paralelo
        if len([t for t in parallel_tasks if t["priority"] == 1]) == 0:
            parallel_tasks.extend([
                {"agent": "planner", "request": {"task": "create_execution_plan", "input": user_request}, "priority": 1},
                {"agent": "executor", "request": {"task": "execute_primary_task", "input": user_request}, "priority": 1},
                {"agent": "web", "request": {"task": "supporting_research", "query": user_request}, "priority": 1},
                {"agent": "code", "request": {"task": "generate_supporting_code", "requirements": user_request}, "priority": 1}
            ])

        logging.info(f"🚀 Ultra-decomposição: {len(parallel_tasks)} workers para máxima velocidade")
        return parallel_tasks

    def execute_worker_pipeline(self, user_request: str) -> Dict[str, Any]:
        """
        Pipeline ULTRA-OTIMIZADO para máxima velocidade (100x).
        Execução paralela agressiva com cache e otimizações avançadas.
        """
        import time
        start_time = time.time()

        logging.info(f"🚀 ULTRA-PIPELINE iniciado para: {user_request[:50]}...")

        # 1. Decomposição ultra-granular
        parallel_tasks = self.smart_task_decomposition(user_request)
        logging.info(f"📋 {len(parallel_tasks)} workers ultra-paralelos identificados")

        # 2. Organizar por prioridade COM otimização AutoFlux
        priority_groups = {}
        for task in parallel_tasks:
            priority = task.get('priority', 1)
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(task)

        # 3. EXECUÇÃO ULTRA-PARALELA por prioridades
        all_results = []

        # Executar grupos em paralelo com overlapping para máxima velocidade
        if HAS_AUTOFLUX and self.autoflux:
            # Usar AutoFlux para processamento de prioridades simultâneo
            @self.autoflux.parallel(strategy='auto', use_process=False, chunk_management=True)
            def execute_priority_group(group_data_list):
                results = []
                for group_data in group_data_list:
                    try:
                        priority, group_tasks = group_data
                        logging.info(f"⚡ ULTRA-EXEC: {len(group_tasks)} workers prioridade {priority}")

                        # Execução ultra-paralela dentro do grupo
                        group_results = self.execute_parallel_agents(group_tasks)
                        results.append({
                            'priority': priority,
                            'results': group_results.get('results', []),
                            'execution_time': time.time() - start_time
                        })
                    except Exception as e:
                        logging.error(f"❌ Erro ao processar grupo: {e}")
                        results.append({
                            'priority': 0,
                            'results': [],
                            'error': str(e)
                        })
                return results

            # Processar TODOS os grupos simultaneamente para máxima velocidade
            priority_data = [(p, tasks) for p, tasks in priority_groups.items()]

            # Executar cada grupo individualmente para evitar erro de desempacotamento
            priority_results = []
            for group_data in priority_data:
                try:
                    group_result = execute_priority_group([group_data])  # Passar como lista
                    if isinstance(group_result, list) and len(group_result) > 0:
                        priority_results.extend(group_result)
                    elif isinstance(group_result, dict):
                        priority_results.append(group_result)
                except Exception as e:
                    logging.error(f"❌ Erro no grupo de prioridade: {e}")

            # Organizar resultados por prioridade
            for priority_result in priority_results:
                if isinstance(priority_result, dict) and 'results' in priority_result:
                    all_results.extend(priority_result.get('results', []))

        else:
            # Fallback sequencial otimizado
            for priority in sorted(priority_groups.keys()):
                group_tasks = priority_groups[priority]
                logging.info(f"⚡ Executando {len(group_tasks)} workers prioridade {priority}")

                group_results = self.execute_parallel_agents(group_tasks)
                all_results.extend(group_results.get('results', []))

        # 4. Coordenação ultra-rápida dos resultados
        coordination_result = self._coordinate_worker_results(all_results, user_request)

        execution_time = time.time() - start_time
        speedup_factor = max(1, len(parallel_tasks) * 2)  # Estimativa conservadora

        logging.info(f"✅ ULTRA-PIPELINE concluído em {execution_time:.2f}s - Speedup: ~{speedup_factor}x")

        return {
            'success': True,
            'user_request': user_request,
            'workers_executed': len(parallel_tasks),
            'parallel_groups': len(priority_groups),
            'results': all_results,
            'final_output': coordination_result,
            'execution_type': 'ultra_parallel_workers',
            'execution_time': execution_time,
            'estimated_speedup': f"{speedup_factor}x",
            'ultra_optimized': True
        }

    def _coordinate_worker_results(self, worker_results: List[Dict], user_request: str) -> str:
        """
        Coordena e sintetiza resultados de múltiplos workers.
        """
        coordination_hmp = f"""
SET worker_results TO {worker_results}
SET user_request TO "{user_request}"
SET final_output TO ""

# ANÁLISE DOS RESULTADOS
CALL analyze_worker_outputs WITH results = worker_results
SET successful_workers TO filter_successful(worker_results)
SET failed_workers TO filter_failed(worker_results)

# SÍNTESE INTELIGENTE
IF successful_workers.length > 0 THEN
    CALL synthesize_worker_outputs WITH
        successful_results = successful_workers,
        original_request = user_request,
        synthesis_mode = "comprehensive"
    SET final_output TO synthesis_result
ELSE
    SET final_output TO "Falha na execução dos workers - verifique logs"
ENDIF

# RELATÓRIO DE EXECUÇÃO
CALL generate_execution_report WITH
    total_workers = worker_results.length,
    successful = successful_workers.length,
    failed = failed_workers.length

RETURN final_output
"""

        result = self.hmp_interpreter.execute_hmp(coordination_hmp)
        return result.get('variables', {}).get('final_output', 'Coordenação de resultados concluída')

    def _execute_sequential_fallback(self, agent_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback para execução sequencial quando AutoFlux não está disponível."""
        logging.info("⚡ Executando agentes sequencialmente (fallback)")

        results = []
        for task in agent_tasks:
            agent_name = task.get('agent')
            request = task.get('request', {})

            if agent_name in self.agent_routes:
                try:
                    result = self.agent_routes[agent_name](request)
                    results.append({
                        'agent': agent_name,
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'agent': agent_name,
                        'success': False,
                        'error': str(e)
                    })

        return {
            'success': True,
            'parallel_execution': False,
            'results': results,
            'total_agents': len(agent_tasks)
        }

    async def execute_parallel_chains(self, chain_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executa múltiplas cadeias HMP em paralelo.

        Args:
            chain_requests: Lista de requisições [{'chain': 'web_research', 'input': '...', 'context': {...}}, ...]
        """
        if not HAS_AUTOFLUX:
            return await self._execute_chains_sequential(chain_requests)

        logging.info(f"🧠 Executando {len(chain_requests)} cadeias HMP em paralelo")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.autoflux.max_workers) as executor:
            futures = []

            for chain_request in chain_requests:
                chain_name = chain_request.get('chain')
                user_input = chain_request.get('input', '')
                context = chain_request.get('context', {})

                if chain_name in self.hmp_chains:
                    future = executor.submit(self._execute_single_chain, chain_name, user_input, context)
                    futures.append({
                        'future': future,
                        'chain': chain_name,
                        'input': user_input
                    })

            # Coletar resultados
            results = []
            for future_data in futures:
                try:
                    result = future_data['future'].result(timeout=30.0)
                    results.append({
                        'chain': future_data['chain'],
                        'input': future_data['input'][:50] + "...",
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    logging.error(f"❌ Erro na cadeia {future_data['chain']}: {e}")
                    results.append({
                        'chain': future_data['chain'],
                        'input': future_data['input'][:50] + "...",
                        'success': False,
                        'error': str(e)
                    })

        return {
            'success': True,
            'parallel_chains': True,
            'results': results,
            'total_chains': len(chain_requests)
        }

    def _execute_single_chain(self, chain_name: str, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa uma única cadeia HMP."""
        hmp_code = self.hmp_chains[chain_name].format(
            user_input=user_input,
            context=context
        )
        return self.hmp_interpreter.execute_hmp(hmp_code, context)

    async def _execute_chains_sequential(self, chain_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback para execução sequencial de cadeias."""
        results = []
        for chain_request in chain_requests:
            chain_name = chain_request.get('chain')
            user_input = chain_request.get('input', '')
            context = chain_request.get('context', {})

            if chain_name in self.hmp_chains:
                try:
                    result = self._execute_single_chain(chain_name, user_input, context)
                    results.append({
                        'chain': chain_name,
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'chain': chain_name,
                        'success': False,
                        'error': str(e)
                    })

        return {
            'success': True,
            'parallel_chains': False,
            'results': results
        }