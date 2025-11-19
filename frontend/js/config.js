// Configuração de ambiente para frontend
class Config {
    constructor() {
        this.environment = this.detectEnvironment();
        this.backendUrls = this.getBackendUrls();
        this.timeout = 30000;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
    }

    detectEnvironment() {
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'development';
        } else {
            return 'production';
        }
    }

    getBackendUrls() {
        if (this.environment === 'development') {
            return {
                base: 'http://18.219.41.143:8001',
                classify: 'http://18.219.41.143:8001/classify',
                classifyFile: 'http://18.219.41.143:8001/classify/file',
                upload: 'http://18.219.41.143:8001/upload',
                health: 'http://18.219.41.143:8001/health',
                modelStatus: 'http://18.219.41.143:8001/model-status'
            };
        } else {
            // Em produção, usa as rotas relativas através do proxy do Vercel
            return {
                base: '',
                classify: '/api/classify',
                classifyFile: '/api/classify/file',
                upload: '/api/upload',
                health: '/api/health',
                modelStatus: '/api/model-status'
            };
        }
    }

    getApiUrl(endpoint) {
        const urls = this.backendUrls;
        return urls[endpoint] || `${urls.base}${endpoint}`;
    }
}

// Instância global de configuração
const CONFIG = new Config();