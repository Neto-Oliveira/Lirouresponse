# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import time
import os
import logging
from typing import Optional

from models import EmailRequest, ClassificationResult, HealthCheck
from email_classifier import EmailClassifier
from response_generator import ResponseGenerator
from file_processor import FileProcessor
from performance_metrics import PerformanceMetrics

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# Instâncias globais
logger.info("🚀 Inicializando Email Classifier...")
classifier = EmailClassifier(use_ml_models=True)
response_generator = ResponseGenerator()
file_processor = FileProcessor()
performance_metrics = PerformanceMetrics()
logger.info("✅ Serviços inicializados com sucesso!")

# Static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

print(f"📍 Pasta do main.py: {BASE_DIR}")
print(f"📍 Pasta raiz do projeto: {PROJECT_ROOT}")
print(f"📍 Pasta do frontend: {FRONTEND_DIR}")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    print("✅ Frontend configurado com sucesso!")
    print(f"📁 Arquivos no frontend: {os.listdir(FRONTEND_DIR)}")
else:
    print(f"❌ Frontend não encontrado em: {FRONTEND_DIR}")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend não encontrado. Acesse /docs para a API."}

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        model_status="loaded" if classifier.use_ml_models else "rule_based",
        version="2.0.0"
    )

@app.get("/metrics")
async def get_metrics():
    return performance_metrics.get_metrics()

@app.post("/classify", response_model=ClassificationResult)
async def classify_email(request: EmailRequest):
    start_time = time.time()

    try:
        email_text = (request.text or request.file_content or "").strip()

        if not email_text:
            raise HTTPException(status_code=400, detail="Texto do email é obrigatório.")

        if len(email_text) > 10_000:
            raise HTTPException(status_code=400, detail="Texto muito longo. Máximo: 10.000 caracteres.")

        logger.info(f"📧 Classificando email com {len(email_text)} caracteres...")

        # Classificação
        classification_result = classifier.classify(email_text)
        
        # Geração de resposta
        suggested_response = response_generator.generate(
            classification_result["category"],
            email_text,
            classification_result
        )

        processing_time = round(time.time() - start_time, 2)
        performance_metrics.record_request(processing_time, True)

        logger.info(f"✅ Classificação concluída: {classification_result['category']} (confiança: {classification_result['confidence']:.2f})")

        return ClassificationResult(
            category=classification_result["category"],
            confidence=classification_result["confidence"],
            suggested_response=suggested_response,
            processing_time=processing_time,
            model_used="BERT + Semantic Similarity" if classifier.use_ml_models else "Rule-Based",
            tokens_processed=classification_result.get("tokens_processed"),
            detected_topics=classification_result.get("detected_topics", [])
        )

    except HTTPException:
        processing_time = round(time.time() - start_time, 2)
        performance_metrics.record_request(processing_time, False)
        raise
    except Exception as e:
        logger.error(f"❌ Erro na classificação: {e}")
        processing_time = round(time.time() - start_time, 2)
        performance_metrics.record_request(processing_time, False)
        raise HTTPException(status_code=500, detail="Erro interno ao classificar o email.")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        logger.info(f"📁 Processando arquivo: {file.filename}")
        text = await file_processor.process_uploaded_file(file)
        
        logger.info(f"✅ Arquivo processado com sucesso: {len(text)} caracteres extraídos")
        
        return {
            "status": "success",
            "filename": file.filename,
            "text": text,
            "text_length": len(text)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar arquivo: {str(e)}")
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
    logger.error(f"❌ Erro não tratado: {exc}")
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
    logger.info("🎯 Iniciando servidor FastAPI na porta 8000...")
    
    # REMOVIDO o reload para funcionar com python main.py
    uvicorn.run(
        app,  # Agora passa o app diretamente, não como string
        host="0.0.0.0",
        port=8000,
        log_level="info"
        # reload removido
    )