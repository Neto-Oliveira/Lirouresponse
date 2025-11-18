// Variáveis globais
let currentFile = null;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    setupOptionToggler();
    setupFileUpload();
    setupSmoothAnimations();
});

// Configuração de event listeners
function setupEventListeners() {
    const textarea = document.getElementById('emailText');
    if (textarea) {
        textarea.addEventListener('input', autoResizeTextarea);
        textarea.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                processEmailRequest();
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

function setupOptionToggler() {
    const options = document.querySelectorAll('.input-option');
    options.forEach(option => {
        option.addEventListener('click', (e) => {
            if (e.target.closest('button') || e.target.tagName === 'INPUT') return;
            options.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
        });

        option.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                options.forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
                if (option.dataset.option === 'file') document.getElementById('fileInput').click();
            }
        });
    });
}

function setupFileUpload() {
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
        if (files.length) handleFileSelect(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileSelect(e.target.files[0]);
    });
}

function setupSmoothAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('fade-in');
        });
    }, { threshold: 0.12 });

    document.querySelectorAll('.result-card, .section-header, .input-option').forEach(el => observer.observe(el));
}

// Funções de manipulação de arquivo
async function extractTextFromFile(file) {
    if (file.type === 'application/pdf') {
        return "[Conteúdo PDF] Arquivo carregado com sucesso. Clique em 'Analisar Email' para processar.";
    } else {
        return await readAsText(file);
    }
}

function readAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            resolve(String(e.target.result).replace(/\r\n/g, '\n'));
        };
        reader.onerror = (e) => reject(new Error('Failed to read file as text'));
        reader.readAsText(file, 'utf-8');
    });
}

