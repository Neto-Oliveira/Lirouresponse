// EmailClassifierApp - Versão Otimizada para Vercel + Backend Remoto
class EmailClassifierApp {
    constructor() {
        this.currentFile = null;
        this.isProcessing = false;
        this.backendAvailable = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupOptionToggler();
        this.setupFileUpload();
        this.setupSmoothAnimations();
        this.checkBackendStatus();
    }

    setupEventListeners() {
        const textarea = document.getElementById('emailText');
        if (textarea) {
            textarea.addEventListener('input', this.autoResizeTextarea.bind(this));
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

        // Enter key no textarea
        textarea?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.processEmail();
            }
        });
    }

    setupOptionToggler() {
        const options = document.querySelectorAll('.input-option');
        options.forEach(option => {
            option.addEventListener('click', (e) => {
                if (e.target.closest('button') || e.target.tagName === 'INPUT') return;
                this.switchOption(option);
            });

            option.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.switchOption(option);
                }
            });
        });
    }

    switchOption(option) {
        const options = document.querySelectorAll('.input-option');
        options.forEach(opt => opt.classList.remove('active'));
        option.classList.add('active');
        
        if (option.dataset.option === 'file') {
            document.getElementById('fileInput').click();
        }
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

    setupSmoothAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.result-card, .section-header, .input-option').forEach(el => {
            observer.observe(el);
        });
    }

    async checkBackendStatus() {
    try {
        // Tenta primeiro o endpoint raiz
        const response = await fetch(CONFIG.getApiUrl('health'), {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        // Se receber HTML, tenta parsear como JSON ou verifica se é a documentação
        const contentType = response.headers.get('content-type') || '';
        
        if (response.ok) {
            if (contentType.includes('application/json')) {
                const data = await response.json();
                this.backendAvailable = true;
                console.log('✅ Backend conectado:', data);
                this.updateBackendStatus(true);
            } else {
                // Se não é JSON mas retornou OK, considera online
                this.backendAvailable = true;
                console.log('✅ Backend respondendo (HTML)');
                this.updateBackendStatus(true);
            }
        } else {
            console.warn('⚠️ Backend com status não ideal');
            this.updateBackendStatus(false);
        }
    } catch (error) {
        console.error('❌ Backend não disponível:', error);
        this.updateBackendStatus(false);
    }
}

    updateBackendStatus(available) {
        this.backendAvailable = available;
        const statusIndicator = document.getElementById('backendStatus') || this.createStatusIndicator();
        
        if (available) {
            statusIndicator.className = 'backend-status connected';
            statusIndicator.innerHTML = '✅ Backend Online';
        } else {
            statusIndicator.className = 'backend-status disconnected';
            statusIndicator.innerHTML = '❌ Backend Offline';
        }
    }

    createStatusIndicator() {
        const header = document.querySelector('.header');
        const statusDiv = document.createElement('div');
        statusDiv.id = 'backendStatus';
        statusDiv.className = 'backend-status';
        statusDiv.style.cssText = `
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 4px;
            margin-left: 10px;
        `;
        header.appendChild(statusDiv);
        return statusDiv;
    }

    // Manipulação de arquivos
    async extractTextFromFile(file) {
        if (file.type === 'application/pdf') {
            // Para PDF, faz upload e extração no backend
            return await this.uploadAndExtractFile(file);
        } else {
            return await this.readAsText(file);
        }
    }

    async uploadAndExtractFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(CONFIG.getApiUrl('upload'), {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Erro no upload: ${response.status}`);
            }

            const result = await response.json();
            return result.text || "Conteúdo extraído com sucesso. Clique em 'Analisar Email'.";
            
        } catch (error) {
            console.error('Erro no upload:', error);
            return await this.readAsText(file); // Fallback para leitura local
        }
    }

    readAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                resolve(String(e.target.result).replace(/\r\n/g, '\n'));
            };
            reader.onerror = (e) => reject(new Error('Falha ao ler arquivo'));
            reader.readAsText(file, 'utf-8');
        });
    }

    validateFile(file) {
        const allowedTypes = ['text/plain', 'application/pdf'];
        const allowedExtensions = ['.txt', '.pdf'];
        const maxSize = CONFIG.maxFileSize;

        const hasValidType = allowedTypes.includes(file.type);
        const hasValidExtension = allowedExtensions.some(ext => 
            file.name.toLowerCase().endsWith(ext)
        );

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

    handleFileSelect(file) {
        try {
            this.validateFile(file);
        } catch (err) {
            this.showNotification(err.message || 'Arquivo inválido', 'error');
            return;
        }

        this.currentFile = file;
        this.displayFileInfo(file);

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

    // Processamento principal
    async processEmail() {
        if (this.isProcessing) return;

        if (!this.backendAvailable) {
            this.showNotification('Backend não disponível. Verifique a conexão.', 'error');
            return;
        }

        const activeOption = document.querySelector('.input-option.active');
        const optionType = activeOption?.dataset.option;
        let emailContent = '';

        // Validação de conteúdo
        if (optionType === 'text') {
            emailContent = document.getElementById('emailText').value.trim();
        } else if (optionType === 'file' && this.currentFile) {
            try {
                this.showNotification('📁 Processando arquivo...', 'info');
                emailContent = await this.extractTextFromFile(this.currentFile);
            } catch (err) {
                this.showNotification('Erro ao processar arquivo: ' + err.message, 'error');
                return;
            }
        }

        if (!emailContent) {
            this.showNotification('Por favor, insira o conteúdo do email ou selecione um arquivo.', 'warning');
            return;
        }

        if (emailContent.length > 10000) {
            this.showNotification('Texto muito longo. Máximo: 10.000 caracteres.', 'warning');
            return;
        }

        this.showLoading(true);
        this.isProcessing = true;

        try {
            const payload = { text: emailContent };
            const response = await fetch(CONFIG.getApiUrl('classify'), {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload),
                signal: AbortSignal.timeout(CONFIG.timeout)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                const msg = errorData?.detail || errorData?.error || `Erro HTTP ${response.status}`;
                throw new Error(msg);
            }

            const data = await response.json();
            this.displayResults(data);
            this.showNotification('✅ Email analisado com sucesso!', 'success');

        } catch (err) {
            console.error('Erro no processamento:', err);
            this.showNotification('❌ Erro ao processar email: ' + (err.message || err), 'error');
        } finally {
            this.showLoading(false);
            this.isProcessing = false;
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
        const modelUsed = document.getElementById('modelUsed');

        // Garantir que category é string
        const categoryStr = String(data.category || '').toUpperCase();
        const isProductive = categoryStr === 'PRODUTIVO';
        const confidence = data.confidence || 0;
        
        // Atualizar badge de categoria
        categoryBadge.className = `category-badge ${isProductive ? 'productive' : 'improductive'}`;
        categoryLabel.textContent = isProductive ? 'PRODUTIVO' : 'IMPRODUTIVO';
        confidenceValue.textContent = `${Math.round(confidence * 100)}%`;
        
        // Barra de confiança
        confidenceFill.className = `confidence-fill ${isProductive ? 'productive' : 'improductive'}`;
        confidenceFill.style.width = `${Math.round(confidence * 100)}%`;

        // Resposta sugerida
        responseText.textContent = data.suggested_response || '—';
        
        // Informações de processamento
        processingTime.textContent = `${data.processing_time || '0.0'}s`;
        modelUsed.textContent = data.model_used || 'BERT + Semantic Similarity';
        timestamp.textContent = new Date().toLocaleString('pt-BR');

        // Atualizar estatísticas no header
        document.getElementById('statAccuracy').textContent = `${Math.round(confidence * 100)}%`;
        document.getElementById('statTime').textContent = `${data.processing_time || '0.0'}s`;

        // Mostrar resultados com animação
        resultsSection.style.display = 'block';
        setTimeout(() => {
            resultsSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        const analyzeBtn = document.getElementById('analyzeBtn');
        
        if (show) {
            overlay.style.display = 'flex';
            overlay.setAttribute('aria-hidden','false');
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = 'Processando...';
            analyzeBtn.classList.add('pulse');
        } else {
            overlay.style.display = 'none';
            overlay.setAttribute('aria-hidden','true');
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analisar Email';
            analyzeBtn.classList.remove('pulse');
        }
    }

    removeFile() {
        const fileInfo = document.getElementById('fileInfo');
        const uploadArea = document.getElementById('fileUploadArea');
        const fileInput = document.getElementById('fileInput');

        fileInfo.style.display = 'none';
        uploadArea.style.display = 'block';
        fileInput.value = '';
        this.currentFile = null;

        document.querySelectorAll('.input-option').forEach(opt => opt.classList.remove('active'));
        document.querySelector('[data-option="text"]').classList.add('active');

        this.showNotification('📁 Arquivo removido', 'info');
    }

    clearForm() {
        document.getElementById('emailText').value = '';
        this.removeFile();

        const resultsSection = document.getElementById('resultsSection');
        resultsSection.style.display = 'none';

        // Resetar estatísticas
        document.getElementById('statAccuracy').textContent = '—';
        document.getElementById('statTime').textContent = '—';

        this.showNotification('🧹 Formulário limpo', 'info');
    }

    async copyResponse() {
        const responseText = document.getElementById('responseText').textContent || '';
        if (!responseText || responseText === '—') {
            this.showNotification('Nenhuma resposta para copiar', 'warning');
            return;
        }

        try {
            await navigator.clipboard.writeText(responseText);
            this.showNotification('📋 Resposta copiada!', 'success');
        } catch (err) {
            // Fallback para navegadores antigos
            const textArea = document.createElement('textarea');
            textArea.value = responseText;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showNotification('📋 Resposta copiada!', 'success');
        }
    }

    showNotification(message, type = 'info') {
        // Remover notificações existentes
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notif => notif.remove());

        const notification = document.createElement('div');
        notification.className = `notification notification-${type} bounce-in`;
        notification.setAttribute('role','alert');
        notification.style.cssText = `
            position: fixed; 
            top: 20px; 
            right: 20px; 
            background: var(--surface-color); 
            border: 1px solid var(--border-color);
            border-radius: 10px; 
            padding: 12px 16px; 
            box-shadow: var(--shadow-lg); 
            z-index: 1200; 
            display: flex; 
            align-items: center;
            gap: 12px;
            max-width: 400px;
            min-width: 300px;
        `;

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        notification.innerHTML = `
            <span style="font-size: 18px;">${icons[type] || 'ℹ️'}</span>
            <div style="flex: 1; color: var(--text-primary); font-size: 14px;">${message}</div>
            <button style="background: none; border: none; cursor: pointer; color: var(--text-tertiary); font-size: 16px; padding: 4px;">✕</button>
        `;

        notification.querySelector('button').addEventListener('click', () => {
            notification.remove();
        });

        document.body.appendChild(notification);

        // Auto-remove após 5 segundos
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideIn 0.3s ease reverse';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    generateExampleEmail() {
        const categories = ['productive', 'improductive', 'borderline'];
        const randomCategory = categories[Math.floor(Math.random() * categories.length)];
        
        const emails = this.exampleEmails[randomCategory];
        const randomEmail = emails[Math.floor(Math.random() * emails.length)];
        
        const textarea = document.getElementById('emailText');
        textarea.value = randomEmail.text;
        
        this.autoResizeTextarea({ target: textarea });
        
        this.showNotification(`📧 Exemplo carregado: ${randomEmail.description}`, 'info');
        
        document.querySelectorAll('.input-option').forEach(opt => opt.classList.remove('active'));
        document.querySelector('[data-option="text"]').classList.add('active');
    }

    // Base de emails exemplo
    exampleEmails = {
        productive: [
            {
                text: "URGENTE: Sistema crítico fora do ar. Não consigo acessar o painel administrativo desde às 14h. Preciso de suporte imediato para restabelecer o serviço.",
                category: "PRODUTIVO",
                description: "🚨 Emergência técnica"
            },
            {
                text: "Gostaria de solicitar um reembolso da minha última transação. O pagamento foi debitado mas o serviço não foi ativado. Número da transação: TRX-12345.",
                category: "PRODUTIVO", 
                description: "💰 Solicitação de reembolso"
            },
            {
                text: "Preciso de ajuda com um erro 500 no sistema. Quando tento fazer login, recebo mensagem de 'serviço indisponível'. Podem verificar?",
                category: "PRODUTIVO",
                description: "🔧 Problema técnico"
            }
        ],
        improductive: [
            {
                text: "Muito obrigado pelo excelente atendimento de ontem! A equipe foi muito prestativa e resolveu meu problema rapidamente.",
                category: "IMPRODUTIVO",
                description: "🙏 Agradecimento"
            },
            {
                text: "Desejo um feliz natal e um próspero ano novo para toda a equipe! Muito sucesso em 2024!",
                category: "IMPRODUTIVO",
                description: "🎄 Cumprimentos festivos"
            }
        ]
    };
}

// Inicialização da aplicação
let app;

document.addEventListener('DOMContentLoaded', function() {
    app = new EmailClassifierApp();
    
    // Expor funções globais para o HTML
    window.processEmail = () => app.processEmail();
    window.clearForm = () => app.clearForm();
    window.copyResponse = () => app.copyResponse();
    window.removeFile = () => app.removeFile();
    window.generateExampleEmail = () => app.generateExampleEmail();
});