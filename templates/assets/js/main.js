// CodeR Chat Interface v2.0 - Main JavaScript

// Global initialization - with enhanced debugging
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando sistema CodeR...');

    try {
        // Debug available systems
        console.log('🔍 Sistemas disponíveis:', {
            InputManager: typeof InputManager,
            ChatManager: typeof window.ChatManager,
            ProjectSystem: typeof ProjectSystem,
            StatusManager: typeof StatusManager
        });

        // Initialize core systems
        if (typeof InputManager !== 'undefined') {
            InputManager.init();
            console.log('✅ InputManager inicializado');
        } else {
            console.warn('⚠️ InputManager não disponível');
        }

        // Initialize chat system
        if (window.ChatManager && typeof window.ChatManager.init === 'function') {
            window.ChatManager.init();
            console.log('✅ ChatManager inicializado com sucesso');

            // Test sendMessage function
            if (typeof window.ChatManager.sendMessage === 'function') {
                console.log('✅ ChatManager.sendMessage disponível');
            } else {
                console.error('❌ ChatManager.sendMessage não é uma função');
            }
        } else {
            console.error('❌ ChatManager não encontrado ou não é uma função válida');
            console.log('Debug ChatManager:', window.ChatManager);
        }

        if (typeof ProjectSystem !== 'undefined') {
            ProjectSystem.init();
            console.log('✅ ProjectSystem inicializado');
        }

        if (typeof StatusManager !== 'undefined') {
            StatusManager.updateStatus('online', 'Online');
            console.log('✅ StatusManager inicializado');
        }

        console.log('🎯 Inicialização concluída com sucesso');

    } catch (error) {
        console.error('❌ Erro na inicialização:', error);
        if (typeof StatusManager !== 'undefined') {
            StatusManager.updateStatus('offline', 'Erro de inicialização');
        }
    }

    // Aguardar um pouco para garantir que todos os scripts carregaram
        setTimeout(() => {
            console.log('ChatManager status:', typeof window.ChatManager);
            if (!window.ChatManager) {
                console.error('❌ ChatManager não carregado');
                // Não forçar reload para evitar loops
                console.log('💡 Dica: Verifique se chat.js carregou corretamente');
            } else {
                console.log('✅ ChatManager carregado com sucesso');
            }
        }, 500);
});