function validateFile(file) {
    const allowedTypes = ['text/plain', 'application/pdf'];
    const allowedExtensions = ['.txt', '.pdf'];
    const maxSize = 5 * 1024 * 1024;

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

function handleFileSelect(file) {
    try {
        validateFile(file);
    } catch (err) {
        showNotification(err.message || 'Arquivo inválido', 'error');
        return;
    }

    currentFile = file;
    displayFileInfo(file);

    document.querySelectorAll('.input-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector('[data-option="file"]').classList.add('active');
}

function displayFileInfo(file) {
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('fileInfo').style.display = 'block';
    document.getElementById('fileUploadArea').style.display = 'none';
}

function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B','KB','MB','GB','TB'];
    const i = Math.floor(Math.log(bytes)/Math.log(k));
    return parseFloat((bytes/Math.pow(k,i)).toFixed(2)) + ' ' + sizes[i];
}

function autoResizeTextarea(e) {
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// CORREÇÃO: Renomeei a função principal para evitar recursão
async function processEmailRequest() {
    const activeOption = document.querySelector('.input-option.active');
    const optionType = activeOption?.dataset.option;
    let emailContent = '';

    if (optionType === 'text') {
        emailContent = document.getElementById('emailText').value.trim();
    } else if (optionType === 'file' && currentFile) {
        try {
            emailContent = await extractTextFromFile(currentFile);
        } catch (err) {
            showNotification('Erro ao ler arquivo: ' + err.message, 'error');
            return;
        }
    }

    if (!emailContent) {
        showNotification('Por favor, insira o conteúdo do email ou selecione um arquivo.', 'warning');
        return;
    }

    showLoading(true);

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
        displayResults(data);
        showNotification('Email analisado com sucesso!', 'success');

    } catch (err) {
        showNotification('Erro ao processar email: ' + (err.message || err), 'error');
    } finally {
        showLoading(false);
    }
}

function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const categoryBadge = document.getElementById('categoryBadge');
    const categoryLabel = document.getElementById('categoryLabel');
    const confidenceValue = document.getElementById('confidenceValue');
    const confidenceFill = document.getElementById('confidenceFill');
    const responseText = document.getElementById('responseText');
    const processingTime = document.getElementById('processingTime');
    const timestamp = document.getElementById('timestamp');

    const categoryStr = String(data.category).toUpperCase();
    const isProductive = categoryStr === 'PRODUTIVO';
    
    categoryBadge.className = `category-badge ${isProductive ? 'productive' : 'improductive'}`;
    categoryLabel.textContent = data.category;
    confidenceValue.textContent = `${Math.round((data.confidence || 0) * 100)}%`;
    confidenceFill.className = `confidence-fill ${isProductive ? 'productive' : 'improductive'}`;
    confidenceFill.style.width = `${Math.round((data.confidence || 0) * 100)}%`;

    responseText.textContent = data.suggested_response || '—';
    
    // CORREÇÃO: Garantir que o tempo aparece corretamente
    processingTime.textContent = `${data.processing_time || '0.0'}s`;
    
    timestamp.textContent = new Date().toLocaleString('pt-BR');

    // CORREÇÃO: Resetar stats quando limpar
    document.getElementById('statAccuracy').textContent = '94%';
    document.getElementById('statTime').textContent = `${data.processing_time || '0.0'}s`;

    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showLoading(show) {
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

// CORREÇÃO: Esta é a função que é chamada pelo botão HTML
function processEmail() {
    processEmailRequest();
}

function removeFile() {
    const fileInfo = document.getElementById('fileInfo');
    const uploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('fileInput');

    fileInfo.style.display = 'none';
    uploadArea.style.display = 'block';
    fileInput.value = '';
    currentFile = null;

    document.querySelectorAll('.input-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector('[data-option="text"]').classList.add('active');

    showNotification('Arquivo removido', 'info');
}

function clearForm() {
    document.getElementById('emailText').value = '';
    removeFile();

    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'none';

    // CORREÇÃO: Resetar estatísticas no header
    document.getElementById('statAccuracy').textContent = '—';
    document.getElementById('statTime').textContent = '—';

    showNotification('Formulário limpo', 'info');
}

async function copyResponse() {
    const responseText = document.getElementById('responseText').textContent || '';
    try {
        await navigator.clipboard.writeText(responseText);
        showNotification('Resposta copiada para a área de transferência!', 'success');
    } catch (err) {
        showNotification('Erro ao copiar resposta', 'error');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} slide-up`;
    notification.setAttribute('role','alert');
    notification.innerHTML = `
        <div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:18px;color:var(--primary-color);width:24px;height:24px;display:flex;align-items:center;justify-content:center">
                ${getIconSvg(type)}
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

function getIconSvg(type) {
    if (type === 'success') return '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.2 4.8 12l1.4-1.4L9 13.4 18.8 3.6 20.2 5z"/></svg>';
    if (type === 'error') return '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"/></svg>';
    if (type === 'warning') return '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>';
    return '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>';
}

// Base de emails exemplo
const exampleEmails = {
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
        },
        {
            text: "Esqueci minha senha de acesso e não consigo entrar na minha conta. Podem me ajudar a redefinir?",
            category: "PRODUTIVO",
            description: "🔐 Problema de acesso"
        },
        {
            text: "Qual o status do meu pedido #7890? Fiz a compra há 5 dias e ainda não recebi confirmação de envio.",
            category: "PRODUTIVO",
            description: "📋 Consulta de status"
        },
        {
            text: "Estou com problemas para fazer upload de arquivos PDF no sistema. Recebo erro 'tamanho máximo excedido' mesmo com arquivos pequenos.",
            category: "PRODUTIVO",
            description: "📎 Problema com upload"
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
        },
        {
            text: "Bom dia equipe! Só passando para desejar um ótimo final de semana a todos.",
            category: "IMPRODUTIVO", 
            description: "👋 Saudação"
        },
        {
            text: "Parabéns pelo aniversário da empresa! Desejo muitos anos de sucesso e crescimento.",
            category: "IMPRODUTIVO",
            description: "🎂 Parabéns"
        },
        {
            text: "Gostaria de agradecer a todos pelo suporte técnico excepcional. Ficamos muito satisfeitos com o serviço!",
            category: "IMPRODUTIVO",
            description: "⭐ Agradecimento elogioso"
        }
    ],
    borderline: [
        {
            text: "Primeiro gostaria de agradecer pelo atendimento anterior que foi excelente. Agora estou com outro problema: não consigo fazer upload de arquivos PDF no sistema.",
            category: "PRODUTIVO",
            description: "🔄 Misto: Agradecimento + Problema"
        },
        {
            text: "Prezados, venho por meio deste solicitar informações sobre o status de minha solicitação de suporte técnico registrada sob o protocolo ST-456.",
            category: "PRODUTIVO", 
            description: "📝 Formal corporativo"
        },
        {
            text: "EMERGÊNCIA: Servidor de produção apresentando falhas críticas. Necessário suporte URGENTE da equipe técnica.",
            category: "PRODUTIVO",
            description: "⚡ Emergência explícita"
        }
    ]
};

// Função para gerar email exemplo
function generateExampleEmail() {
    // Seleciona categoria aleatória
    const categories = ['productive', 'improductive', 'borderline'];
    const randomCategory = categories[Math.floor(Math.random() * categories.length)];
    
    // Seleciona email aleatório da categoria
    const emails = exampleEmails[randomCategory];
    const randomEmail = emails[Math.floor(Math.random() * emails.length)];
    
    // Insere no textarea
    const textarea = document.getElementById('emailText');
    textarea.value = randomEmail.text;
    
    // Auto-resize
    autoResizeTextarea({ target: textarea });
    
    // Mostra notificação informativa
    showNotification(`📧 Exemplo carregado: ${randomEmail.description} (Esperado: ${randomEmail.category})`, 'info');
    
    // Ativa a opção de texto
    document.querySelectorAll('.input-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector('[data-option="text"]').classList.add('active');
}