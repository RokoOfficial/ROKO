
"""
Agent ROKO PRO - Cadeia HMP reutilizável completa
Implementação full-stack, auditável e segura para o sistema ROKO
"""

import os
import json
import sqlite3
import logging
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from .hmp_interpreter import HMPInterpreter

class AgentROKOProChain:
    """
    Implementação da cadeia Agent ROKO PRO com todas as funcionalidades:
    - Acesso SSH/shell controlado
    - Deploy multi-cloud
    - Auditoria completa em SQLite HGR
    - Auto-correção e retry
    - Sistema de permissões RBAC
    - Observabilidade e métricas
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.setup_defaults()
        self.setup_database()
        self.setup_logging()
        
    def setup_defaults(self):
        """Configuração padrão dos parâmetros"""
        self.project_name = self.config.get('project_name', 'rokopro-agent')
        self.host_list = self.config.get('hosts', [])
        self.max_parallel = self.config.get('max_parallel', 6)
        self.sqlite_path = self.config.get('sqlite_path', f'ROKO/{self.project_name}_hgr.db')
        self.fail_safe = self.config.get('fail_safe', True)
        self.required_alignment = self.config.get('required_alignment', 80)
        self.attempt_limit = self.config.get('attempt_limit', 4)
        self.auth_backends = self.config.get('auth_backends', ['replit', 'vault', 'aws-secrets'])
        self.deploy_targets = self.config.get('deploy_targets', ['vercel', 'netlify', 'aws_s3'])
        self.rbac_roles = self.config.get('rbac_roles', {
            'admin': ['*'],
            'deployer': ['deploy', 'read'],
            'auditor': ['read']
        })
        self.debug = self.config.get('debug', False)
        
    def setup_database(self):
        """Inicializa SQLite HGR com migrations"""
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        self.db = sqlite3.connect(self.sqlite_path)
        self.db.execute("PRAGMA journal_mode=WAL;")
        
        # Criar tabelas se não existirem
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS chains (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT,
                status TEXT,
                metadata TEXT
            );
            
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                chain_id TEXT,
                step_index INTEGER,
                type TEXT,
                status TEXT,
                output TEXT
            );
            
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                chain_id TEXT,
                name TEXT,
                path TEXT,
                meta TEXT
            );
            
            CREATE TABLE IF NOT EXISTS hgr_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event TEXT,
                payload TEXT
            );
            
            CREATE TABLE IF NOT EXISTS migrations (
                id TEXT PRIMARY KEY,
                applied_at TEXT
            );
        """)
        
        # Migration v1
        cursor = self.db.execute("SELECT id FROM migrations WHERE id='v1_init'")
        if not cursor.fetchone():
            self.db.execute("INSERT INTO migrations (id, applied_at) VALUES ('v1_init', ?)", 
                          [datetime.now().isoformat()])
        
        self.db.commit()
        
    def setup_logging(self):
        """Configurar logging auditável"""
        self.logger = logging.getLogger('ROKO.AgentPro')
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
    def log_hgr(self, event_type: str, payload: Dict[str, Any]):
        """Log para auditoria HGR"""
        try:
            self.db.execute(
                "INSERT INTO hgr_audit (timestamp, event, payload) VALUES (?, ?, ?)",
                [datetime.now().isoformat(), event_type, json.dumps(payload)]
            )
            self.db.commit()
            self.logger.info(f"HGR: {event_type} - {payload}")
        except Exception as e:
            self.logger.error(f"Erro no log HGR: {e}")
            
    def generate_uuid(self) -> str:
        """Gerar UUID único"""
        return f"rokopro-{uuid.uuid4().hex[:8]}-{int(time.time())}"
        
    def auth_manager(self, backend: str, key: str) -> Optional[str]:
        """Gerenciador de autenticação multi-backend"""
        try:
            if backend == 'replit':
                return os.environ.get(key)
            elif backend == 'vault':
                # Implementação Vault (mock para demo)
                vault_addr = os.environ.get('VAULT_ADDR')
                vault_token = os.environ.get('VAULT_TOKEN')
                if vault_addr and vault_token:
                    # Aqui faria request real para Vault
                    return os.environ.get(f'VAULT_{key}')
            elif backend == 'aws-secrets':
                # Implementação AWS Secrets (mock para demo)
                return os.environ.get(f'AWS_SECRET_{key}')
        except Exception as e:
            self.logger.error(f"Erro auth {backend}: {e}")
        return None
        
    def thinking(self, input_data: str, level: str = 'info') -> str:
        """Registra pensamento e autodescrição"""
        tid = self.generate_uuid()
        note = {
            'id': tid,
            'input': input_data,
            'level': level,
            'started_at': datetime.now().isoformat()
        }
        self.log_hgr('thinking.start', note)
        return tid
        
    def plan_generator(self, objetivo: str) -> List[Dict[str, Any]]:
        """Gerador de plano avançado"""
        tid = self.thinking(objetivo)
        self.logger.info(f'Gerando plano avançado para: {objetivo}')
        
        base_tasks = [
            {'id': 'inventory', 'type': 'inventory', 'desc': 'coletar inventario local+remoto'},
            {'id': 'probe', 'type': 'probe', 'desc': 'testar endpoints via curl/http'},
            {'id': 'gather', 'type': 'gather_logs', 'desc': 'coletar logs relevantes'},
            {'id': 'analyze', 'type': 'analyze', 'desc': 'analisar e calcular alinhamento'},
            {'id': 'act', 'type': 'act', 'desc': 'executar ações priorizadas'},
            {'id': 'validate', 'type': 'validate', 'desc': 'testes e validação'}
        ]
        
        # IA auxiliar pode reordenar/priorizar
        tasks = self.ia_assistant('Priorizacao das tarefas para: ' + objetivo, base_tasks) or base_tasks
        
        self.log_hgr('plan.generated', {'id': tid, 'tasks': tasks})
        return tasks
        
    def inventory(self, hosts: List[str]) -> List[Dict[str, Any]]:
        """Coleta inventário local e remoto"""
        out = []
        
        # Inventário local
        try:
            import subprocess
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=10)
            out.append({'target': 'local', 'method': 'shell', 'out': result.stdout})
        except Exception as e:
            out.append({'target': 'local', 'method': 'shell', 'error': str(e)})
            
        # Inventário remoto (SSH probe seguro)
        for host in hosts:
            cred_key = f'host_{host}_creds'
            creds_raw = None
            
            for backend in self.auth_backends:
                creds_raw = self.auth_manager(backend, cred_key)
                if creds_raw:
                    break
                    
            if not creds_raw:
                out.append({'target': host, 'status': 'no_creds'})
                continue
                
            try:
                # SSH probe seguro
                ssh_cmd = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=6', 
                          f'{creds_raw}@{host}', 'echo __rokoshok__']
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
                out.append({'target': host, 'method': 'ssh_probe', 'out': result.stdout})
            except Exception as e:
                out.append({'target': host, 'method': 'ssh_probe', 'error': str(e)})
                
        self.log_hgr('inventory.result', out)
        return out
        
    def probe_hosts(self, hosts: List[str]) -> List[Dict[str, Any]]:
        """Probe hosts com curl + requests"""
        results = []
        
        for host in hosts:
            health_url = f'http://{host}/health'
            host_result = {'host': host}
            
            # Curl probe
            try:
                import subprocess
                curl_result = subprocess.run(
                    ['curl', '-s', '--max-time', '5', health_url],
                    capture_output=True, text=True, timeout=10
                )
                host_result['curl'] = curl_result.stdout
            except Exception as e:
                host_result['curl_error'] = str(e)
                
            # HTTP library probe
            try:
                import requests
                response = requests.get(health_url, timeout=7)
                host_result['http'] = {
                    'status_code': response.status_code,
                    'content': response.text[:500]
                }
            except Exception as e:
                host_result['http_error'] = str(e)
                
            results.append(host_result)
            
        self.log_hgr('probe.result', results)
        return results
        
    def execute_actions(self, steps: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execução controlada e auditada"""
        exec_out = []
        
        for step in steps:
            if step.get('type') == 'shell':
                if self.fail_safe and step.get('dangerous'):
                    exec_out.append({'step': step, 'status': 'blocked_fail_safe'})
                    self.log_hgr('exec.blocked', step)
                    continue
                    
                self.log_hgr('exec.start.shell', step)
                try:
                    import subprocess
                    result = subprocess.run(
                        step['cmd'], shell=True, capture_output=True, 
                        text=True, timeout=30
                    )
                    exec_out.append({
                        'step': step, 
                        'status': 'ok', 
                        'out': result.stdout,
                        'stderr': result.stderr
                    })
                    self.log_hgr('exec.shell', {'step': step, 'out': result.stdout})
                except Exception as e:
                    exec_out.append({'step': step, 'status': 'error', 'error': str(e)})
                    
            elif step.get('type') == 'ssh':
                creds_key = f"host_{step['target']}_creds"
                creds = None
                
                for backend in self.auth_backends:
                    creds = self.auth_manager(backend, creds_key)
                    if creds:
                        break
                        
                if not creds:
                    exec_out.append({'step': step, 'status': 'no_creds'})
                    self.log_hgr('exec.ssh.nocreds', {'step': step})
                    continue
                    
                try:
                    import subprocess
                    ssh_cmd = ['ssh', f"{creds}@{step['target']}", step['cmd']]
                    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
                    exec_out.append({'step': step, 'status': 'ok', 'out': result.stdout})
                    self.log_hgr('exec.ssh', {
                        'target': step['target'], 
                        'cmd': step['cmd'], 
                        'out': result.stdout
                    })
                except Exception as e:
                    exec_out.append({'step': step, 'status': 'error', 'error': str(e)})
                    
            elif step.get('type') == 'http':
                try:
                    import requests
                    response = requests.request(
                        method=step.get('method', 'POST'),
                        url=step['url'],
                        json=step.get('body', {}),
                        headers=step.get('headers', {}),
                        timeout=15
                    )
                    exec_out.append({
                        'step': step, 
                        'status': 'ok', 
                        'out': {
                            'status_code': response.status_code,
                            'content': response.text[:1000]
                        }
                    })
                    self.log_hgr('exec.http', {'step': step, 'status': response.status_code})
                except Exception as e:
                    exec_out.append({'step': step, 'status': 'error', 'error': str(e)})
                    
            elif step.get('type') == 'deploy':
                self.log_hgr('exec.deploy.start', step)
                deploy_res = self.deploy_adapter(step['target'], step.get('params', {}))
                exec_out.append({'step': step, 'status': 'ok', 'out': deploy_res})
                self.log_hgr('exec.deploy', {'step': step, 'out': deploy_res})
                
        return exec_out
        
    def deploy_adapter(self, target: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adapter para múltiplos providers de deploy"""
        try:
            import subprocess
            
            if target == 'vercel':
                result = subprocess.run(['npx', 'vercel', '--prod', '--confirm'], 
                                      capture_output=True, text=True, timeout=300)
                return {'stdout': result.stdout, 'stderr': result.stderr}
                
            elif target == 'netlify':
                cmd = ['npx', 'netlify', 'deploy', '--prod', '--dir=dist', 
                       '--message=deploy from ROKO']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                return {'stdout': result.stdout, 'stderr': result.stderr}
                
            elif target == 'github_pages':
                commands = [
                    'git add .',
                    'git commit -m "gh-pages deploy" || true',
                    'git push origin HEAD:gh-pages --force'
                ]
                results = []
                for cmd in commands:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    results.append({'cmd': cmd, 'out': result.stdout})
                return {'commands': results}
                
            elif target == 'aws_s3':
                bucket = params.get('bucket', f"{self.project_name}-static")
                sync_cmd = ['aws', 's3', 'sync', 'dist', f's3://{bucket}']
                result = subprocess.run(sync_cmd, capture_output=True, text=True, timeout=300)
                
                output = {'sync': {'stdout': result.stdout, 'stderr': result.stderr}}
                
                if params.get('invalidation'):
                    inv_cmd = ['aws', 'cloudfront', 'create-invalidation', 
                              '--distribution-id', params['invalidation'], '--paths', '/*']
                    inv_result = subprocess.run(inv_cmd, capture_output=True, text=True)
                    output['invalidation'] = {'stdout': inv_result.stdout, 'stderr': inv_result.stderr}
                    
                return output
                
        except Exception as e:
            return {'error': str(e)}
            
        return {'error': 'target_not_supported'}
        
    def analyze_results(self, results: List[Dict[str, Any]], objetivo: str) -> Dict[str, Any]:
        """Análise de similaridade e alinhamento"""
        texts = []
        for r in results:
            text = r.get('out') or r.get('output') or str(r)
            if isinstance(text, dict):
                text = json.dumps(text)
            texts.append(str(text))
            
        scored = []
        for text in texts:
            # Análise simples de similaridade baseada em palavras-chave
            score = self.calculate_similarity(objetivo, text)
            scored.append({'text': text[:200], 'score': score})
            
        avg_score = (sum(s['score'] for s in scored) / max(len(scored), 1)) * 100
        top = sorted(scored, key=lambda x: x['score'], reverse=True)[:5]
        
        self.log_hgr('analysis', {'avg': avg_score, 'top': top})
        
        if avg_score >= self.required_alignment:
            return {'aligned': True, 'score': avg_score, 'top': top}
        else:
            nearest = [m for m in top if m['score'] >= 0.5]
            if nearest:
                suggestion = f"Ajustar execuções para focar nos targets: {', '.join([n['text'][:50] for n in nearest[:3]])}. Proponho re-probing e coleta adicional de logs."
            else:
                suggestion = "Nenhum dado suficientemente próximo — recomendo aumentar a amplitude dos probes e aumentar timeouts."
                
            return {
                'aligned': False, 
                'score': avg_score, 
                'suggestion': suggestion, 
                'top': top
            }
            
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Cálculo simples de similaridade"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / max(len(union), 1)
        
    def auto_heal_and_retry(self, exec_results: List[Dict[str, Any]], max_attempts: int) -> List[Dict[str, Any]]:
        """Sistema de auto-correção e retry"""
        attempt = 1
        aggregated = exec_results[:]
        
        while attempt <= max_attempts:
            needs_retry = [r for r in aggregated if r.get('status') in ['no_creds', 'timeout', 'error', 'blocked_fail_safe']]
            
            if not needs_retry:
                break
                
            for nr in needs_retry:
                if nr['status'] == 'no_creds':
                    self.logger.info(f"Tentando recuperar credenciais alternativas para {nr.get('step', {}).get('target', '')}")
                    alt_creds = self.auth_manager('replit', f"alt_{nr.get('step', {}).get('target', '')}_creds")
                    if alt_creds:
                        self.log_hgr('heal.creds_restore', {'target': nr.get('step', {}).get('target')})
                        retry_out = self.execute_actions([nr['step']])
                        aggregated.extend(retry_out)
                        
                elif nr['status'] == 'timeout':
                    # Aumentar timeout e tentar novamente
                    step = nr['step'].copy()
                    step['timeout'] = step.get('timeout', 5) * 2
                    retry_out = self.execute_actions([step])
                    aggregated.extend(retry_out)
                    
                elif nr['status'] == 'blocked_fail_safe':
                    self.log_hgr('heal.blocked', {'step': nr['step']})
                    
            attempt += 1
            
        return aggregated
        
    def tests_and_validation(self, project_dir: str) -> Dict[str, Any]:
        """Executa testes e validação"""
        try:
            import subprocess
            
            results = {}
            
            # Install dependencies
            try:
                result = subprocess.run(['npm', 'ci'], cwd=project_dir, capture_output=True, text=True, timeout=300)
                results['install'] = {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}
            except Exception as e:
                results['install'] = {'error': str(e)}
                
            # Lint
            try:
                result = subprocess.run(['npm', 'run', 'lint'], cwd=project_dir, capture_output=True, text=True, timeout=120)
                results['lint'] = {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}
            except Exception as e:
                results['lint'] = {'error': str(e)}
                
            # Test
            try:
                result = subprocess.run(['npm', 'run', 'test'], cwd=project_dir, capture_output=True, text=True, timeout=300)
                results['test'] = {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}
            except Exception as e:
                results['test'] = {'error': str(e)}
                
            # Build
            try:
                result = subprocess.run(['npm', 'run', 'build'], cwd=project_dir, capture_output=True, text=True, timeout=300)
                results['build'] = {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}
            except Exception as e:
                results['build'] = {'error': str(e)}
                
            self.log_hgr('tests.report', results)
            return results
            
        except Exception as e:
            return {'error': str(e)}
            
    def permissions_check(self, user: Dict[str, Any], action: str) -> bool:
        """Verificação de permissões RBAC"""
        roles = user.get('roles', [])
        for role in roles:
            allowed = self.rbac_roles.get(role, [])
            if '*' in allowed or action in allowed:
                return True
        return False
        
    def ia_assistant(self, prompt: str, context: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Mini agente para sugestões"""
        if 'Priorizacao' in prompt:
            # Reordena por criticidade detectada
            ordered = sorted(context, key=lambda x: 0 if x.get('id') == 'probe' else 1)
            return ordered
        return None
        
    def execute_agent_roko_pro(self, objetivo: str, user: Dict[str, Any]) -> Dict[str, Any]:
        """Cadeia principal Agent ROKO PRO"""
        # Verificação de permissões
        if not self.permissions_check(user, 'execute'):
            self.log_hgr('agent.auth.fail', {'user': user})
            return {'status': 'forbidden', 'reason': 'user_not_authorized'}
            
        # Iniciar thinking
        t_id = self.thinking(objetivo)
        self.log_hgr('agent.start', {'id': t_id, 'objetivo': objetivo, 'user': user})
        
        try:
            # Planejar
            plan = self.plan_generator(objetivo)
            self.log_hgr('agent.plan', plan)
            
            # Inventário e probes
            inv = self.inventory(self.host_list)
            probes = self.probe_hosts(self.host_list)
            
            # Construir passos de execução
            steps = []
            for p in plan:
                if p['type'] == 'inventory':
                    steps.append({'type': 'shell', 'cmd': 'echo "inventory step"'})
                elif p['type'] == 'probe':
                    if self.host_list:
                        steps.append({
                            'type': 'http', 
                            'url': f'http://{self.host_list[0]}/api/check', 
                            'method': 'GET'
                        })
                elif p['type'] == 'act':
                    # Deploy para targets configurados
                    for target in self.deploy_targets:
                        steps.append({
                            'type': 'deploy', 
                            'target': target, 
                            'params': {'bucket': f'{self.project_name}-static'}
                        })
                        
            # Executar ações
            exec_res = self.execute_actions(steps)
            self.log_hgr('agent.exec', exec_res)
            
            # Auto-correção
            healed = self.auto_heal_and_retry(exec_res, self.attempt_limit)
            self.log_hgr('agent.heal', healed)
            
            # Testes
            tests = self.tests_and_validation(self.project_name)
            
            # Análise de alinhamento
            analysis = self.analyze_results(healed, objetivo)
            self.log_hgr('agent.analysis', analysis)
            
            # Decisão final
            if analysis['aligned']:
                self.log_hgr('agent.complete', {'id': t_id, 'score': analysis['score']})
                return {
                    'status': 'ok',
                    'id': t_id,
                    'score': analysis['score'],
                    'results': healed,
                    'tests': tests,
                    'inventory': inv,
                    'probes': probes
                }
            else:
                self.log_hgr('agent.partial', {
                    'id': t_id, 
                    'score': analysis['score'], 
                    'suggestion': analysis['suggestion']
                })
                return {
                    'status': 'partial',
                    'id': t_id,
                    'score': analysis['score'],
                    'suggestion': analysis['suggestion'],
                    'top': analysis['top']
                }
                
        except Exception as e:
            self.log_hgr('agent.error', {'id': t_id, 'error': str(e)})
            return {'status': 'error', 'id': t_id, 'error': str(e)}
            
    def close(self):
        """Fecha conexões"""
        if hasattr(self, 'db'):
            self.db.close()
