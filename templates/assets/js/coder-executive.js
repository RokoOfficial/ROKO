/* CODER Executive Functions */

// Função para copiar código com feedback mobile-friendly
function copyToClipboard(text) {
    // Tentar usar a API moderna de clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showCopyNotification('✅ Código copiado!', 'success');
        }).catch(err => {
            console.error('Erro ao copiar código:', err);
            // Fallback para dispositivos mais antigos
            fallbackCopyToClipboard(text);
        });
    } else {
        // Fallback para dispositivos sem suporte à API moderna
        fallbackCopyToClipboard(text);
    }
}

// Fallback para copiar código em dispositivos antigos/mobile
function fallbackCopyToClipboard(text) {
    try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);

        if (successful) {
            showCopyNotification('✅ Código copiado!', 'success');
        } else {
            showCopyNotification('❌ Erro ao copiar', 'error');
        }
    } catch (err) {
        console.error('Erro no fallback de cópia:', err);
        showCopyNotification('❌ Erro ao copiar', 'error');
    }
}

// Mostrar notificação de cópia mobile-friendly
function showCopyNotification(message, type = 'success') {
    // Remover notificação anterior se existir
    const existingNotification = document.querySelector('.copy-notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    const notification = document.createElement('div');
    notification.className = `copy-notification fixed top-4 left-1/2 transform -translate-x-1/2 px-4 py-3 rounded-lg z-50 font-mono text-sm shadow-lg border transition-all duration-300 ${
        type === 'success'
            ? 'bg-green-600 text-white border-green-500 shadow-green-500/25'
            : 'bg-red-600 text-white border-red-500 shadow-red-500/25'
    }`;

    notification.innerHTML = `
        <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full ${type === 'success' ? 'bg-green-300' : 'bg-red-300'} animate-pulse"></div>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    // Animar entrada
    setTimeout(() => {
        notification.style.transform = 'translateX(-50%) translateY(0)';
        notification.style.opacity = '1';
    }, 10);

    // Remover após delay
    setTimeout(() => {
        notification.style.transform = 'translateX(-50%) translateY(-100%)';
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 2500);
}

// Sistema de execução de comandos em tempo real
class CODERExecutiveMode {
    constructor() {
        this.activeExecution = null;
        this.commandQueue = [];
        this.isExecuting = false;
    }

    // Iniciar execução de comandos
    async startExecution(commands, containerId) {
        this.isExecuting = true;
        this.commandQueue = [...commands];

        const container = document.getElementById(containerId);
        if (!container) return;

        // Criar terminal de execução
        const terminal = this.createExecutionTerminal(commands);
        container.appendChild(terminal);

        // Executar comandos sequencialmente
        for (let i = 0; i < commands.length; i++) {
            await this.executeCommand(i, commands[i], terminal);
            await this.delay(800); // Delay entre comandos
        }

        this.isExecuting = false;
        this.updateTerminalStatus(terminal, 'completed');
    }

    // Criar terminal de execução
    createExecutionTerminal(commands) {
        const terminal = document.createElement('div');
        terminal.className = 'execution-terminal coder-executive-mode animate-fade-in';

        terminal.innerHTML = `
            <div class="execution-header">
                <div class="execution-status">
                    <div class="status-indicator running"></div>
                    <span>CODER Executando</span>
                </div>
                <div class="text-xs text-gray-400">
                    ${commands.length} comando${commands.length !== 1 ? 's' : ''} na fila
                </div>
            </div>
            <ol class="command-sequence">
                ${commands.map((cmd, index) => `
                    <li class="command-step" data-step="${index}">
                        <div class="flex items-start gap-3">
                            <span class="step-number">${index + 1}</span>
                            <div class="flex-1">
                                <div class="flex items-center gap-2">
                                    <span class="command-name">${cmd.command}</span>
                                    <span class="command-args">${(cmd.args || []).join(' ')}</span>
                                </div>
                                <div class="command-description">${cmd.description}</div>
                                <div class="execution-result hidden" id="result-${index}"></div>
                            </div>
                        </div>
                    </li>
                `).join('')}
            </ol>
        `;

        return terminal;
    }

    // Executar comando individual
    async executeCommand(index, command, terminal) {
        const stepElement = terminal.querySelector(`[data-step="${index}"]`);
        const resultElement = terminal.querySelector(`#result-${index}`);

        // Marcar como ativo
        stepElement.classList.add('active');

        // Simular execução
        await this.simulateCommandExecution(command, resultElement);

        // Marcar como concluído
        stepElement.classList.remove('active');
        stepElement.classList.add('completed');
    }

    // Simular execução de comando
    async simulateCommandExecution(command, resultElement) {
        const messages = this.getCommandMessages(command);

        for (const message of messages) {
            await this.typeMessage(resultElement, message);
            await this.delay(300);
        }
    }

    // Obter mensagens de execução baseadas no comando
    getCommandMessages(command) {
        const messageMap = {
            'coder-analyze': [
                'Analisando entrada do usuário...',
                'Identificando padrões e intenções...',
                'Análise concluída ✓'
            ],
            'coder-create': [
                'Preparando estrutura de arquivo...',
                'Definindo formato e conteúdo...',
                'Arquivo pronto para criação ✓'
            ],
            'coder-execute': [
                'Validando ambiente de execução...',
                'Executando código com segurança...',
                'Execução concluída com sucesso ✓'
            ],
            'coder-install': [
                'Verificando dependências...',
                'Resolvendo conflitos automático...',
                'Instalação finalizada ✓'
            ],
            'coder-finalize': [
                'Validando resultado final...',
                'Otimizando performance...',
                'Processo finalizado com sucesso ✓'
            ]
        };

        return messageMap[command.command] || ['Executando...', 'Concluído ✓'];
    }

    // Digitar mensagem com efeito typewriter
    async typeMessage(element, message) {
        element.classList.remove('hidden');
        element.innerHTML = '';

        for (let i = 0; i < message.length; i++) {
            element.innerHTML += message[i];
            await this.delay(20); // 20ms por caractere
        }
    }

    // Atualizar status do terminal
    updateTerminalStatus(terminal, status) {
        const indicator = terminal.querySelector('.status-indicator');
        const statusText = terminal.querySelector('.execution-status span');

        indicator.className = `status-indicator ${status}`;

        const statusTexts = {
            running: 'CODER Executando',
            completed: 'CODER Finalizado',
            error: 'CODER Erro'
        };

        statusText.textContent = statusTexts[status] || 'CODER Status';
    }

    // Delay helper
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Instância global
window.CODERExecutive = new CODERExecutiveMode();

// Integração com o sistema de chat
window.ChatManager.displayCommandFlow = async function(commands) {
    const container = document.getElementById('messages-container');
    if (!container) return;

    // Usar o sistema executivo
    await window.CODERExecutive.startExecution(commands, 'messages-container');
    this.scrollToBottom();
};

// --- MODIFICAÇÕES PARA ABRIR ARQUIVOS ---

// Event listener para cliques em arquivos e pastas  
document.addEventListener('DOMContentLoaded', function() {
    // Aguardar um pouco para garantir que os elementos do projeto foram carregados
    setTimeout(() => {
        // Buscar por diferentes possíveis seletores para a lista de arquivos
        const possibleSelectors = ['#projectFiles', '.project-tree', '.file-list', '[data-project-files]', '.sidebar .space-y-2'];
        let projectList = null;
        
        for (const selector of possibleSelectors) {
            projectList = document.querySelector(selector);
            if (projectList) {
                console.log('📁 Encontrado container de projetos:', selector);
                break;
            }
        }
        
        // Se ainda não encontrou, usar delegação de evento no documento
        if (!projectList) {
            console.log('📁 Usando delegação de evento global para arquivos');
            document.addEventListener('click', handleFileClick);
        } else {
            projectList.addEventListener('click', handleFileClick);
        }
        
        function handleFileClick(e) {
            // Procurar pelo item clicado (li, div, ou qualquer elemento com data-path)
            const listItem = e.target.closest('[data-path]') || e.target.closest('li') || e.target.closest('.project-item');
            if (!listItem) return;

            const itemType = listItem.dataset.type;
            const itemPath = listItem.dataset.path;
            const itemName = listItem.dataset.name || listItem.textContent?.trim() || 'arquivo';

            console.log('🖱️ Clique detectado:', {
                itemType,
                itemName,
                itemPath,
                element: listItem
            });

            if (itemType === 'folder') {
                // Toggle da pasta
                listItem.classList.toggle('expanded');

                // Animação visual
                listItem.classList.add('clicking-folder');
                setTimeout(() => listItem.classList.remove('clicking-folder'), 200);

            } else if (itemType === 'file') {
                // Prevenir propagação para evitar cliques duplos
                e.preventDefault();
                e.stopPropagation();
                
                console.log('📄 Abrindo arquivo:', itemName, 'em:', itemPath);

                // Animação visual
                listItem.classList.add('clicking-file');
                setTimeout(() => listItem.classList.remove('clicking-file'), 300);

                // Abrir arquivo usando o sistema de abas
                openFileInTabs(itemPath, itemName);
            }
        }
    }, 1000); // Aguardar 1 segundo para carregar elementos
});


    // Função para abrir arquivo em sistema de abas
    function openFileInTabs(filePath, fileName) {
        console.log('📂 Abrindo arquivo em abas:', fileName);

        try {
            // Verificar se o ModalManager existe e tem a função
            if (window.ModalManager && typeof window.ModalManager.openFileViewer === 'function') {
                console.log('✅ Usando ModalManager.openFileViewer');
                window.ModalManager.openFileViewer(filePath, fileName);
            }
            // Fallback: usar função direta do sistema de abas
            else if (window.ModalManager && typeof window.ModalManager.openFileInIframe === 'function') {
                console.log('✅ Usando ModalManager.openFileInIframe');
                window.ModalManager.openFileInIframe(filePath, fileName);
            }
            // Outro fallback: criar aba manualmente
            else {
                console.log('✅ Criando aba manualmente');
                createFileTabManually(filePath, fileName);
            }
        } catch (error) {
            console.error('❌ Erro ao abrir arquivo:', error);
            // Fallback final: mostrar modal simples
            showSimpleFileModal(filePath, fileName);
        }
    }

    // Função para criar aba manualmente
    function createFileTabManually(filePath, fileName) {
        console.log('🔧 Criando aba manual para:', fileName);

        // Mostrar containers de abas e editor
        const tabContainer = document.getElementById('tabContainer');
        const editorContainer = document.getElementById('editorContainer');
        const chatContent = document.getElementById('chatContent');

        if (tabContainer && editorContainer && chatContent) {
            tabContainer.classList.remove('hidden');
            editorContainer.classList.remove('hidden');
            chatContent.classList.add('hidden');
        }

        // Verificar se arquivo já está aberto
        const existingTab = document.querySelector(`[data-file-path="${filePath}"]`);
        if (existingTab) {
            // Ativar aba existente
            activateTab(existingTab);
            return;
        }

        // Criar nova aba
        const tabId = `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const iframeId = `iframe_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // Criar elemento da aba
        const tab = document.createElement('div');
        tab.className = 'tab';
        tab.dataset.filePath = filePath;
        tab.dataset.tabId = tabId;
        tab.dataset.iframeId = iframeId;

        // Determinar ícone baseado na extensão
        const extension = fileName.split('.').pop()?.toLowerCase() || '';
        const iconClass = getFileIcon(extension);

        tab.innerHTML = `
            <i class="${iconClass}" style="margin-right: 8px;"></i>
            <span>${fileName}</span>
            <button class="tab-close-btn" onclick="closeFileTab('${tabId}', event)">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Adicionar event listener para ativar aba
        tab.addEventListener('click', (e) => {
            if (!e.target.closest('.tab-close-btn')) {
                activateTab(tab);
            }
        });

        if (tabContainer) {
            tabContainer.appendChild(tab);
        }

        // Criar iframe para o arquivo
        createFileIframe(iframeId, filePath, fileName);

        // Ativar nova aba
        activateTab(tab);
    }

    // Função para criar iframe do arquivo
    function createFileIframe(iframeId, filePath, fileName) {
        const editorContainer = document.getElementById('editorContainer');
        if (!editorContainer) return;

        const iframe = document.createElement('iframe');
        iframe.id = iframeId;
        iframe.className = 'editor-frame';
        iframe.style.cssText = 'width: 100%; height: 100%; border: none; background: #1a1a1a;';

        console.log('🔗 Carregando arquivo:', filePath);

        // Buscar conteúdo do arquivo via API
        fetch(`/api/projects/file?path=${encodeURIComponent(filePath)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const extension = fileName.split('.').pop()?.toLowerCase() || '';

                    // Para arquivos HTML, mostrar diretamente
                    if (extension === 'html') {
                        iframe.srcdoc = data.content;
                    } else {
                        // Para outros arquivos, criar visualizador de código
                        const language = getLanguageFromExtension(extension);
                        iframe.srcdoc = createCodeViewerHTML(data.content, fileName, language);
                    }
                } else {
                    iframe.srcdoc = createErrorHTML(`Erro ao carregar arquivo: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Erro ao buscar arquivo:', error);
                iframe.srcdoc = createErrorHTML(`Erro de rede: ${error.message}`);
            });

        editorContainer.appendChild(iframe);
    }

    // Função para ativar aba
    function activateTab(targetTab) {
        // Remover active de todas as abas
        const allTabs = document.querySelectorAll('.tab');
        allTabs.forEach(tab => tab.classList.remove('active'));

        // Ocultar todos os iframes
        const allIframes = document.querySelectorAll('.editor-frame');
        allIframes.forEach(iframe => iframe.classList.add('hidden'));

        // Ativar aba selecionada
        targetTab.classList.add('active');

        // Mostrar iframe correspondente
        const iframeId = targetTab.dataset.iframeId;
        const iframe = document.getElementById(iframeId);
        if (iframe) {
            iframe.classList.remove('hidden');
        }
    }

    // Função para fechar aba
    window.closeFileTab = function(tabId, event) {
        if (event) {
            event.stopPropagation();
        }

        const tab = document.querySelector(`[data-tab-id="${tabId}"]`);
        const iframe = document.getElementById(tab?.dataset.iframeId);

        if (tab && iframe) {
            // Se esta aba estava ativa, ativar outra
            if (tab.classList.contains('active')) {
                const otherTabs = document.querySelectorAll('.tab:not([data-tab-id="' + tabId + '"])');
                if (otherTabs.length > 0) {
                    activateTab(otherTabs[otherTabs.length - 1]);
                } else {
                    // Não há mais abas, mostrar chat
                    showChatInterface();
                }
            }

            // Remover aba e iframe
            tab.remove();
            iframe.remove();
        }
    };

    // Função para mostrar interface do chat
    function showChatInterface() {
        const tabContainer = document.getElementById('tabContainer');
        const editorContainer = document.getElementById('editorContainer');
        const chatContent = document.getElementById('chatContent');

        if (tabContainer && editorContainer && chatContent) {
            tabContainer.classList.add('hidden');
            editorContainer.classList.add('hidden');
            chatContent.classList.remove('hidden');
        }
    }

    // Função para mostrar modal simples como fallback
    function showSimpleFileModal(filePath, fileName) {
        console.log('📄 Mostrando modal simples para:', fileName);

        fetch(`/api/projects/file?path=${encodeURIComponent(filePath)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modal = document.createElement('div');
                    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
                    modal.innerHTML = `
                        <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-full flex flex-col">
                            <div class="flex justify-between items-center p-4 border-b">
                                <h3 class="text-lg font-semibold">${fileName}</h3>
                                <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                    </svg>
                                </button>
                            </div>
                            <div class="flex-1 p-4 overflow-auto">
                                <pre class="bg-gray-100 p-4 rounded text-sm overflow-auto"><code>${escapeHtml(data.content)}</code></pre>
                            </div>
                        </div>
                    `;

                    document.body.appendChild(modal);
                    modal.onclick = (e) => {
                        if (e.target === modal) {
                            modal.remove();
                        }
                    };
                }
            })
            .catch(error => {
                console.error('Erro ao carregar arquivo:', error);
                alert(`Erro ao abrir arquivo: ${error.message}`);
            });
    }

// Funções auxiliares
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getFileIcon(extension) {
    const iconMap = {
        'html': 'fas fa-file-code icon-html',
        'css': 'fab fa-css3-alt icon-css',
        'js': 'fab fa-js-square icon-js',
        'ts': 'fab fa-js-square icon-ts',
        'py': 'fab fa-python icon-py',
        'md': 'fab fa-markdown icon-md',
        'json': 'fas fa-file-code icon-json',
        'jsx': 'fab fa-react icon-react',
        'tsx': 'fab fa-react icon-react',
        'java': 'fab fa-java icon-java',
        'cpp': 'fas fa-file-code icon-cpp',
        'c': 'fas fa-file-code icon-cpp',
        'cs': 'fas fa-file-code icon-csharp',
        'txt': 'fas fa-file-alt icon-file',
        'xml': 'fas fa-file-code icon-file',
        'sql': 'fas fa-database icon-file'
    };
    return iconMap[extension] || 'fas fa-file icon-file';
}

function getLanguageFromExtension(extension) {
    const languageMap = {
        'html': 'html',
        'css': 'css',
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'md': 'markdown',
        'json': 'json',
        'jsx': 'jsx',
        'tsx': 'tsx',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'cs': 'csharp',
        'xml': 'xml',
        'sql': 'sql'
    };
    return languageMap[extension] || 'text';
}

function createCodeViewerHTML(content, fileName, language) {
    return `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${fileName}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-dark.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #e5e7eb;
            font-family: 'JetBrains Mono', 'Monaco', 'Consolas', monospace;
            line-height: 1.5;
        }
        .header {
            background: #2a2a2a;
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #404040;
        }
        .file-name {
            font-weight: 600;
            color: #60a5fa;
        }
        .copy-btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .copy-btn:hover {
            background: #2563eb;
        }
        pre {
            margin: 0;
            background: #111111 !important;
            border: 1px solid #404040;
            border-radius: 8px;
            overflow-x: auto;
        }
        code {
            font-family: 'JetBrains Mono', 'Monaco', 'Consolas', monospace !important;
            font-size: 14px;
        }
        .line-numbers .line-numbers-rows {
            border-right: 1px solid #404040;
        }
    </style>
</head>
<body>
    <div class="header">
        <span class="file-name">${fileName}</span>
        <button class="copy-btn" onclick="copyToClipboard()">Copiar</button>
    </div>
    <pre class="line-numbers"><code class="language-${language}">${escapeHtml(content)}</code></pre>

    <script>
        function copyToClipboard() {
            const content = ${JSON.stringify(content)};
            if (navigator.clipboard) {
                navigator.clipboard.writeText(content).then(() => {
                    const btn = document.querySelector('.copy-btn');
                    const originalText = btn.textContent;
                    btn.textContent = 'Copiado!';
                    btn.style.background = '#10b981';
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.style.background = '#3b82f6';
                    }, 2000);
                });
            }
        }

        // Inicializar Prism.js
        Prism.highlightAll();
    </script>
</body>
</html>`;
}

function createErrorHTML(errorMessage) {
    return `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro</title>
    <style>
        body {
            margin: 0;
            padding: 40px;
            background: #1a1a1a;
            color: #ef4444;
            font-family: 'Monaco', 'Consolas', monospace;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
        }
        .error-container {
            text-align: center;
            background: #2a2a2a;
            padding: 30px;
            border-radius: 12px;
            border: 1px solid #ef4444;
        }
        .error-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        .error-message {
            font-size: 16px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <div class="error-message">${errorMessage}</div>
        <p style="color: #9ca3af; font-size: 12px;">Tente recarregar ou entre em contato com o suporte</p>
    </div>
</body>
</html>`;
}