class CoderInterface {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.initializeProjects();
        this.setupChat();
    }

    initializeElements() {
        // Menu elements
        this.sideMenu = document.getElementById('sideMenu');
        this.overlay = document.getElementById('overlay');
        this.menuToggle = document.getElementById('menuToggle');
        this.headerTitleContainer = document.getElementById('headerTitleContainer');

        // Project elements
        this.addProjectBtn = document.getElementById('addProjectBtn');
        this.projectList = document.getElementById('projectList');
        this.addProjectModal = document.getElementById('addProjectModal');
        this.closeAddProjectModalBtn = document.getElementById('closeAddProjectModalBtn');
        this.newProjectNameInput = document.getElementById('newProjectNameInput');
        this.createProjectBtn = document.getElementById('createProjectBtn');
        this.modalTitle = document.getElementById('modalTitle');
        this.contextMenu = document.getElementById('contextMenu');
        this.addFolderBtn = document.getElementById('addFolderBtn');
        this.addFileBtn = document.getElementById('addFileBtn');

        // Tab system elements
        this.chatContent = document.getElementById('chatContent');
        this.editorContainer = document.getElementById('editorContainer');
        this.tabContainer = document.getElementById('tabContainer');

        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.welcomeMessage = document.getElementById('welcomeMessage');
        this.loadingIndicator = document.getElementById('loadingIndicator');

        // Profile elements
        this.userAvatarBtn = document.getElementById('userAvatar');
        this.profileModal = document.getElementById('profileModal');
        this.closeProfileModalBtn = document.getElementById('closeProfileModalBtn');

        // State
        this.currentParentFolder = null;
        this.itemTypeToCreate = null;
        this.openedFiles = new Set();
        this.activeTab = null;
    }

    setupEventListeners() {
        // Menu toggle
        if (this.menuToggle) {
            this.menuToggle.addEventListener('click', () => this.toggleMenu());
        }
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.toggleMenu());
        }

        // Project management
        if (this.addProjectBtn) {
            this.addProjectBtn.addEventListener('click', () => this.openAddProjectModal());
        }
        if (this.closeAddProjectModalBtn) {
            this.closeAddProjectModalBtn.addEventListener('click', () => this.closeAddProjectModal());
        }
        if (this.createProjectBtn) {
            this.createProjectBtn.addEventListener('click', () => this.createProject());
        }

        // Context menu
        document.addEventListener('click', (e) => this.handleContextMenuClose(e));
        if (this.projectList) {
            this.projectList.addEventListener('contextmenu', (e) => this.handleContextMenu(e));
            this.projectList.addEventListener('click', (e) => this.handleProjectClick(e));
        }
        if (this.addFolderBtn) {
            this.addFolderBtn.addEventListener('click', () => this.addFolder());
        }
        if (this.addFileBtn) {
            this.addFileBtn.addEventListener('click', () => this.addFile());
        }

        // Profile modal
        if (this.userAvatarBtn) {
            this.userAvatarBtn.addEventListener('click', () => this.openProfileModal());
        }
        if (this.closeProfileModalBtn) {
            this.closeProfileModalBtn.addEventListener('click', () => this.closeProfileModal());
        }

        // Chat form
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => this.handleMessageSubmit(e));
        }
    }

    toggleMenu() {
        const isOpen = !this.sideMenu.classList.contains('-translate-x-full');

        if (isOpen) {
            // Close menu
            this.sideMenu.classList.add('-translate-x-full');
            this.overlay.classList.add('hidden');
        } else {
            // Open menu
            this.sideMenu.classList.remove('-translate-x-full');
            this.overlay.classList.remove('hidden');
        }
    }

    openAddProjectModal() {
        this.currentParentFolder = null;
        this.itemTypeToCreate = 'folder';
        this.modalTitle.textContent = 'Create New Project';
        this.newProjectNameInput.placeholder = 'Project Name';
        this.addProjectModal.classList.remove('hidden');
    }

    closeAddProjectModal() {
        this.addProjectModal.classList.add('hidden');
        this.newProjectNameInput.value = '';
    }

    handleContextMenuClose(e) {
        if (!this.contextMenu.contains(e.target) && this.contextMenu.style.display === 'block') {
            this.contextMenu.style.display = 'none';
        }
    }

    handleContextMenu(e) {
        const folderItem = e.target.closest('[data-type="folder"]');
        if (folderItem) {
            e.preventDefault();
            this.currentParentFolder = folderItem;
            this.contextMenu.style.display = 'block';
            this.contextMenu.style.left = `${e.clientX}px`;
            this.contextMenu.style.top = `${e.clientY}px`;
        }
    }

    addFolder() {
        this.itemTypeToCreate = 'folder';
        this.modalTitle.textContent = 'Create New Folder';
        this.newProjectNameInput.placeholder = 'Folder Name';
        this.addProjectModal.classList.remove('hidden');
        this.contextMenu.style.display = 'none';
    }

    addFile() {
        this.itemTypeToCreate = 'file';
        this.modalTitle.textContent = 'Create New File';
        this.newProjectNameInput.placeholder = 'File Name';
        this.addProjectModal.classList.remove('hidden');
        this.contextMenu.style.display = 'none';
    }

    getFileIconHtml(fileName) {
        const extension = fileName.split('.').pop().toLowerCase();
        switch (extension) {
            case 'html':
            case 'htm':
                return '<i class="fas fa-file-code icon-html mr-2"></i>';
            case 'css':
                return '<i class="fab fa-css3-alt icon-css mr-2"></i>';
            case 'js':
            case 'jsx':
                return '<i class="fab fa-js-square icon-js mr-2"></i>';
            case 'ts':
            case 'tsx':
                return '<i class="fab fa-react icon-ts mr-2"></i>';
            case 'json':
                return '<i class="fas fa-file-code icon-json mr-2"></i>';
            case 'py':
                return '<i class="fab fa-python icon-py mr-2"></i>';
            case 'java':
                return '<i class="fab fa-java icon-java mr-2"></i>';
            case 'cpp':
            case 'cxx':
            case 'cc':
            case 'c':
                return '<i class="fas fa-file-code icon-cpp mr-2"></i>';
            case 'cs':
                return '<i class="fas fa-file-code icon-csharp mr-2"></i>';
            case 'md':
            case 'txt':
                return '<i class="fas fa-file-alt icon-md mr-2"></i>';
            default:
                return '<i class="fas fa-file icon-file mr-2"></i>';
        }
    }

    handleMessageSubmit(e) {
        e.preventDefault();
        console.log('📝 Formulário submetido');

        if (window.ChatManager && typeof window.ChatManager.sendMessage === 'function') {
            console.log('✅ Chamando ChatManager.sendMessage()');
            window.ChatManager.sendMessage();
        } else {
            console.error('❌ ChatManager.sendMessage não encontrado');
            console.log('Disponível:', {
                ChatManager: typeof window.ChatManager,
                sendMessage: window.ChatManager ? typeof window.ChatManager.sendMessage : 'undefined'
            });
        }
    }

    async initializeProjects() {
        console.log('📁 Loading real projects from workspace...');
        try {
            await this.loadRealProjects();
        } catch (error) {
            console.error('❌ Error loading projects:', error);
        }
    }

    async loadRealProjects() {
        try {
            const response = await fetch('/api/projects/tree');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                console.log(`✅ Workspace loaded: ${data.workspace_label} (${data.total_items} items)`);
                this.renderProjectTree(data.projects);
                this.updateWorkspaceInfo(data);
            } else {
                console.error('❌ Error loading projects:', data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('❌ Error loading projects:', error);
        }
    }

    renderProjectTree(projects) {
        // Clear current list
        this.projectList.innerHTML = '';

        if (projects.length === 0) {
            const emptyMessage = document.createElement('li');
            emptyMessage.className = 'text-gray-500 text-sm italic p-2';
            emptyMessage.textContent = 'No projects found. Create your first project!';
            this.projectList.appendChild(emptyMessage);
            return;
        }

        // Render each item
        projects.forEach(project => {
            const item = this.createProjectItem(project);
            this.projectList.appendChild(item);
        });
    }

    createProjectItem(project) {
        const li = document.createElement('li');
        li.className = 'project-item';
        li.dataset.type = project.type;
        li.dataset.path = project.path;

        const mainContent = document.createElement('div');
        mainContent.className = 'main-content flex items-center px-3 py-2 hover:bg-gray-700 cursor-pointer transition-colors';

        if (project.type === 'folder') {
            li.classList.add('animate-folder-toggle');
            const arrow = document.createElement('span');
            arrow.className = 'toggle-arrow text-gray-400 mr-2';
            arrow.textContent = '▶';
            mainContent.appendChild(arrow);
        }

        const icon = document.createElement('span');
        icon.className = 'mr-2';
        if (project.type === 'folder') {
            icon.innerHTML = '<i class="fas fa-folder icon-folder"></i>';
        } else {
            icon.innerHTML = this.getFileIconHtml(project.name);
        }
        mainContent.appendChild(icon);

        const name = document.createElement('span');
        name.textContent = project.name;
        name.className = 'text-gray-200';
        mainContent.appendChild(name);

        li.appendChild(mainContent);

        // Add children if folder
        if (project.type === 'folder' && project.children && project.children.length > 0) {
            const childList = document.createElement('ul');
            childList.className = 'hidden-initial';
            project.children.forEach(child => {
                const childItem = this.createProjectItem(child);
                childList.appendChild(childItem);
            });
            li.appendChild(childList);
        }

        return li;
    }

    updateWorkspaceInfo(data) {
        // Update header or status as needed
        console.log(`📂 Workspace: ${data.workspace_label} with ${data.total_items} items`);
    }

    setupChat() {
        // Chat setup is handled by ChatManager
        console.log('🚀 CodeR Chat Interface Loading...');
        console.log('🔍 System checks completed');
        console.log('📋 All systems initialized');
        console.log('✅ CodeR System ready');
    }

    handleProjectClick(e) {
        e.preventDefault();

        const item = e.target.closest('li[data-type]');
        if (!item) return;

        const itemType = item.dataset.type;
        const itemPath = item.dataset.path;

        if (itemType === 'folder') {
            // Toggle folder expansion
            this.toggleFolder(item);
        } else if (itemType === 'file') {
            // Open file
            this.openFile(itemPath, item);
        }
    }

    toggleFolder(folderItem) {
        const childList = folderItem.querySelector('ul');
        const arrow = folderItem.querySelector('.toggle-arrow');

        if (childList) {
            const isExpanded = folderItem.classList.contains('expanded');

            if (isExpanded) {
                // Collapse folder
                folderItem.classList.remove('expanded');
                childList.classList.add('hidden-initial');
                if (arrow) arrow.textContent = '▶';
            } else {
                // Expand folder
                folderItem.classList.add('expanded');
                childList.classList.remove('hidden-initial');
                if (arrow) arrow.textContent = '▼';
            }
        }
    }

    async openFile(filePath, fileItem) {
        if (!filePath) return;

        try {
            // Add visual feedback
            fileItem.classList.add('clicking-file');
            setTimeout(() => fileItem.classList.remove('clicking-file'), 200);

            // Show loading state
            StatusManager.updateStatus('loading', `Abrindo ${filePath}...`);

            // Fetch file content
            const response = await fetch(`/api/projects/file?path=${encodeURIComponent(filePath)}`);

            if (!response.ok) {
                throw new Error(`Erro ao carregar arquivo: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.displayFileContent(result.path, result.content, filePath);
                StatusManager.updateStatus('online', 'Arquivo carregado');
            } else {
                throw new Error(result.error || 'Erro desconhecido');
            }

        } catch (error) {
            console.error('Erro ao abrir arquivo:', error);
            NotificationManager.error(`Erro ao abrir arquivo: ${error.message}`);
            StatusManager.updateStatus('online', 'Erro ao carregar arquivo');
        }
    }

    displayFileContent(filePath, content, originalPath) {
        // Hide chat content and show editor
        this.chatContent.classList.add('hidden');
        this.editorContainer.classList.remove('hidden');
        this.tabContainer.classList.remove('hidden');

        // Create or update tab
        const tabId = this.createFileTab(filePath, originalPath);

        // Create file editor iframe
        this.createFileEditor(tabId, filePath, content);

        // Set as active tab
        this.setActiveTab(tabId);
    }

    createFileTab(filePath, originalPath) {
        const fileName = filePath.split('/').pop();
        const tabId = `tab-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // Check if tab already exists
        const existingTab = Array.from(this.tabContainer.children).find(tab => 
            tab.dataset.filePath === filePath
        );

        if (existingTab) {
            this.setActiveTab(existingTab.id);
            return existingTab.id;
        }

        // Create new tab
        const tab = document.createElement('div');
        tab.id = tabId;
        tab.className = 'tab';
        tab.dataset.filePath = filePath;
        tab.dataset.originalPath = originalPath;

        tab.innerHTML = `
            <span class="tab-icon">${this.getFileIconText(fileName)}</span>
            <span class="tab-name">${fileName}</span>
            <button class="tab-close-btn" onclick="window.coderInterface.closeTab('${tabId}')">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Add click handler to tab
        tab.addEventListener('click', (e) => {
            if (!e.target.classList.contains('tab-close-btn')) {
                this.setActiveTab(tabId);
            }
        });

        this.tabContainer.appendChild(tab);
        return tabId;
    }

    createFileEditor(tabId, filePath, content) {
        const editorFrame = document.createElement('iframe');
        editorFrame.id = `editor-${tabId}`;
        editorFrame.className = 'editor-frame hidden';
        editorFrame.style.width = '100%';
        editorFrame.style.height = '100%';
        editorFrame.style.border = 'none';

        // Create simple code editor HTML
        const editorHTML = this.createEditorHTML(content, filePath);
        editorFrame.srcdoc = editorHTML;

        this.editorContainer.appendChild(editorFrame);
    }

    createEditorHTML(content, filePath) {
        const fileName = filePath.split('/').pop();
        const fileExtension = fileName.split('.').pop().toLowerCase();

        return `
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${fileName}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
            line-height: 1.6;
        }
        .editor-header {
            background: #2d2d2d;
            padding: 10px 15px;
            border-radius: 8px 8px 0 0;
            border-bottom: 1px solid #404040;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .file-info {
            font-size: 14px;
            color: #888;
        }
        .editor-content {
            background: #1e1e1e;
            border: 1px solid #404040;
            border-radius: 0 0 8px 8px;
            min-height: 500px;
        }
        .code-editor {
            width: 100%;
            height: 500px;
            background: transparent;
            border: none;
            color: #e0e0e0;
            font-family: inherit;
            font-size: 14px;
            padding: 15px;
            resize: vertical;
            outline: none;
        }
        .code-display {
            padding: 15px;
            white-space: pre-wrap;
            font-size: 14px;
            overflow: auto;
            max-height: 500px;
        }
        .line-numbers {
            background: #2d2d2d;
            padding: 15px 10px;
            border-right: 1px solid #404040;
            color: #666;
            font-size: 14px;
            user-select: none;
            min-width: 50px;
            text-align: right;
        }
        .editor-main {
            display: flex;
            background: #1e1e1e;
            border-radius: 0 0 8px 8px;
        }
        .actions {
            display: flex;
            gap: 10px;
        }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .btn:hover { background: #45a049; }
        .btn.secondary { background: #666; }
        .btn.secondary:hover { background: #555; }
    </style>
</head>
<body>
    <div class="editor-header">
        <div class="file-info">
            <strong>${fileName}</strong> • ${fileExtension.toUpperCase()} • ${content.length} caracteres
        </div>
        <div class="actions">
            <button class="btn secondary" onclick="copyContent()">Copiar</button>
            <button class="btn" onclick="saveFile()">Salvar</button>
        </div>
    </div>

    <div class="editor-main">
        <div class="line-numbers" id="lineNumbers"></div>
        <div class="editor-content">
            <textarea class="code-editor" id="codeEditor" spellcheck="false">${this.escapeHtml(content)}</textarea>
        </div>
    </div>

    <script>
        const editor = document.getElementById('codeEditor');
        const lineNumbers = document.getElementById('lineNumbers');

        function updateLineNumbers() {
            const lines = editor.value.split('\\n');
            const numbers = lines.map((_, i) => i + 1).join('\\n');
            lineNumbers.textContent = numbers;
        }

        function copyContent() {
            navigator.clipboard.writeText(editor.value).then(() => {
                alert('Conteúdo copiado!');
            });
        }

        function saveFile() {
            // TODO: Implement save functionality
            alert('Funcionalidade de salvamento será implementada em breve');
        }

        editor.addEventListener('input', updateLineNumbers);
        editor.addEventListener('scroll', () => {
            lineNumbers.scrollTop = editor.scrollTop;
        });

        // Initial line numbers
        updateLineNumbers();
    </script>
</body>
</html>`;
    }

    setActiveTab(tabId) {
        // Remove active class from all tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });

        // Hide all editor frames
        document.querySelectorAll('.editor-frame').forEach(frame => {
            frame.classList.add('hidden');
        });

        // Set active tab
        const activeTab = document.getElementById(tabId);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Show corresponding editor frame
        const editorFrame = document.getElementById(`editor-${tabId}`);
        if (editorFrame) {
            editorFrame.classList.remove('hidden');
        }

        this.activeTab = tabId;
    }

    closeTab(tabId) {
        const tab = document.getElementById(tabId);
        const editorFrame = document.getElementById(`editor-${tabId}`);

        if (tab) tab.remove();
        if (editorFrame) editorFrame.remove();

        // If this was the active tab, switch to another or show chat
        if (this.activeTab === tabId) {
            const remainingTabs = document.querySelectorAll('.tab');
            if (remainingTabs.length > 0) {
                this.setActiveTab(remainingTabs[0].id);
            } else {
                // No more tabs, show chat
                this.editorContainer.classList.add('hidden');
                this.tabContainer.classList.add('hidden');
                this.chatContent.classList.remove('hidden');
                this.activeTab = null;
            }
        }
    }

    getFileIconText(fileName) {
        const extension = fileName.split('.').pop().toLowerCase();
        const iconMap = {
            'js': '📜', 'ts': '🔷', 'py': '🐍', 'html': '🌐', 'css': '🎨',
            'json': '📋', 'md': '📝', 'txt': '📄', 'yml': '⚙️', 'yaml': '⚙️'
        };
        return iconMap[extension] || '📄';
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize the interface when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof CoderInterface !== 'undefined') {
        window.coderInterface = new CoderInterface();
    }
});

// Global functions for backward compatibility
window.logout = async () => {
    try {
        const response = await fetch('/api/auth/logout', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });

        // Always redirect to login, even if there's an API error
        if (response.ok) {
            const result = await response.json();
            console.log('Logout successful:', result);
        } else {
            console.warn('Logout API error, but redirecting anyway');
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Continue with logout even with error
    }

    // Clear local data
    try {
        localStorage.clear();
        sessionStorage.clear();
    } catch (e) {
        console.warn('Error clearing storage:', e);
    }

    // Always redirect
    window.location.replace('/login');
};

window.attachFile = () => {
    if (window.FileManager) {
        window.FileManager.attachFile();
    }
};

window.closeArtifactModal = () => {
    if (window.ModalManager) {
        window.ModalManager.closeArtifactModal();
    }
};

console.log('🎯 CodeR v2.0.0 - Modular Interface Ready');