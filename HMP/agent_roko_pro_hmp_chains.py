
"""
Cadeias HMP específicas para Agent ROKO PRO
Define cadeias reutilizáveis para diferentes cenários de uso
"""

from typing import Dict, Any
from .hmp_interpreter import HMPInterpreter

class AgentROKOProHMPChains:
    """
    Coleção de cadeias HMP pré-definidas para Agent ROKO PRO
    """
    
    @staticmethod
    def get_deployment_chain() -> str:
        """Cadeia HMP para deploy full-stack"""
        return """
SET projeto TO {user_input}
SET deploy_targets TO ["vercel", "netlify", "aws_s3"]
SET user TO {user_context}

# Verificar permissões
CALL agent_roko_pro.permissions_check WITH user = user, action = "deploy"
IF NOT permission_result THEN
    RETURN {status: "forbidden", reason: "insufficient_permissions"}
ENDIF

# Preparar ambiente
CALL agent_roko_pro.thinking WITH input = "Iniciando deploy de " + projeto
CALL agent_roko_pro.log_hgr WITH type = "deploy.start", payload = {projeto: projeto, targets: deploy_targets}

# Inventário e validação
CALL agent_roko_pro.inventory WITH hosts = []
CALL agent_roko_pro.tests_and_validation WITH project_dir = projeto

# Deploy para múltiplos targets
SET deploy_results TO []
FOR target IN deploy_targets:
    CALL agent_roko_pro.deploy_adapter WITH target = target, params = {bucket: projeto + "-static"}
    APPEND deploy_results WITH deployment_result
ENDFOR

# Análise e validação
CALL agent_roko_pro.analyze_results WITH results = deploy_results, objetivo = "deploy bem-sucedido"

RETURN {status: "completed", deployments: deploy_results, analysis: analysis_result}
"""

    @staticmethod
    def get_security_audit_chain() -> str:
        """Cadeia HMP para auditoria de segurança"""
        return """
SET target_system TO {user_input}
SET audit_scope TO ["dependencies", "permissions", "network", "secrets"]
SET user TO {user_context}

# Verificar permissões de auditoria
CALL agent_roko_pro.permissions_check WITH user = user, action = "audit"
IF NOT permission_result THEN
    RETURN {status: "forbidden", reason: "audit_not_authorized"}
ENDIF

# Iniciar auditoria
CALL agent_roko_pro.thinking WITH input = "Auditoria de segurança para " + target_system
CALL agent_roko_pro.log_hgr WITH type = "audit.start", payload = {target: target_system, scope: audit_scope}

# Coleta de informações de segurança
SET security_steps TO [
    {type: "shell", cmd: "npm audit --audit-level moderate", desc: "Audit NPM packages"},
    {type: "shell", cmd: "find . -name '*.py' -exec bandit {} \\;", desc: "Python security scan"},
    {type: "shell", cmd: "grep -r 'password\\|secret\\|key' . --exclude-dir=node_modules", desc: "Search for exposed secrets"}
]

CALL agent_roko_pro.execute_actions WITH steps = security_steps
CALL agent_roko_pro.auto_heal_and_retry WITH exec_results = execution_results, max_attempts = 2

# Análise de vulnerabilidades
CALL agent_roko_pro.analyze_results WITH results = healed_results, objetivo = "sistema seguro"

# Gerar relatório de segurança
SET security_report TO {
    target: target_system,
    vulnerabilities_found: vulnerabilities_count,
    recommendations: security_recommendations,
    compliance_score: analysis_result.score
}

CALL agent_roko_pro.log_hgr WITH type = "audit.complete", payload = security_report

RETURN {status: "completed", report: security_report}
"""

    @staticmethod
    def get_infrastructure_monitoring_chain() -> str:
        """Cadeia HMP para monitoramento de infraestrutura"""
        return """
SET infrastructure TO {user_input}
SET monitoring_interval TO {monitoring_config.interval} OR 300
SET alert_thresholds TO {monitoring_config.thresholds} OR {cpu: 80, memory: 85, disk: 90}

# Monitoramento contínuo
CALL agent_roko_pro.thinking WITH input = "Monitoramento de infraestrutura " + infrastructure

WHILE true:
    # Coleta de métricas
    SET monitoring_steps TO [
        {type: "shell", cmd: "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'", desc: "CPU usage"},
        {type: "shell", cmd: "free | grep Mem | awk '{printf \"%.2f\", $3/$2 * 100.0}'", desc: "Memory usage"},
        {type: "shell", cmd: "df -h | awk 'NR==2{printf \"%s\", $5}' | sed 's/%//'", desc: "Disk usage"}
    ]
    
    CALL agent_roko_pro.execute_actions WITH steps = monitoring_steps
    
    # Análise de alertas
    FOR result IN execution_results:
        IF result.step.desc == "CPU usage" AND FLOAT(result.out) > alert_thresholds.cpu THEN
            CALL agent_roko_pro.log_hgr WITH type = "alert.cpu", payload = {value: result.out, threshold: alert_thresholds.cpu}
        ENDIF
        IF result.step.desc == "Memory usage" AND FLOAT(result.out) > alert_thresholds.memory THEN
            CALL agent_roko_pro.log_hgr WITH type = "alert.memory", payload = {value: result.out, threshold: alert_thresholds.memory}
        ENDIF
        IF result.step.desc == "Disk usage" AND FLOAT(result.out) > alert_thresholds.disk THEN
            CALL agent_roko_pro.log_hgr WITH type = "alert.disk", payload = {value: result.out, threshold: alert_thresholds.disk}
        ENDIF
    ENDFOR
    
    # Aguardar próximo ciclo
    SLEEP monitoring_interval
ENDWHILE
"""

    @staticmethod
    def get_data_processing_chain() -> str:
        """Cadeia HMP para processamento de dados em lote"""
        return """
SET data_source TO {user_input}
SET processing_config TO {data_config}
SET batch_size TO processing_config.batch_size OR 1000

# Inicializar processamento
CALL agent_roko_pro.thinking WITH input = "Processamento de dados de " + data_source
CALL agent_roko_pro.log_hgr WITH type = "data.processing.start", payload = {source: data_source, config: processing_config}

# Preparação do ambiente
SET prep_steps TO [
    {type: "shell", cmd: "mkdir -p data/input data/output data/temp", desc: "Create directories"},
    {type: "shell", cmd: "python -c 'import pandas, numpy, sqlalchemy'", desc: "Check dependencies"}
]

CALL agent_roko_pro.execute_actions WITH steps = prep_steps

# Processamento em lotes
SET batch_number TO 1
SET total_processed TO 0

WHILE true:
    # Carregar próximo lote
    SET load_step TO {
        type: "shell",
        cmd: "python -c \"import pandas as pd; df = pd.read_csv('" + data_source + "', skiprows=" + STR((batch_number-1)*batch_size) + ", nrows=" + STR(batch_size) + "); print(len(df))\"",
        desc: "Load batch " + STR(batch_number)
    }
    
    CALL agent_roko_pro.execute_actions WITH steps = [load_step]
    
    SET batch_size_actual TO INT(execution_results[0].out)
    IF batch_size_actual == 0 THEN
        BREAK  # Fim dos dados
    ENDIF
    
    # Processar lote
    SET process_step TO {
        type: "shell",
        cmd: "python scripts/process_batch.py --batch=" + STR(batch_number) + " --source=" + data_source,
        desc: "Process batch " + STR(batch_number)
    }
    
    CALL agent_roko_pro.execute_actions WITH steps = [process_step]
    
    SET total_processed = total_processed + batch_size_actual
    SET batch_number = batch_number + 1
    
    # Log progresso
    CALL agent_roko_pro.log_hgr WITH type = "data.batch.complete", payload = {
        batch: batch_number - 1,
        records: batch_size_actual,
        total: total_processed
    }
ENDWHILE

# Consolidação final
SET consolidate_step TO {
    type: "shell",
    cmd: "python scripts/consolidate_results.py --output=data/output/final_result.csv",
    desc: "Consolidate results"
}

CALL agent_roko_pro.execute_actions WITH steps = [consolidate_step]

# Análise dos resultados
CALL agent_roko_pro.analyze_results WITH results = [final_consolidation], objetivo = "processamento completo de dados"

RETURN {
    status: "completed",
    total_records: total_processed,
    batches_processed: batch_number - 1,
    output_file: "data/output/final_result.csv"
}
"""

    @staticmethod
    def get_system_recovery_chain() -> str:
        """Cadeia HMP para recuperação de sistema"""
        return """
SET recovery_scenario TO {user_input}
SET recovery_config TO {recovery_config}
SET backup_location TO recovery_config.backup_location OR "backups/"

# Avaliação do cenário
CALL agent_roko_pro.thinking WITH input = "Recuperação de sistema: " + recovery_scenario
CALL agent_roko_pro.log_hgr WITH type = "recovery.start", payload = {scenario: recovery_scenario}

# Diagnóstico inicial
SET diagnostic_steps TO [
    {type: "shell", cmd: "systemctl status", desc: "Check system services"},
    {type: "shell", cmd: "df -h", desc: "Check disk space"},
    {type: "shell", cmd: "free -m", desc: "Check memory"},
    {type: "shell", cmd: "ps aux | head -20", desc: "Check running processes"}
]

CALL agent_roko_pro.execute_actions WITH steps = diagnostic_steps

# Análise do problema
CALL agent_roko_pro.analyze_results WITH results = diagnostic_results, objetivo = "sistema operacional"

IF analysis_result.score < 30 THEN
    # Sistema gravemente comprometido - recuperação completa
    SET recovery_steps TO [
        {type: "shell", cmd: "sudo systemctl stop all", desc: "Stop services", dangerous: true},
        {type: "shell", cmd: "cp -r " + backup_location + "config/* /etc/", desc: "Restore config"},
        {type: "shell", cmd: "cp -r " + backup_location + "data/* /var/lib/", desc: "Restore data"},
        {type: "shell", cmd: "sudo systemctl start all", desc: "Start services"}
    ]
ELSE IF analysis_result.score < 60 THEN
    # Problemas moderados - recuperação seletiva
    SET recovery_steps TO [
        {type: "shell", cmd: "sudo systemctl restart failed-service", desc: "Restart failed services"},
        {type: "shell", cmd: "sudo systemctl reload nginx", desc: "Reload web server"},
        {type: "shell", cmd: "sudo service database restart", desc: "Restart database"}
    ]
ELSE
    # Problemas menores - correções pontuais
    SET recovery_steps TO [
        {type: "shell", cmd: "sudo systemctl reload-daemon", desc: "Reload systemd"},
        {type: "shell", cmd: "sudo sysctl -p", desc: "Reload kernel parameters"}
    ]
ENDIF

# Executar recuperação
CALL agent_roko_pro.execute_actions WITH steps = recovery_steps
CALL agent_roko_pro.auto_heal_and_retry WITH exec_results = recovery_results, max_attempts = 3

# Verificação pós-recuperação
SET verification_steps TO [
    {type: "shell", cmd: "systemctl is-system-running", desc: "Check system state"},
    {type: "http", url: "http://localhost/health", method: "GET", desc: "Check web service"},
    {type: "shell", cmd: "netstat -tlnp", desc: "Check listening ports"}
]

CALL agent_roko_pro.execute_actions WITH steps = verification_steps

# Análise final
CALL agent_roko_pro.analyze_results WITH results = verification_results, objetivo = "sistema totalmente recuperado"

# Relatório de recuperação
SET recovery_report TO {
    scenario: recovery_scenario,
    initial_score: initial_analysis.score,
    final_score: final_analysis.score,
    actions_taken: LENGTH(recovery_steps),
    recovery_successful: final_analysis.score > 80
}

CALL agent_roko_pro.log_hgr WITH type = "recovery.complete", payload = recovery_report

RETURN {status: "completed", report: recovery_report}
"""

    @staticmethod
    def get_all_chains() -> Dict[str, str]:
        """Retorna todas as cadeias disponíveis"""
        return {
            'agent_roko_pro_deployment': AgentROKOProHMPChains.get_deployment_chain(),
            'agent_roko_pro_security_audit': AgentROKOProHMPChains.get_security_audit_chain(),
            'agent_roko_pro_infrastructure_monitoring': AgentROKOProHMPChains.get_infrastructure_monitoring_chain(),
            'agent_roko_pro_data_processing': AgentROKOProHMPChains.get_data_processing_chain(),
            'agent_roko_pro_system_recovery': AgentROKOProHMPChains.get_system_recovery_chain()
        }
