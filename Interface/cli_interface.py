
"""
Interface de linha de comando para o MOMO.
"""

import time
import logging
from typing import Optional
from contextlib import contextmanager

try:
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from Pipeline import CODERPipeline, APIKeyNotFoundError

class CODERInterface:
    """Interface de linha de comando rica para o MOMO."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.coder_system = None
        
    def show_welcome(self):
        """Exibe mensagem de boas-vindas elegante."""
        welcome_text = """
# 🤖 CODER - Assistente IA Autônoma

Olá! Sou o **CODER**, seu assistente IA capaz de realizar tarefas complexas autonomamente.

## 🚀 O que posso fazer:
- 🔍 **Pesquisar** informações na web
- 💻 **Executar** código Python e comandos
- 📊 **Criar** relatórios e gráficos
- 🔧 **Corrigir** erros automaticamente
- 🧠 **Aprender** com interações anteriores

Digite **'sair'** para terminar a qualquer momento.
"""
        
        if RICH_AVAILABLE:
            self.console.print(Panel(
                Markdown(welcome_text),
                title="[bold blue]MOMO System[/bold blue]",
                border_style="blue"
            ))
        else:
            print(welcome_text)
            
    def show_error(self, title: str, message: str):
        """Exibe mensagem de erro elegante."""
        if RICH_AVAILABLE:
            self.console.print(Panel(
                f"[red]{message}[/red]",
                title=f"[bold red]❌ {title}[/bold red]",
                border_style="red"
            ))
        else:
            print(f"\n❌ {title}: {message}")
            
    @contextmanager
    def show_thinking(self, message: str):
        """Context manager para mostrar progresso de processamento."""
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(f"[cyan]{message}[/cyan]", total=None)
                yield progress
        else:
            print(f"\n🤔 {message}")
            yield None
            
    def show_response(self, response: str, execution_log: list):
        """Exibe resposta do MOMO de forma elegante."""
        if RICH_AVAILABLE:
            # Resposta principal
            self.console.print(Panel(
                Markdown(response),
                title="[bold green]🤖 MOMO Responde[/bold green]",
                border_style="green"
            ))
            
            # Log de execução (se houver)
            if execution_log and len(execution_log) > 1:
                log_text = "\n".join([f"• {step}" for step in execution_log])
                self.console.print(Panel(
                    log_text,
                    title="[bold yellow]📋 Passos Executados[/bold yellow]",
                    border_style="yellow"
                ))
        else:
            print(f"\n🤖 MOMO: {response}")
            if execution_log:
                print(f"\n📋 Passos: {len(execution_log)} executados")
                
    def show_progress(self, steps_completed: int, total_steps: int):
        """Mostra progresso da execução."""
        if total_steps > 0:
            progress_text = f"[bold cyan]📋 Concluído: {steps_completed}/{total_steps} passos[/bold cyan]"
            if RICH_AVAILABLE:
                self.console.print(progress_text)
            else:
                print(f"📋 Progresso: {steps_completed}/{total_steps}")
            
    def get_user_input(self) -> str:
        """Obtém input do usuário de forma elegante."""
        if RICH_AVAILABLE:
            return Prompt.ask(
                "\n[bold yellow]💬 Você[/bold yellow]",
                console=self.console
            )
        else:
            return input("\n💬 Você: ")
        
    def initialize_coder(self) -> bool:
        """Inicializa o sistema CODER."""
        try:
            with self.show_thinking("Inicializando sistema CODER..."):
                time.sleep(1)  # Simula carregamento
                self.coder_system = CODERPipeline()
                
            if RICH_AVAILABLE:
                self.console.print("[bold green]✅ Sistema MOMO inicializado com sucesso![/bold green]\n")
            else:
                print("✅ Sistema MOMO inicializado com sucesso!")
            return True
            
        except APIKeyNotFoundError:
            self.show_error(
                "Configuração Necessária",
                "Chave da API da OpenAI não encontrada.\nPor favor, defina a variável de ambiente 'OPENAI_API_KEY'."
            )
            return False
            
        except Exception as e:
            self.show_error("Erro de Inicialização", str(e))
            return False
            
    def process_request(self, user_input: str):
        """Processa pedido do usuário com feedback elegante."""
        if not self.coder_system:
            self.show_error("Sistema Não Inicializado", "O sistema CODER não foi inicializado.")
            return
            
        try:
            with self.show_thinking("CODER está processando seu pedido..."):
                result = self.coder_system.process_request(user_input)
                
            self.show_response(
                result['final_response'],
                result['execution_log']
            )
            
        except Exception as e:
            self.show_error("Erro no Processamento", str(e))
            
    def run(self):
        """Executa a interface principal."""
        self.show_welcome()
        
        if not self.initialize_coder():
            return
            
        while True:
            try:
                user_input = self.get_user_input()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    if RICH_AVAILABLE:
                        self.console.print("\n[bold blue]👋 Até logo! Foi um prazer ajudar.[/bold blue]")
                    else:
                        print("\n👋 Até logo!")
                    break
                    
                self.process_request(user_input)
                
            except KeyboardInterrupt:
                if RICH_AVAILABLE:
                    self.console.print("\n[bold blue]👋 Interrompido pelo usuário. Até logo![/bold blue]")
                else:
                    print("\n👋 Até logo!")
                break
                
            except Exception as e:
                self.show_error("Erro Inesperado", str(e))
