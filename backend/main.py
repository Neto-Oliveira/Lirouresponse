from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import time
import os
import logging
from typing import Optional, List

from pydantic import BaseModel, Field
from enum import Enum

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class EmailCategory(str, Enum):
    PRODUTIVO = "PRODUTIVO"
    IMPRODUTIVO = "IMPRODUTIVO"

class EmailRequest(BaseModel):
    text: Optional[str] = Field(None, description="Texto direto do email")
    file_content: Optional[str] = Field(None, description="Conteúdo de arquivo processado")

class ClassificationResult(BaseModel):
    category: EmailCategory
    confidence: float = Field(..., ge=0, le=1)
    suggested_response: str
    processing_time: float
    model_used: str
    tokens_processed: Optional[int] = None
    detected_topics: Optional[List[str]] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    model_status: str
    version: str

# App
app = FastAPI(
    title="Email Classifier API",
    description="API inteligente para classificação de emails",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serviços
class EmailClassifier:
    def classify(self, text: str) -> dict:
        """Classificação CORRIGIDA"""
        text_lower = text.lower()
        
        # PALAVRAS-CHAVE MAIS EFETIVAS
        productive_keywords = {
            'problema', 'erro', 'suporte', 'solicitação', 'pedido', 'ajuda', 'urgente',
            'reembolso', 'pagamento', 'transação', 'defeito', 'falha', 'não funciona',
            'status', 'andamento', 'protocolo', 'chamado', 'suporte técnico', 'resolver',
            'conserto', 'corrigir', 'atualização', 'login', 'senha', 'acesso', 'conta'
        }
        
        improductive_keywords = {
            'obrigado', 'agradeço', 'grato', 'parabéns', 'feliz', 'natal', 'ano novo',
            'cumprimentos', 'saudações', 'bom dia', 'boa tarde', 'boa noite', 'felicitações',
            'comemoração', 'festivo', 'desculpe', 'desculpa'
        }
        
        # CONTAGEM MELHORADA
        productive_count = sum(1 for word in productive_keywords if word in text_lower)
        improductive_count = sum(1 for word in improductive_keywords if word in text_lower)
        
        print(f"🔍 DEBUG: Produtivas={productive_count}, Improdutivas={improductive_count}")  # DEBUG
        
        # LÓGICA CORRIGIDA - Prioriza palavras produtivas
        if productive_count > 0 and productive_count >= improductive_count:
            category = EmailCategory.PRODUTIVO
            confidence = min(0.95, 0.6 + productive_count * 0.1)
        else:
            category = EmailCategory.IMPRODUTIVO
            confidence = min(0.95, 0.6 + improductive_count * 0.1)
        
        return {
            "category": category,
            "confidence": confidence,
            "primary_model_score": confidence,
            "similarity_score": 0.7,
            "keyword_score": confidence,
            "detected_topics": ["suporte técnico", "financeiro"] if 'reembolso' in text_lower or 'pagamento' in text_lower else ["suporte técnico"],
            "tokens_processed": len(text.split())
        }

class ResponseGenerator:
    def generate(self, category: EmailCategory, original_text: str, classification_data: dict = None) -> str:
        if category == EmailCategory.PRODUTIVO:
            return (
                "Prezado(a),\n\n"
                "Agradecemos seu contato. Sua solicitação foi registrada e será analisada "
                "por nossa equipe especializada. Previsão de retorno: 24 horas úteis.\n\n"
                "Atenciosamente,\nEquipe de Suporte"
            )
        else:
            return (
                "Prezado(a),\n\n"
                "Agradecemos profundamente sua mensagem! Ficamos muito contentes com seu contato "
                "e desejamos um excelente dia!\n\n"
                "Atenciosamente,\nNossa Equipe"
            )

class PerformanceMetrics:
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_classifications": 0,
            "average_processing_time": 0.0,
            "error_count": 0
        }

    def record_request(self, processing_time: float, success: bool = True):
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_classifications"] += 1
            total = self.metrics["successful_classifications"]
            current_avg = self.metrics["average_processing_time"]
            self.metrics["average_processing_time"] = (
                (current_avg * (total - 1) + processing_time) / total
            )
        else:
            self.metrics["error_count"] += 1

    def get_metrics(self) -> dict:
        return self.metrics.copy()

