// ChatManager - Sistema de Chat Completo
class ChatManager {
    constructor() {
        this.isInitialized = false;
        this.messageForm = null;
        this.messageInput = null;
        this.chatMessages = null;
        this.loadingIndicator = null;
        this.currentEventSource = null;
        this.isProcessing = false;
        this.retryCount = 0;
        this.maxRetries = 3;

        console.log('[ChatManager] Instance created');
    }

    init() {
        try {
            console.log('[ChatManager] Initializing...');

            // Buscar elementos do DOM
            this.messageForm = document.getElementById('messageForm');
            this.messageInput = document.getElementById('messageInput');
            this.chatMessages = document.getElementById('chatMessages');
            this.loadingIndicator = document.getElementById('loadingIndicator');

            if (!this.messageForm || !this.messageInput || !this.chatMessages) {
                console.error('[ChatManager] ERROR: Essential chat elements not found');
                return false;
            }

            // Configurar event listeners
            this.setupEventListeners();

            // Marcar como inicializado
            this.isInitialized = true;
            console.log('[ChatManager] Initialized successfully');

            return true;
        } catch (error) {
            console.error('[ChatManager] ERROR: Failed to initialize:', error);
            return false;
        }
    }

    setupEventListeners() {
        // Event listener para submit do formulário
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        // Event listener para Enter no input
        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }

    async sendMessage() {
        try {
            console.log('[ChatManager] Sending message...');

            if (this.isProcessing) {
                console.log('[ChatManager] WARNING: Already processing a message');
                return;
            }

            const message = this.messageInput?.value?.trim();
            if (!message) {
                console.log('[ChatManager] WARNING: Empty message');
                return;
            }

            this.isProcessing = true;
            this.retryCount = 0;

            // Limpar input e mostrar mensagem do usuário
            this.messageInput.value = '';
            this.addUserMessage(message);
            this.showLoading(true);

            // Enviar para API
            await this.sendToAPI(message);

        } catch (error) {
            console.error('[ChatManager] ERROR: Failed to send message:', error);
            this.handleError(error);
        } finally {
            this.isProcessing = false;
            this.showLoading(false);
        }
    }

