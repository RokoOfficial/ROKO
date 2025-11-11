/* CodeR Utility Functions */

/**
 * Utility functions for CodeR interface
 */

// Safe element selection
function getElementById(id) {
    return document.getElementById(id);
}

// Safe event listener addition
function addEventListenerSafe(element, event, handler) {
    if (element && typeof handler === 'function') {
        element.addEventListener(event, handler);
    }
}

// Generate unique IDs
function generateId(prefix = 'id') {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Debounce function
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

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// HTML escaping
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format time
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// Storage wrapper - check if already declared to avoid conflicts
if (typeof window.storage === 'undefined') {
    window.storage = {
        get(key) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : null;
            } catch (error) {
                console.warn('Storage get error:', error);
                return null;
            }
        },

        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (error) {
                console.warn('Storage set error:', error);
            }
        },

        remove(key) {
            try {
                localStorage.removeItem(key);
            } catch (error) {
                console.warn('Storage remove error:', error);
            }
        }
    };
}

// Message formatting
function formatMessage(message) {
    if (!message) return '';
    return escapeHtml(message).replace(/\n/g, '<br>');
}

// Render assistant message with full markdown support
function renderAssistantMessage(content) {
    if (!content) return '';

    // Usar sistema de markdown profissional
    if (window.renderMarkdown && typeof window.renderMarkdown === 'function') {
        try {
            return window.renderMarkdown(content);
        } catch (error) {
            console.warn('Erro no renderMarkdown:', error);
        }
    }

    // Fallback básico sem emojis
    const escapeHtml = (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };

    let processed = escapeHtml(content);

    // Formatações básicas
    processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
    processed = processed.replace(/\*(.*?)\*/g, '<em class="text-gray-300">$1</em>');
    processed = processed.replace(/`([^`]+)`/g, '<code class="bg-gray-800 text-gray-100 px-2 py-1 rounded text-sm font-mono">$1</code>');
    processed = processed.replace(/\n/g, '<br>');

    return `<div class="text-gray-200 leading-relaxed">${processed}</div>`;
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        if (navigator.clipboard) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            return true;
        }
    } catch (error) {
        console.error('Copy to clipboard failed:', error);
        return false;
    }
}

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Scroll element into view smoothly
function scrollIntoView(element, behavior = 'smooth') {
    if (element && element.scrollIntoView) {
        element.scrollIntoView({ behavior, block: 'nearest' });
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Validate email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Get file extension
function getFileExtension(filename) {
    return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
}

// Random ID generator
function randomId() {
    return Math.random().toString(36).substr(2, 9);
}

// Deep clone object
function deepClone(obj) {
    try {
        return JSON.parse(JSON.stringify(obj));
    } catch (error) {
        console.warn('Deep clone failed:', error);
        return obj;
    }
}

// Check if object is empty
function isEmpty(obj) {
    if (obj == null) return true;
    if (Array.isArray(obj) || typeof obj === 'string') return obj.length === 0;
    return Object.keys(obj).length === 0;
}

// Wait for element to exist
function waitForElement(selector, timeout = 5000) {
    return new Promise((resolve, reject) => {
        const element = document.querySelector(selector);
        if (element) {
            resolve(element);
            return;
        }

        const observer = new MutationObserver((mutations, obs) => {
            const element = document.querySelector(selector);
            if (element) {
                obs.disconnect();
                resolve(element);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        setTimeout(() => {
            observer.disconnect();
            reject(new Error(`Element ${selector} not found within ${timeout}ms`));
        }, timeout);
    });
}

// Export all utilities to window for global access
window.utils = {
    getElementById,
    addEventListenerSafe,
    generateId,
    debounce,
    throttle,
    escapeHtml,
    formatTime,
    storage,
    formatMessage,
    renderAssistantMessage,
    copyToClipboard,
    isInViewport,
    scrollIntoView,
    formatFileSize,
    isValidEmail,
    getFileExtension,
    randomId,
    deepClone,
    isEmpty,
    waitForElement
};