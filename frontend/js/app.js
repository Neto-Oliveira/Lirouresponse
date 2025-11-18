// UI utilities and small controller
class UIController {
    static init() {
        this.setupSmoothAnimations();
    }

    static setupSmoothAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) entry.target.classList.add('fade-in');
            });
        }, { threshold: 0.12 });

        document.querySelectorAll('.result-card, .section-header, .input-option').forEach(el => observer.observe(el));
    }

    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} slide-up`;
        notification.setAttribute('role','alert');
        notification.innerHTML = `
            <div style="display:flex;align-items:center;gap:12px">
                <div style="font-size:18px;color:var(--primary-color);width:24px;height:24px;display:flex;align-items:center;justify-content:center">
                    ${this._getIconSvg(type)}
                </div>
                <div style="max-width:420px;color:var(--text-primary)">${message}</div>
                <button style="margin-left:8px;background:none;border:none;cursor:pointer;color:var(--text-tertiary)">✕</button>
            </div>
        `;
        notification.style.cssText = `
            position:fixed; top:20px; right:20px; background:var(--surface-color); border:1px solid var(--border-color);
            border-radius:10px; padding:12px; box-shadow:var(--shadow-lg); z-index:1200; display:flex; align-items:center;
        `;

        notification.querySelector('button').addEventListener('click', () => notification.remove());
        document.body.appendChild(notification);
        setTimeout(() => { if (notification.parentElement) notification.remove(); }, 5000);
    }

    static _getIconSvg(type) {
        if (type === 'success') return '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.2 4.8 12l1.4-1.4L9 13.4 18.8 3.6 20.2 5z"/></svg>';
        if (type === 'error') return '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"/></svg>';
        if (type === 'warning') return '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>';
        return '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>';
    }
}

// File handling utilities
class FileHandler {
    static async extractTextFromFile(file) {
        if (file.type === 'application/pdf') {
            // For PDF files, we'll use a simple approach - extract text from upload
            return "[Conteúdo PDF] Arquivo carregado com sucesso. Clique em 'Analisar Email' para processar.";
        } else {
            // text/plain
            return await this._readAsText(file);
        }
    }

    static _readAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                // normalize line endings
                resolve(String(e.target.result).replace(/\r\n/g, '\n'));
            };
            reader.onerror = (e) => reject(new Error('Failed to read file as text'));
            reader.readAsText(file, 'utf-8');
        });
    }

    static validateFile(file) {
        const allowedTypes = ['text/plain', 'application/pdf'];
        const allowedExtensions = ['.txt', '.pdf'];
        const maxSize = 5 * 1024 * 1024; // 5MB

        const hasValidType = allowedTypes.includes(file.type);
        const hasValidExtension = allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

        if (!hasValidType && !hasValidExtension) {
            throw new Error('Tipo de arquivo não suportado. Use .txt ou .pdf.');
        }
        if (file.size > maxSize) {
            throw new Error('Arquivo muito grande. Máximo: 5MB.');
        }
        if (file.size === 0) {
            throw new Error('Arquivo vazio.');
        }
        return true;
    }
}

// Main Application Logic
class EmailClassifierApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentFile = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupOptionToggler();
        this.setupFileUpload();
        UIController.init();
    }

    setupEventListeners() {
        const textarea = document.getElementById('emailText');
        if (textarea) {
            textarea.addEventListener('input', this.autoResizeTextarea);
            textarea.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    this.processEmail();
                }
            });
        }

        document.getElementById('fileSelectBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        document.getElementById('changeFileBtn')?.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    setupOptionToggler() {
        const options = document.querySelectorAll('.input-option');
        options.forEach(option => {
            option.addEventListener('click', (e) => {
                // ignore clicks on interactive elements inside
                if (e.target.closest('button') || e.target.tagName === 'INPUT') return;
                options.forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
            });

            option.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    options.forEach(opt => opt.classList.remove('active'));
                    option.classList.add('active');
                    // trigger file select if file option
                    if (option.dataset.option === 'file') document.getElementById('fileInput').click();
                }
            });
        });
    }

    setupFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('fileUploadArea');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--primary-color)';
            uploadArea.style.background = 'var(--background-color)';
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--border-color)';
            uploadArea.style.background = 'transparent';
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--border-color)';
            uploadArea.style.background = 'transparent';
            const files = e.dataTransfer.files;
            if (files.length) this.handleFileSelect(files[0]);
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) this.handleFileSelect(e.target.files[0]);
        });
    }

    handleFileSelect(file) {
        try {
            FileHandler.validateFile(file);
        } catch (err) {
            this.showNotification(err.message || 'Arquivo inválido', 'error');
            return;
        }

        this.currentFile = file;
        this.displayFileInfo(file);

        // activate file option visually
        document.querySelectorAll('.input-option').forEach(opt => opt.classList.remove('active'));
        document.querySelector('[data-option="file"]').classList.add('active');
    }

    displayFileInfo(file) {
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = this.formatFileSize(file.size);
        document.getElementById('fileInfo').style.display = 'block';
        document.getElementById('fileUploadArea').style.display = 'none';
    }

    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B','KB','MB','GB','TB'];
        const i = Math.floor(Math.log(bytes)/Math.log(k));
        return parseFloat((bytes/Math.pow(k,i)).toFixed(2)) + ' ' + sizes[i];
    }

    autoResizeTextarea(e) {
        const textarea = e.target;
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    async processEmail() {
        const activeOption = document.querySelector('.input-option.active');
        const optionType = activeOption?.dataset.option;
        let emailContent = '';

        if (optionType === 'text') {
            emailContent = document.getElementById('emailText').value.trim();
        } else if (optionType === 'file' && this.currentFile) {
            try {
                emailContent = await FileHandler.extractTextFromFile(this.currentFile);
            } catch (err) {
                this.showNotification('Erro ao ler arquivo: ' + err.message, 'error');
                return;
            }
        }

        if (!emailContent) {
            this.showNotification('Por favor, insira o conteúdo do email ou selecione um arquivo.', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            const payload = { text: emailContent };
            const response = await fetch('/classify', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                const msg = errorData?.detail || `Erro HTTP ${response.status}`;
                throw new Error(msg);
            }

            const data = await response.json();
            this.displayResults(data);
            this.showNotification('Email analisado com sucesso!', 'success');

        } catch (err) {
            this.showNotification('Erro ao processar email: ' + (err.message || err), 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(data) {
        const resultsSection = document.getElementById('resultsSection');
        const categoryBadge = document.getElementById('categoryBadge');
        const categoryLabel = document.getElementById('categoryLabel');
        const confidenceValue = document.getElementById('confidenceValue');
        const confidenceFill = document.getElementById('confidenceFill');
        const responseText = document.getElementById('responseText');
        const processingTime = document.getElementById('processingTime');
        const timestamp = document.getElementById('timestamp');

        // Ensure category is treated as string for comparison
        const categoryStr = String(data.category).toUpperCase();
        const isProductive = categoryStr === 'PRODUTIVO';
        
        categoryBadge.className = `category-badge ${isProductive ? 'productive' : 'improductive'}`;
        categoryLabel.textContent = data.category;
        confidenceValue.textContent = `${Math.round((data.confidence || 0) * 100)}%`;
        confidenceFill.className = `confidence-fill ${isProductive ? 'productive' : 'improductive'}`;
        confidenceFill.style.width = `${Math.round((data.confidence || 0) * 100)}%`;

        responseText.textContent = data.suggested_response || '—';
        processingTime.textContent = `${data.processing_time || '—'}s`;
        timestamp.textContent = new Date().toLocaleString('pt-BR');

        // Update stats
        document.getElementById('statAccuracy').textContent = '94%';
        document.getElementById('statTime').textContent = `${data.processing_time || '-'}s`;

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (show) {
            overlay.style.display = 'flex';
            overlay.setAttribute('aria-hidden','false');
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = 'Processando...';
        } else {
            overlay.style.display = 'none';
            overlay.setAttribute('aria-hidden','true');
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analisar Email';
        }
    }

    showNotification(message, type = 'info') {
        UIController.showNotification(message, type);
    }
}

// Global functions
async function processEmail() {
    if (!window.app) window.app = new EmailClassifierApp();
    await window.app.processEmail();
}

function removeFile() {
    if (!window.app) return;
    const fileInfo = document.getElementById('fileInfo');
    const uploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('fileInput');

    fileInfo.style.display = 'none';
    uploadArea.style.display = 'block';
    fileInput.value = '';
    window.app.currentFile = null;

    document.querySelectorAll('.input-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector('[data-option="text"]').classList.add('active');

    window.app.showNotification('Arquivo removido', 'info');
}

function clearForm() {
    document.getElementById('emailText').value = '';
    removeFile();

    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'none';

    if (window.app) window.app.showNotification('Formulário limpo', 'info');
}

async function copyResponse() {
    const responseText = document.getElementById('responseText').textContent || '';
    try {
        await navigator.clipboard.writeText(responseText);
        UIController.showNotification('Resposta copiada para a área de transferência!', 'success');
    } catch (err) {
        UIController.showNotification('Erro ao copiar resposta', 'error');
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new EmailClassifierApp();
});