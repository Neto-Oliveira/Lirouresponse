import aiofiles
import PyPDF2
import io
import logging
from typing import Optional
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)


class FileProcessor:
    @staticmethod
    async def process_uploaded_file(file: UploadFile) -> str:
        """Process uploaded file and extract text content."""
        try:
            if not file.filename:
                raise HTTPException(400, "Nome do arquivo não fornecido")
            
            filename = file.filename.lower()

            # Extensões suportadas
            if not filename.endswith(('.txt', '.pdf')):
                raise HTTPException(400, "Tipo de arquivo não suportado. Use .txt ou .pdf")
            
            # Lê o conteúdo do arquivo
            content = await file.read()

            if filename.endswith('.pdf'):
                text = await FileProcessor._extract_text_from_pdf(content)
            else:
                # TXT
                try:
                    text = content.decode('utf-8')
                except UnicodeDecodeError:
                    raise HTTPException(400, "Erro ao decodificar arquivo .txt. Certifique-se de que está em UTF-8.")

            if not text.strip():
                raise HTTPException(400, "Arquivo vazio ou sem texto legível")

            return text
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {str(e)}")
            raise HTTPException(500, f"Erro ao processar arquivo: {str(e)}")

    @staticmethod
    async def _extract_text_from_pdf(pdf_content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text = ""

            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            if not text.strip():
                raise ValueError("PDF sem texto extraível")

            return text.strip()

        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
            raise HTTPException(400, "Não foi possível extrair texto do PDF")


class PerformanceMetrics:
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_classifications": 0,
            "average_processing_time": 0.0,
            "error_count": 0
        }

    def record_request(self, processing_time: float, success: bool = True):
        """Record metrics for each request."""
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
        """Return a copy of current metrics."""
        return self.metrics.copy()


# Instância global para uso no sistema
performance_metrics = PerformanceMetrics()
