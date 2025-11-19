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
        } else if (hostname.includes('vercel.app')) {
            return 'production';
        } else {
            return 'production';
        }
    }

    getBackendUrls() {
        if (this.environment === 'development') {
            return {
                base: 'http://localhost:8001',
                classify: 'http://localhost:8001/classify',
                classifyFile: 'http://localhost:8001/classify/file',
                upload: 'http://localhost:8001/upload', 
                health: 'http://localhost:8001/health',
                modelStatus: 'http://localhost:8001/model-status'
            };
        } else {
            // ✅ SUBSTITUIR pela SUA VPS
            return {
                base: 'http://18.219.41.143:8001',
                classify: 'http://18.219.41.143:8001/classify',
                classifyFile: 'http://18.219.41.143:8001/classify/file',
                upload: 'http://18.219.41.143:8001/upload',
                health: 'http://18.219.41.143:8001/health',
                modelStatus: 'http://18.219.41.143:8001/model-status'
            };
        }
    }

    getApiUrl(endpoint) {
        return this.backendUrls[endpoint] || `${this.backendUrls.base}${endpoint}`;
    }
}

// Instância global de configuração
const CONFIG = new Config();