    async sendToAPI(message) {
        try {
            console.log('[ChatManager] Sending to API...');

            // Preparar dados
            const data = {
                message: message,
                timestamp: Date.now()
            };

            // Fazer requisição com streaming
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Processar stream se disponível
            if (response.headers.get('content-type')?.includes('text/event-stream')) {
                await this.processEventStream(response);
            } else {
                // Fallback para resposta JSON
                const result = await response.json();
                this.handleAPIResponse(result);
            }

        } catch (error) {
            console.error('[ChatManager] API ERROR:', error);

            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`[ChatManager] RETRY: Attempt ${this.retryCount}/${this.maxRetries}`);
                setTimeout(() => this.sendToAPI(message), 1000 * this.retryCount);
            } else {
                this.handleError(error);
            }
        }
    }

    async processEventStream(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentAIMessage = null;

        try {
            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Processar mensagens completas
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Manter linha incompleta no buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            currentAIMessage = this.handleStreamEvent(data, currentAIMessage);
                        } catch (parseError) {
                            console.warn('Erro ao parsear evento:', parseError);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }

    handleStreamEvent(event, currentMessage) {
        console.log('[ChatManager] Stream event received:', event.type);

        switch (event.type) {
            case 'thinking':
                this.showThinking(event.message);
                break;

            case 'action_start':
                this.showAction(event.action_name, 'iniciada');
                break;

            case 'tool_execution':
                this.showToolUsage(event.tool_name);
                break;

            case 'response':
                if (currentMessage) {
                    this.updateAIMessage(currentMessage, event.message);
                } else {
                    currentMessage = this.addAIMessage(event.message);
                }

                // Processar artefatos se houver
                if (event.artifacts && event.artifacts.length > 0) {
                    this.handleArtifacts(event.artifacts);
                }
                break;

            case 'complete':
                this.hideThinking();
                console.log('[ChatManager] Stream completed');
                break;

            case 'error':
                this.handleError(new Error(event.message || 'Erro no stream'));
                break;
        }

        return currentMessage;
    }

    handleAPIResponse(response) {
        if (response.success === false) {
            throw new Error(response.error || 'Erro desconhecido na API');
        }

        if (response.response) {
            this.addAIMessage(response.response);
        }

        if (response.artifacts && response.artifacts.length > 0) {
            this.handleArtifacts(response.artifacts);
        }
    }

    addUserMessage(message) {
        const messageElement = this.createMessageElement('user', message);
        this.appendMessage(messageElement);
        this.scrollToBottom();
    }

    addAIMessage(message) {
        const messageElement = this.createMessageElement('ai', message);
        this.appendMessage(messageElement);
        this.scrollToBottom();
        return messageElement;
    }

    updateAIMessage(messageElement, newContent) {
        const contentDiv = messageElement.querySelector('.message-content');
        if (contentDiv && window.renderMarkdown) {
            contentDiv.innerHTML = window.renderMarkdown(newContent);
        } else if (contentDiv && window.marked) {
            contentDiv.innerHTML = window.marked.parse(newContent);
        } else if (contentDiv) {
            contentDiv.textContent = newContent;
        }
        this.scrollToBottom();
    }

    createMessageElement(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message mb-4`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content p-4 rounded-2xl';

        // Usar sistema de markdown profissional
        if (type === 'ai' && window.renderMarkdown) {
            contentDiv.innerHTML = window.renderMarkdown(content);
        } else if (window.marked && typeof window.marked.parse === 'function') {
            contentDiv.innerHTML = window.marked.parse(content);
        } else {
            contentDiv.textContent = content;
        }

        messageDiv.appendChild(contentDiv);
        return messageDiv;
    }

    appendMessage(messageElement) {
        if (this.chatMessages) {
            // Remover mensagem de boas-vindas se existir
            const welcomeMessage = document.getElementById('welcomeMessage');
            if (welcomeMessage) {
                welcomeMessage.style.display = 'none';
            }

            this.chatMessages.appendChild(messageElement);
        }
    }

    showThinking(message) {
        // Remover thinking anterior
        this.hideThinking();

        const thinkingDiv = document.createElement('div');
        thinkingDiv.id = 'thinking-indicator';
        thinkingDiv.className = 'thinking-message mb-4 p-3 rounded-lg bg-gray-100 text-gray-600 italic';
        thinkingDiv.innerHTML = `
            <div class="flex items-center">
                <div class="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent mr-2"></div>
                <span>${message}</span>
            </div>
        `;

        this.appendMessage(thinkingDiv);
    }

    hideThinking() {
        const existing = document.getElementById('thinking-indicator');
        if (existing) {
            existing.remove();
        }
    }

    showAction(actionName, status) {
        console.log(`[ChatManager] Action: ${actionName} - ${status}`);
    }

    showToolUsage(toolName) {
        console.log(`[ChatManager] Using tool: ${toolName}`);
    }

    showLoading(show) {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = show ? 'block' : 'none';
        }
    }

    handleArtifacts(artifacts) {
        console.log('[ChatManager] Processing artifacts:', artifacts.length);

        // Criar container para artefatos se não existir
        let artifactsContainer = document.getElementById('artifacts-container');
        if (!artifactsContainer) {
            artifactsContainer = document.createElement('div');
            artifactsContainer.id = 'artifacts-container';
            artifactsContainer.className = 'artifacts-section mt-4 mb-4';
            this.appendMessage(artifactsContainer);
        }

        artifacts.forEach(artifact => {
            this.createArtifactCard(artifact, artifactsContainer);
        });
    }

    createArtifactCard(artifact, container = null) {
        const card = document.createElement('div');
        card.className = 'artifact-notification bg-gradient-to-r from-green-600 to-green-700 border border-green-500 rounded-lg p-4 mb-4 shadow-lg transition-all duration-300 hover:shadow-2xl';

        card.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <div>
                        <h3 class="font-semibold text-white">${artifact.title || 'Artefato Criado'}</h3>
                        <p class="text-sm text-green-100">${artifact.description || `Arquivo salvo: ${artifact.filename}`}</p>
                    </div>
                </div>
                <button 
                    onclick="window.ChatManager.openFileInProject('${artifact.workspace_path || artifact.filename}')" 
                    class="flex items-center gap-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-all duration-200 transform hover:scale-105 font-medium"
                >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                    </svg>
                    Ver Arquivo
                </button>
            </div>
        `;

        // Adicionar ao container apropriado
        if (container) {
            container.appendChild(card);
        } else {
            this.appendMessage(card);
        }
    }

    openArtifactModal(artifactId, artifactUrl, title, artifactData = {}) {
        console.log('[ChatManager] Opening artifact modal:', title, 'URL:', artifactUrl);

        // Validar URL do artefato
        if (!artifactUrl || artifactUrl === 'undefined' || artifactUrl === 'null') {
            console.error('[ChatManager] URL do artefato inválida:', artifactUrl);
            this.showNotification('Erro: URL do artefato não encontrada', 'error');
            return;
        }

        // Parse artifactData se for string
        let parsedData = {};
        if (typeof artifactData === 'string') {
            try {
                parsedData = JSON.parse(artifactData.replace(/&quot;/g, '"').replace(/&#39;/g, "'"));
            } catch (e) {
                console.warn('Could not parse artifact data:', e);
                parsedData = {};
            }
        } else {
            parsedData = artifactData;
        }

        // Remover modal existente se houver
        const existingModal = document.getElementById('artifact-viewer-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Criar novo modal
        const modal = this.createArtifactModal();
        document.body.appendChild(modal);

        // Configurar conteúdo do modal
        const modalTitle = modal.querySelector('#artifact-modal-title');
        const modalTabs = modal.querySelector('#artifact-modal-tabs');
        const modalClose = modal.querySelector('#artifact-modal-close');

        modalTitle.textContent = title || 'Artefato';

        // Criar sistema de abas com URLs escapadas
        const escapedUrl = artifactUrl.replace(/'/g, "\\'");
        modalTabs.innerHTML = `
            <button class="tab-button active" onclick="window.ChatManager.switchArtifactTab('preview', '${escapedUrl}', event)">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                </svg>
                Visualização
            </button>
            <button class="tab-button" onclick="window.ChatManager.switchArtifactTab('code', '${escapedUrl}', event)">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
                </svg>
                Código Fonte
            </button>
        `;

        // Carregar visualização inicialmente
        this.switchArtifactTab('preview', artifactUrl, null);

        // Mostrar modal com animação
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';

        // Event listeners para fechar
        modalClose.onclick = () => this.closeArtifactModal();
        modal.onclick = (e) => {
            if (e.target === modal) this.closeArtifactModal();
        };

        // ESC para fechar
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                this.closeArtifactModal();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);

        console.log('[ChatManager] Modal criado e exibido com sucesso');
    }

    switchArtifactTab(tabType, artifactUrl, event) {
        const modal = document.getElementById('artifact-viewer-modal');
        if (!modal) {
            console.error('[ChatManager] Modal não encontrado');
            return;
        }

        const modalContent = modal.querySelector('#artifact-modal-content');
        const tabs = modal.querySelectorAll('.tab-button');

        if (!modalContent) {
            console.error('[ChatManager] Conteúdo do modal não encontrado');
            return;
        }

        // Atualizar abas visuais
        tabs.forEach(tab => tab.classList.remove('active'));
        if (event && event.target) {
            event.target.classList.add('active');
        } else {
            // Se não houver event (chamada programática), ativar a primeira aba
            tabs[0]?.classList.add('active');
        }

        console.log('[ChatManager] Switching to tab:', tabType, 'URL:', artifactUrl);

        if (tabType === 'preview') {
            const loadingId = `iframe-loading-${Date.now()}`;
            const iframeId = `artifact-iframe-${Date.now()}`;
            
            modalContent.innerHTML = `
                <div class="w-full h-full relative bg-white rounded-lg overflow-hidden">
                    <div class="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-75 rounded-lg" id="${loadingId}">
                        <div class="flex items-center text-white">
                            <svg class="animate-spin -ml-1 mr-3 h-6 w-6 text-white" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Carregando artefato...
                        </div>
                    </div>
                    <iframe 
                        id="${iframeId}"
                        src="${artifactUrl}" 
                        class="w-full h-full border-0"
                        style="min-height: 600px; background: white; opacity: 0; transition: opacity 0.5s ease;"
                        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads"
                        frameborder="0"
                        allowfullscreen
                    ></iframe>
                </div>
            `;

            // Configurar carregamento do iframe
            const iframe = document.getElementById(iframeId);
            const loadingDiv = document.getElementById(loadingId);
            
            if (iframe && loadingDiv) {
                iframe.onload = () => {
                    console.log('[ChatManager] Iframe carregado com sucesso');
                    iframe.style.opacity = '1';
                    loadingDiv.style.display = 'none';
                };
                
                iframe.onerror = () => {
                    console.error('[ChatManager] Erro ao carregar iframe');
                    loadingDiv.innerHTML = `
                        <div class="flex flex-col items-center text-white">
                            <svg class="w-12 h-12 mb-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <p class="text-lg font-semibold">Erro ao carregar artefato</p>
                            <p class="text-sm text-gray-300 mt-2">Tente novamente ou abra em nova aba</p>
                            <a href="${artifactUrl}" target="_blank" class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                                Abrir em Nova Aba
                            </a>
                        </div>
                    `;
                };

                // Timeout para mostrar erro se demorar muito
                setTimeout(() => {
                    if (iframe.style.opacity === '0') {
                        console.warn('[ChatManager] Iframe demorou para carregar');
                        loadingDiv.innerHTML = `
                            <div class="flex flex-col items-center text-white">
                                <svg class="animate-spin -ml-1 mr-3 h-8 w-8 text-white" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <p class="text-sm text-gray-300 mt-2">Carregando... Isso pode levar alguns segundos</p>
                                <a href="${artifactUrl}" target="_blank" class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                                    Abrir em Nova Aba
                                </a>
                            </div>
                        `;
                    }
                }, 5000);
            }

        } else if (tabType === 'code') {
            const escapedUrl = artifactUrl.replace(/'/g, "\\'");
            modalContent.innerHTML = `
                <div class="w-full h-full bg-gray-900 rounded-lg overflow-hidden">
                    <div class="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700">
                        <h4 class="text-white font-medium">Código Fonte</h4>
                        <button onclick="window.ChatManager.copyArtifactCode('${escapedUrl}')" class="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                            </svg>
                            Copiar
                        </button>
                    </div>
                    <div id="code-content" class="p-4 overflow-auto h-full">
                        <div class="flex items-center justify-center h-32">
                            <svg class="animate-spin h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span class="ml-2 text-gray-400">Carregando código...</span>
                        </div>
                    </div>
                </div>
            `;

            // Carregar código fonte
            this.loadArtifactCode(artifactUrl);
        }
    }

    async loadArtifactCode(artifactUrl) {
        try {
            const response = await fetch(artifactUrl);
            const code = await response.text();
            
            const codeContent = document.getElementById('code-content');
            if (codeContent) {
                codeContent.innerHTML = `
                    <pre class="language-html"><code class="language-html" style="color: #e2e8f0; background: transparent; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 14px; line-height: 1.5;">${this.escapeHtml(code)}</code></pre>
                `;
                
                // Aplicar syntax highlighting se disponível
                if (window.Prism) {
                    window.Prism.highlightAll();
                }
            }
        } catch (error) {
            console.error('Erro ao carregar código:', error);
            const codeContent = document.getElementById('code-content');
            if (codeContent) {
                codeContent.innerHTML = `
                    <div class="text-red-400 text-center p-8">
                        <p>Erro ao carregar código fonte</p>
                        <p class="text-sm text-gray-500 mt-2">${error.message}</p>
                    </div>
                `;
            }
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async copyArtifactCode(artifactUrl) {
        try {
            const response = await fetch(artifactUrl);
            const code = await response.text();
            
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(code);
                this.showNotification('Código copiado para a área de transferência!', 'success');
            } else {
                // Fallback
                const textArea = document.createElement('textarea');
                textArea.value = code;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showNotification('Código copiado!', 'success');
            }
        } catch (error) {
            console.error('Erro ao copiar código:', error);
            this.showNotification('Erro ao copiar código', 'error');
        }
    }

    viewArtifactCode(artifactUrl, title) {
        this.openArtifactModal('code-view', artifactUrl, title);
        // Aguardar modal abrir e então trocar para aba de código
        setTimeout(() => {
            this.switchArtifactTab('code', artifactUrl, null);
            
            // Atualizar abas visuais manualmente
            const modal = document.getElementById('artifact-viewer-modal');
            const tabs = modal.querySelectorAll('.tab-button');
            tabs.forEach((tab, index) => {
                tab.classList.toggle('active', index === 1); // Segunda aba (código)
            });
        }, 100);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-white transform transition-all duration-300 ${
            type === 'success' ? 'bg-green-600' : 
            type === 'error' ? 'bg-red-600' : 'bg-blue-600'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animar entrada
        setTimeout(() => notification.style.transform = 'translateX(0)', 10);
        
        // Remover após 3 segundos
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    createArtifactModal() {
        const modal = document.createElement('div');
        modal.id = 'artifact-viewer-modal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-75 z-50 hidden items-center justify-center p-4';

        modal.innerHTML = `
            <div class="bg-gray-900 rounded-xl shadow-2xl w-full max-w-6xl max-h-full flex flex-col border border-gray-700">
                <div class="flex justify-between items-center p-4 border-b border-gray-700">
                    <h3 id="artifact-modal-title" class="text-xl font-semibold text-white">Visualização de Artefato</h3>
                    <button id="artifact-modal-close" class="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-800">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div id="artifact-modal-tabs" class="flex border-b border-gray-700 px-4">
                    <!-- Tabs will be added here -->
                </div>
                <div id="artifact-modal-content" class="flex-1 p-4 overflow-hidden">
                    <!-- Content will be loaded here -->
                </div>
            </div>
        `;

        // Adicionar CSS para as abas
        const style = document.createElement('style');
        style.textContent = `
            .tab-button {
                display: flex;
                align-items: center;
                padding: 12px 16px;
                background: transparent;
                border: none;
                color: #9ca3af;
                cursor: pointer;
                border-bottom: 2px solid transparent;
                transition: all 0.3s ease;
                font-weight: 500;
            }
            .tab-button:hover {
                color: #e5e7eb;
                background: rgba(255, 255, 255, 0.05);
            }
            .tab-button.active {
                color: #60a5fa;
                border-bottom-color: #60a5fa;
                background: rgba(96, 165, 250, 0.1);
            }
            #artifact-modal-content {
                height: calc(70vh - 120px);
                min-height: 400px;
            }
            #artifact-viewer-modal iframe {
                border: none;
                background: white;
                border-radius: 8px;
            }
        `;
        document.head.appendChild(style);

        return modal;
    }

    closeArtifactModal() {
        const modal = document.getElementById('artifact-viewer-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = 'auto'; // Restaurar scroll da página
            
            // Limpar conteúdo do iframe para parar execução
            const content = modal.querySelector('#artifact-modal-content');
            if (content) {
                content.innerHTML = '';
            }
        }
    }

    openFileInProject(filePath) {
        console.log('[ChatManager] Opening file in project view:', filePath);
        
        // Extrair nome do arquivo
        const fileName = filePath.split('/').pop() || filePath;
        
        // Abrir arquivo em iframe usando o ModalManager
        if (window.ModalManager && window.ModalManager.openFileViewer) {
            window.ModalManager.openFileViewer(filePath, fileName);
        }
        
        // Mostrar notificação
        this.showNotification(`Arquivo ${fileName} aberto para visualização`, 'success');
    }

    highlightFileInExplorer(filePath) {
        // Procurar pelo arquivo no explorador de projetos
        const fileItems = document.querySelectorAll('.project-file');
        fileItems.forEach(item => {
            const itemPath = item.dataset.path;
            if (itemPath && itemPath.includes(filePath)) {
                // Destacar o arquivo
                item.classList.add('bg-blue-100', 'border-blue-300');
                item.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Remover destaque após alguns segundos
                setTimeout(() => {
                    item.classList.remove('bg-blue-100', 'border-blue-300');
                }, 3000);
            }
        });
    }

    handleError(error) {
        console.error('[ChatManager] Chat error:', error);

        const errorMessage = this.createMessageElement('ai', 
            `[ERROR] ${error.message || 'Something went wrong. Please try again.'}`
        );
        errorMessage.classList.add('error-message');

        this.appendMessage(errorMessage);
        this.hideThinking();
    }

    scrollToBottom() {
        if (this.chatMessages) {
            requestAnimationFrame(() => {
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            });
        }
    }

    // Método para limpeza
    cleanup() {
        if (this.currentEventSource) {
            this.currentEventSource.close();
            this.currentEventSource = null;
        }
        this.isProcessing = false;
    }

    // Métodos públicos para compatibilidade
    static getInstance() {
        if (!window._chatManagerInstance) {
            window._chatManagerInstance = new ChatManager();
        }
        return window._chatManagerInstance;
    }
}

// Inicialização automática quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    console.log('[System] DOM loaded, initializing ChatManager...');

    // Criar instância global
    window.ChatManager = ChatManager.getInstance();

    // Tentar inicializar
    const success = window.ChatManager.init();

    if (success) {
        console.log('[System] ChatManager ready for use');
    } else {
        console.error('[System] ChatManager initialization failed');
    }
});

// Cleanup quando página for descarregada
window.addEventListener('beforeunload', function() {
    if (window.ChatManager) {
        window.ChatManager.cleanup();
    }
});

// Tornar funções acessíveis globalmente para compatibilidade
window.openArtifactModal = function(artifactId, artifactUrl, title) {
    if (window.ChatManager) {
        window.ChatManager.openArtifactModal(artifactId, artifactUrl, title);
    }
};

window.closeArtifactModal = function() {
    if (window.ChatManager) {
        window.ChatManager.closeArtifactModal();
    }
};

console.log('[System] chat.js loaded successfully');