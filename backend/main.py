from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import os
import logging
from typing import Optional

# Import dos seus módulos existentes
from email_classifier import EmailClassifier
from response_generator import ResponseGenerator
from file_processor import FileProcessor
from performance_metrics import PerformanceMetrics
from models import EmailRequest, ClassificationResult, HealthCheck

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# App FastAPI
app = FastAPI(
    title="Email Classifier API - Premium Optimized",
    description="API inteligente e otimizada para classificação de emails",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para frontend no Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "https://lirouresponse-lbid.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instâncias globais
logger.info("🚀 Inicializando Email Classifier Premium...")

try:
    use_ml = os.getenv("USE_ML_MODELS", "true").lower() == "true"
    classifier = EmailClassifier(use_ml_models=use_ml)
    response_generator = ResponseGenerator()
    file_processor = FileProcessor()
    performance_metrics = PerformanceMetrics()
    
    logger.info(f"✅ Serviços inicializados! ML: {classifier.use_ml_models}")
    
except Exception as e:
    logger.error(f"❌ Erro na inicialização: {e}")
    raise

@app.get("/")
async def root():
    return {
        "message": "Email Classifier API - Premium Optimized",
        "version": "2.1.0",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        model_status="ml_loaded" if classifier.use_ml_models else "rule_based",
        version="2.1.0"
    )

@app.get("/model-status")
async def model_status():
    return {
        "ml_models_loaded": classifier.use_ml_models,
        "using_ml": classifier.use_ml_models,
        "memory_optimized": True,
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.get("/metrics")
async def get_metrics():
    return performance_metrics.get_metrics()

@app.post("/classify", response_model=ClassificationResult)
async def classify_email(request: EmailRequest):
    start_time = time.time()

    try:
        email_text = (request.text or request.file_content or "").strip()

        if not email_text:
            raise HTTPException(status_code=400, detail="Texto do email é obrigatório")

        if len(email_text) > 10_000:
            raise HTTPException(status_code=400, detail="Texto muito longo. Máximo: 10.000 caracteres")

        logger.info(f"📧 Classificando email com {len(email_text)} caracteres")

        # Classificação
        classification_result = classifier.classify(email_text)
        
        # Resposta sugerida
        suggested_response = response_generator.generate(
            classification_result["category"],
            email_text,
            classification_result
        )

        processing_time = round(time.time() - start_time, 3)
        performance_metrics.record_request(processing_time, True)

        logger.info(f"✅ Classificação: {classification_result['category']} (conf: {classification_result['confidence']:.2f})")

        return ClassificationResult(
            category=classification_result["category"],
            confidence=classification_result["confidence"],
            suggested_response=suggested_response,
            processing_time=processing_time,
            model_used="BERT + Semantic" if classifier.use_ml_models else "Rule-Based",
            tokens_processed=classification_result.get("tokens_processed", 0),
            detected_topics=classification_result.get("detected_topics", [])
        )

    except HTTPException:
        processing_time = round(time.time() - start_time, 3)
        performance_metrics.record_request(processing_time, False)
        raise
    except Exception as e:
        logger.error(f"❌ Erro na classificação: {e}")
        processing_time = round(time.time() - start_time, 3)
        performance_metrics.record_request(processing_time, False)
        raise HTTPException(status_code=500, detail="Erro interno ao classificar o email")

@app.post("/classify/file")
async def classify_email_file(file: UploadFile = File(...)):
    start_time = time.time()

    try:
        logger.info(f"📁 Processando arquivo: {file.filename}")
        text_content = await file_processor.process_uploaded_file(file)
        logger.info(f"✅ Arquivo processado: {len(text_content)} caracteres")

        request = EmailRequest(text=text_content)
        return await classify_email(request)

    except HTTPException:
        processing_time = round(time.time() - start_time, 3)
        performance_metrics.record_request(processing_time, False)
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar arquivo: {str(e)}")
        processing_time = round(time.time() - start_time, 3)
        performance_metrics.record_request(processing_time, False)
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        logger.info(f"📤 Upload: {file.filename}")
        text_content = await file_processor.process_uploaded_file(file)
        
        return {
            "status": "success",
            "filename": file.filename,
            "text_length": len(text_content),
            "message": "Arquivo processado com sucesso"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no upload: {str(e)}")
        raise HTTPException(500, f"Erro no processamento: {str(e)}")

# Error handlers
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
    logger.info("🎯 Iniciando servidor na porta 8000...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )