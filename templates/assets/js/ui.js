Applied changes to the ModalManager and ProjectSystem to support artifact visualization.
<replit_final_file>
/* CodeR UI Manager - Utility functions and managers */

// Global state management
const UIState = {
    isLoading: false,
    responseReceived: false,
    currentEventSource: null,
    planCards: {},
    activePlanId: null
};

// Utility functions
function getElementById(id) {
    return document.getElementById(id);
}

function addEventListenerSafe(element, event, handler) {
    if (element && typeof handler === 'function') {
        element.addEventListener(event, handler);
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function generateId(prefix = 'id') {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function formatMessage(content) {
    if (!content) return '';
    return content.replace(/\n/g, '<br>');
}

// Button Manager
const ButtonManager = {
    updateSendButton() {
        const input = getElementById('messageInput');
        const button = getElementById('sendButton') || document.querySelector('button[type="submit"]');

        if (button) {
            const hasText = input && input.value.trim().length > 0;
            button.disabled = !hasText || UIState.isLoading;

            if (UIState.isLoading) {
                button.innerHTML = `
                    <svg class="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 12a9 9 0 11-6.219-8.56"/>
                    </svg>
                `;
            } else {
                button.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                `;
            }
        }
    },

    setLoadingState(loading) {
        UIState.isLoading = loading;
        this.updateSendButton();
    }
};

// Input Manager
const InputManager = {
    init() {
        const input = getElementById('messageInput');
        if (input) {
            // Auto-resize functionality
            addEventListenerSafe(input, 'input', this.autoResize.bind(this));

            // Update button state on input
            addEventListenerSafe(input, 'input', debounce(() => {
                ButtonManager.updateSendButton();
            }, 100));

            // Handle key combinations
            addEventListenerSafe(input, 'keydown', this.handleKeyDown.bind(this));

            // Initialize button state
            ButtonManager.updateSendButton();
        }
    },

    autoResize() {
        const input = getElementById('messageInput');
        if (input) {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 128) + 'px';
        }
    },

    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (window.ChatManager && typeof window.ChatManager.sendMessage === 'function') {
                window.ChatManager.sendMessage();
            }
        }
    },

    clear() {
        const input = getElementById('messageInput');
        if (input) {
            input.value = '';
            input.style.height = 'auto';
            ButtonManager.updateSendButton();
        }
    },

    getValue() {
        const input = getElementById('messageInput');
        return input ? input.value.trim() : '';
    },

    focus() {
        const input = getElementById('messageInput');
        if (input) {
            input.focus();
        }
    }
};

// Status Manager
const StatusManager = {
    updateStatus(status, message) {
        console.log(`Status: ${status} - ${message}`);
        // You can add visual status indicators here if needed
    }
};

// Modal Manager
const ModalManager = {
    openArtifactModal(artifact) {
        console.log('Opening artifact modal:', artifact);
        // Implement modal functionality if needed
    },

    closeArtifactModal() {
        console.log('Closing artifact modal');
        // Implement modal close functionality if needed
    },

    escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
     },

    showFileViewerModal(content, fileName, filePath) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-full flex flex-col">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">${fileName}</h3>
                    <div class="flex gap-2">
                        <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="flex-1 p-4 overflow-auto">
                    <pre class="bg-gray-100 p-4 rounded text-sm overflow-auto"><code>${this.escapeHtml(content)}</code></pre>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        };
    },

    showArtifactViewerModal(content, fileName, filePath) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-full flex flex-col">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">📊 ${fileName}</h3>
                    <div class="flex gap-2">
                        <button onclick="window.ProjectSystem.switchArtifactTab('preview', '${filePath}', event)" class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                            Visualização
                        </button>
                        <button onclick="window.ProjectSystem.switchArtifactTab('code', '${filePath}', event)" class="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700">
                            Código
                        </button>
                        <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                <div id="artifact-content" class="flex-1 overflow-hidden">
                    <iframe 
                        src="data:text/html;charset=utf-8,${encodeURIComponent(content)}" 
                        class="w-full h-full border-0"
                        sandbox="allow-scripts allow-same-origin allow-forms"
                        frameborder="0"
                    ></iframe>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        };
    },

    switchArtifactTab(tabType, filePath, event) {
        const modal = event.target.closest('.fixed');
        const contentDiv = modal.querySelector('#artifact-content'); // Changed variable name to avoid conflict
        const buttons = modal.querySelectorAll('button[onclick*="switchArtifactTab"]');

        // Atualizar botões
        buttons.forEach(btn => btn.classList.remove('bg-blue-600', 'bg-green-600'));
        event.target.classList.add(tabType === 'preview' ? 'bg-blue-600' : 'bg-green-600');

        if (tabType === 'preview') {
            // Buscar conteúdo do arquivo e mostrar preview
            fetch(`/api/projects/file?path=${encodeURIComponent(filePath)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        contentDiv.innerHTML = `
                            <iframe 
                                src="data:text/html;charset=utf-8,${encodeURIComponent(data.content)}" 
                                class="w-full h-full border-0"
                                sandbox="allow-scripts allow-same-origin allow-forms"
                                frameborder="0"
                            ></iframe>
                        `;
                    }
                });
        } else {
            // Mostrar código fonte
            fetch(`/api/projects/file?path=${encodeURIComponent(filePath)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        contentDiv.innerHTML = `
                            <div class="p-4 h-full overflow-auto bg-gray-900">
                                <pre class="text-green-400 text-sm"><code>${this.escapeHtml(data.content)}</code></pre>
                            </div>
                        `;
                    }
                });
        }
    },

    openFileViewer(filePath, fileName) {
        console.log('📖 Opening file viewer for:', filePath);

        // Abrir arquivo em iframe com sistema de abas
        this.openFileInIframe(filePath, fileName);
    },

    openFileInIframe(filePath, fileName) {
        console.log('📄 Opening file in iframe:', fileName);

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
            this.switchToTab(existingTab);
            return;
        }

        // Criar nova aba
        this.createFileTab(filePath, fileName);
    },

    createFileTab(filePath, fileName) {
        const tabContainer = document.getElementById('tabContainer');
        const editorContainer = document.getElementById('editorContainer');

        if (!tabContainer || !editorContainer) {
            console.error('Tab container ou editor container não encontrado');
            return;
        }

        // Criar aba
        const tabId = `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const iframeId = `iframe_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        const tab = document.createElement('div');
        tab.className = 'tab';
        tab.dataset.filePath = filePath;
        tab.dataset.tabId = tabId;
        tab.dataset.iframeId = iframeId;

        // Determinar ícone baseado na extensão
        const extension = fileName.split('.').pop()?.toLowerCase() || '';
        const iconClass = this.getFileIcon(extension);

        tab.innerHTML = `
            <i class="${iconClass}" style="margin-right: 8px;"></i>
            <span>${fileName}</span>
            <button class="tab-close-btn" onclick="window.ProjectSystem.closeTab('${tabId}', event)">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Adicionar event listener para ativar aba
        tab.addEventListener('click', (e) => {
            if (!e.target.closest('.tab-close-btn')) {
                this.switchToTab(tab);
            }
        });

        tabContainer.appendChild(tab);

        // Criar iframe
        const iframe = document.createElement('iframe');
        iframe.id = iframeId;
        iframe.className = 'editor-frame';
        iframe.style.cssText = 'width: 100%; height: 100%; border: none; background: #1a1a1a;';
        
        // Criar URL para visualização do arquivo
        const fileUrl = `/api/projects/file?path=${encodeURIComponent(filePath)}`;
        
        // Para arquivos HTML, mostrar diretamente
        if (fileName.endsWith('.html')) {
            fetch(fileUrl)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        iframe.srcdoc = data.content;
                    } else {
                        iframe.srcdoc = `<html><body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #ff6b6b;">Erro ao carregar arquivo: ${data.error}</body></html>`;
                    }
                })
                .catch(error => {
                    iframe.srcdoc = `<html><body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #ff6b6b;">Erro ao carregar arquivo: ${error.message}</body></html>`;
                });
        } else {
            // Para outros arquivos, mostrar como código
            fetch(fileUrl)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const language = this.getLanguageFromExtension(extension);
                        iframe.srcdoc = this.createCodeViewerHTML(data.content, fileName, language);
                    } else {
                        iframe.srcdoc = `<html><body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #ff6b6b;">Erro ao carregar arquivo: ${data.error}</body></html>`;
                    }
                })
                .catch(error => {
                    iframe.srcdoc = `<html><body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #ff6b6b;">Erro ao carregar arquivo: ${error.message}</body></html>`;
                });
        }

        editorContainer.appendChild(iframe);

        // Ativar nova aba
        this.switchToTab(tab);
    },

    switchToTab(targetTab) {
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
    },

    getFileIcon(extension) {
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
    },

    getLanguageFromExtension(extension) {
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
    },

    createCodeViewerHTML(content, fileName, language) {
        const escapedContent = this.escapeHtml(content);
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
            justify-content: between;
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
            margin-left: auto;
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
    <pre class="line-numbers"><code class="language-${language}">${escapedContent}</code></pre>
    
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
};

// File Manager
const FileManager = {
    attachFile() {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.accept = '*/*';

        input.onchange = (event) => {
            const files = Array.from(event.target.files);
            if (files.length > 0) {
                console.log('Files selected:', files.map(f => f.name));
                // Process files here
                if (window.ChatManager && typeof window.ChatManager.processMultipleFiles === 'function') {
                    window.ChatManager.processMultipleFiles(files);
                }
            }
        };

        input.click();
    }
};

// Notification Manager
const NotificationManager = {
    success(message) {
        console.log('✅ Success:', message);
        this.showToast(message, 'success');
    },

    error(message) {
        console.error('❌ Error:', message);
        this.showToast(message, 'error');
    },

    warning(message) {
        console.warn('⚠️ Warning:', message);
        this.showToast(message, 'warning');
    },

    info(message) {
        console.log('ℹ️ Info:', message);
        this.showToast(message, 'info');
    },

    showToast(message, type = 'info') {
        // Simple console-based notification for now
        // You can implement visual toasts later if needed
        const emoji = {
            success: '✅',
            error: '❌', 
            warning: '⚠️',
            info: 'ℹ️'
        }[type] || 'ℹ️';

        console.log(`${emoji} ${message}`);
    }
};

// Project System
const ProjectSystem = {
    init() {
        console.log('📁 Project System initialized');
    },

    closeTab(tabId, event) {
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
                    window.ModalManager.switchToTab(otherTabs[otherTabs.length - 1]);
                } else {
                    // Não há mais abas, mostrar chat
                    this.showChatInterface();
                }
            }

            // Remover aba e iframe
            tab.remove();
            iframe.remove();
        }
    },

    closeAllTabs() {
        const tabs = document.querySelectorAll('.tab');
        const iframes = document.querySelectorAll('.editor-frame');
        
        tabs.forEach(tab => tab.remove());
        iframes.forEach(iframe => iframe.remove());
        
        this.showChatInterface();
    },

    showChatInterface() {
        const tabContainer = document.getElementById('tabContainer');
        const editorContainer = document.getElementById('editorContainer');
        const chatContent = document.getElementById('chatContent');

        if (tabContainer && editorContainer && chatContent) {
            tabContainer.classList.add('hidden');
            editorContainer.classList.add('hidden');
            chatContent.classList.remove('hidden');
        }
    },

    // Placeholder for switchArtifactTab if it's defined elsewhere
    switchArtifactTab: () => {},
};

// Global markdown renderer
window.renderMarkdown = function(content) {
    if (!content) return '';

    // Use marked.js if available
    if (window.marked) {
        try {
            return window.marked.parse(content);
        } catch (error) {
            console.warn('Markdown parse error:', error);
        }
    }

    // Simple fallback
    return content.replace(/\n/g, '<br>');
};

// Export to global scope
window.UIState = UIState;
window.ButtonManager = ButtonManager;
window.InputManager = InputManager;
window.StatusManager = StatusManager;
window.ModalManager = ModalManager;
window.FileManager = FileManager;
window.NotificationManager = NotificationManager;
window.ProjectSystem = ProjectSystem;

console.log('🎨 UI System loaded successfully');