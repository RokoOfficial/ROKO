"""
Agente para execução de comandos de terminal com fallbacks inteligentes.
"""

import subprocess
import logging
import shutil
import os
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

class ShellAgent(BaseAgent):
    """Agente para execução de comandos de terminal com fallbacks inteligentes."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.command_alternatives = {
            'ping': ['nix-shell -p inetutils --run "ping', 'curl -s -o /dev/null -w "%{http_code}" http://google.com', 'python3 -c "import urllib.request; print(urllib.request.urlopen(\'http://google.com\').getcode())"'],
            'wget': ['curl -L -O', 'python3 -c "import urllib.request; urllib.request.urlretrieve'],
            'git': ['nix-shell -p git --run "git'],
            'docker': ['nix-shell -p docker --run "docker']
        }
        self.workspace_path: Optional[str] = os.getcwd()

    def _get_command_alternatives(self, command: str) -> List[str]:
        """Retorna alternativas para um comando que pode não estar disponível."""
        base_command = command.split()[0]
        return self.command_alternatives.get(base_command, [])

    def _check_command_availability(self, command: str) -> bool:
        """Verifica se um comando está disponível no sistema."""
        base_command = command.split()[0]
        return shutil.which(base_command) is not None

    def _generate_safe_alternative(self, original_command: str) -> str:
        """Gera uma alternativa segura usando o modelo de IA."""
        system_prompt = """
        Você é um especialista em sistemas Linux/Nix. Dado um comando que falhou,
        gere uma alternativa que funcione no ambiente Nix/Replit.

        Prioridades:
        1. Use 'nix-shell -p [pacote] --run "[comando]"' para comandos não disponíveis
        2. Use alternativas Python quando possível
        3. Use curl ao invés de wget
        4. Evite comandos que requerem privilégios de administrador

        Responda APENAS com o comando alternativo.
        """

        user_content = f"Comando original que falhou: {original_command}"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3
            )

            return response.choices[0].message.content.strip()
        except:
            return f"echo 'Comando {original_command} não disponível no ambiente'"

    def execute(self, command: str) -> Dict[str, Any]:
        logging.info(f"ShellAgent executando: '{command}'")

        # Lista de comandos para tentar (original + alternativas)
        commands_to_try = [command]

        # Adicionar alternativas conhecidas
        alternatives = self._get_command_alternatives(command)
        for alt in alternatives:
            if alt.endswith('"'):
                commands_to_try.append(f'{alt} {" ".join(command.split()[1:])}"')
            else:
                commands_to_try.append(f'{alt} {" ".join(command.split()[1:])}')

        # Se comando base não está disponível, gerar alternativa com IA
        base_command = command.split()[0]
        if not self._check_command_availability(base_command):
            ai_alternative = self._generate_safe_alternative(command)
            commands_to_try.append(ai_alternative)

        last_error = None

        for i, cmd in enumerate(commands_to_try):
            try:
                logging.info(f"Tentativa {i+1}/{len(commands_to_try)}: {cmd}")

                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.workspace_path or os.getcwd()
                )

                if result.returncode == 0:
                    success_msg = result.stdout.strip()
                    if i > 0:
                        success_msg += f"\n\n✅ Sucesso usando comando alternativo: {cmd}"

                    logging.info(f"✅ Sucesso na tentativa {i+1}")
                    return {"result": success_msg, "error": None}
                else:
                    error_msg = result.stderr.strip() or f"Código de saída {result.returncode}"
                    last_error = error_msg
                    logging.warning(f"❌ Tentativa {i+1} falhou: {error_msg}")
                    continue

            except subprocess.TimeoutExpired:
                last_error = "Comando excedeu tempo limite de 60 segundos"
                logging.error(f"⏰ Timeout na tentativa {i+1}")
                continue
            except Exception as e:
                last_error = str(e)
                logging.error(f"🚫 Erro na tentativa {i+1}: {e}")
                continue

        # Se todas as tentativas falharam
        fallback_result = f"❌ Todas as {len(commands_to_try)} tentativas falharam.\n\n"
        fallback_result += f"Último erro: {last_error}\n\n"
        fallback_result += "💡 Sugestão: Comando pode não estar disponível neste ambiente Nix/Replit"

        return {"result": fallback_result, "error": f"Falha após {len(commands_to_try)} tentativas: {last_error}"}

    def set_workspace(self, workspace_path: Optional[str], **_):
        if workspace_path:
            self.workspace_path = workspace_path
