// Sistema de Markdown Profissional - Estilo Code/Terminal
window.renderMarkdown = function(text) {
    if (!text) return '';

    let processed = text.toString().trim();

    // Escape HTML para segurança
    const escapeHtml = (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };

    // Processar blocos de código primeiro (mais específico)
    processed = processed.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, lang, code) {
        const language = lang || 'code';
        const cleanCode = escapeHtml(code.trim());
        return `
            <div class="code-block bg-gray-900 border border-gray-700 rounded-lg overflow-hidden my-4">
                <div class="code-header bg-gray-800 px-4 py-2 text-xs text-gray-300 font-mono border-b border-gray-700 flex justify-between items-center">
                    <span class="language-label">${language.toUpperCase()}</span>
                    <button onclick="navigator.clipboard?.writeText(\`${cleanCode.replace(/`/g, '\\`')}\`)" class="copy-btn text-gray-400 hover:text-white transition-colors">
                        Copy
                    </button>
                </div>
                <pre class="p-4 overflow-x-auto"><code class="text-gray-100 text-sm font-mono leading-relaxed">${cleanCode}</code></pre>
            </div>
        `;
    });

    // Comandos inline (estilo terminal)
    processed = processed.replace(/`([^`]+)`/g, '<code class="inline-code bg-gray-800 text-gray-100 px-2 py-1 rounded font-mono text-sm border border-gray-600">$1</code>');

    // Headers (estilo profissional)
    processed = processed.replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold text-white mt-6 mb-3 border-l-4 border-blue-500 pl-4">$1</h3>');
    processed = processed.replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold text-white mt-8 mb-4 border-l-4 border-green-500 pl-4">$1</h2>');
    processed = processed.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-white mt-8 mb-6 border-b border-gray-600 pb-2">$1</h1>');

    // Texto formatado
    processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
    processed = processed.replace(/\*(.*?)\*/g, '<em class="text-gray-300 italic">$1</em>');

    // Links (estilo profissional)
    processed = processed.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-400 hover:text-blue-300 underline transition-colors">$1</a>');

    // Listas (estilo clean)
    processed = processed.replace(/^[\*\-\+] (.*$)/gm, '<li class="text-gray-200 mb-2 pl-4 relative"><span class="absolute left-0 text-blue-400 font-mono">></span>$1</li>');
    processed = processed.replace(/^\d+\. (.*$)/gm, '<li class="text-gray-200 mb-2 pl-6 relative list-decimal">$1</li>');

    // Wrap listas em containers
    processed = processed.replace(/(<li[^>]*>.*<\/li>(\s*<li[^>]*>.*<\/li>)*)/g, '<ul class="list-none space-y-1 my-4">$1</ul>');

    // Blockquotes (estilo terminal)
    processed = processed.replace(/^> (.*$)/gm, '<blockquote class="border-l-4 border-yellow-500 pl-4 py-2 bg-gray-800 text-gray-300 italic my-4">$1</blockquote>');

    // Separadores
    processed = processed.replace(/^---$/gm, '<hr class="border-gray-600 my-6">');

    // Quebras de linha e parágrafos
    processed = processed.replace(/\n\n/g, '</p><p class="mb-4 text-gray-200 leading-relaxed">');
    processed = processed.replace(/\n/g, '<br>');

    // Envolver em parágrafo se necessário
    if (!processed.includes('<h') && !processed.includes('<div') && !processed.includes('<ul') && !processed.includes('<blockquote')) {
        processed = `<p class="mb-4 text-gray-200 leading-relaxed">${processed}</p>`;
    }

    return processed;
};

// Função para processamento específico de comandos/código
window.formatCodeCommand = function(text) {
    return `<div class="command-block bg-gray-900 border-l-4 border-green-500 p-3 my-2 font-mono text-sm">
        <span class="text-green-400">$</span> <span class="text-gray-100">${text}</span>
    </div>`;
};

// Função para resultados de execução
window.formatExecutionResult = function(text, success = true) {
    const borderColor = success ? 'border-green-500' : 'border-red-500';
    const textColor = success ? 'text-green-300' : 'text-red-300';

    return `<div class="execution-result bg-gray-900 border-l-4 ${borderColor} p-3 my-2 font-mono text-sm">
        <div class="${textColor}">${text}</div>
    </div>`;
};

console.log('[System] Professional markdown renderer loaded');