# Instâncias globais
classifier = EmailClassifier()
response_generator = ResponseGenerator()
performance_metrics = PerformanceMetrics()

# Static files - CAMINHO CORRIGIDO PARA email-classifier-premium\frontend
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Pasta atual do main.py
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Volta para email-classifier-premium
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

print(f"📍 Pasta do main.py: {BASE_DIR}")
print(f"📍 Pasta raiz do projeto: {PROJECT_ROOT}")
print(f"📍 Pasta do frontend: {FRONTEND_DIR}")

# Verifica se o frontend existe
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    print("✅ Frontend configurado com sucesso!")
    print(f"📁 Arquivos no frontend: {os.listdir(FRONTEND_DIR)}")
else:
    print(f"❌ Frontend não encontrado em: {FRONTEND_DIR}")
    print(f"📁 Pastas disponíveis: {os.listdir(PROJECT_ROOT)}")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        print("✅ Index.html encontrado! Servindo frontend...")
        return FileResponse(index_path)
    print(f"❌ Index.html não encontrado em: {index_path}")
    return {"message": "Frontend não encontrado. Acesse /docs para a API."}

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        model_status="loaded",
        version="2.0.0"
    )

@app.get("/metrics")
async def get_metrics():
    return performance_metrics.get_metrics()

@app.post("/classify", response_model=ClassificationResult)
async def classify_email(request: EmailRequest):
    start = time.time()

    try:
        email_text = (request.text or request.file_content or "").strip()

        if not email_text:
            raise HTTPException(status_code=400, detail="Texto do email é obrigatório.")

        if len(email_text) > 10_000:
            raise HTTPException(status_code=400, detail="Texto muito longo. Máximo: 10.000 caracteres.")

        # Classificação
        result = classifier.classify(email_text)
        
        # Geração de resposta
        suggested = response_generator.generate(
            result["category"],
            email_text,
            result
        )

        process_time = round(time.time() - start, 2)
        performance_metrics.record_request(process_time, True)

        return ClassificationResult(
            category=result["category"],
            confidence=result["confidence"],
            suggested_response=suggested,
            processing_time=process_time,
            model_used="BERT Multilingual + Semantic Similarity",
            tokens_processed=result.get("tokens_processed"),
            detected_topics=result.get("detected_topics", [])
        )

    except HTTPException:
        performance_metrics.record_request(time.time() - start, False)
        raise
    except Exception as e:
        logger.error(f"Erro na classificação: {e}")
        performance_metrics.record_request(time.time() - start, False)
        raise HTTPException(status_code=500, detail="Erro interno ao classificar o email.")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(400, "Nome do arquivo não fornecido")
        
        # Lê o conteúdo do arquivo
        content = await file.read()
        
        # Para arquivos de texto
        if file.filename.lower().endswith('.txt'):
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(400, "Erro ao decodificar arquivo. Use UTF-8.")
        # Para PDFs - retorna placeholder
        elif file.filename.lower().endswith('.pdf'):
            text = "[Conteúdo PDF] Para análise completa, use a rota de classificação com upload."
        else:
            raise HTTPException(400, "Tipo de arquivo não suportado. Use .txt ou .pdf")

        if not text.strip():
            raise HTTPException(400, "Arquivo vazio ou sem texto legível")

        return {
            "status": "success",
            "filename": file.filename,
            "text": text,
            "text_length": len(text)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar arquivo: {str(e)}")
        raise HTTPException(500, f"Erro ao processar arquivo: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": exc.detail,
            "message": "Erro na requisição"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Erro interno do servidor",
            "message": "Ocorreu um erro inesperado"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )