# file_processor.py
import aiofiles
import PyPDF2
import io
import logging
from typing import Optional
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processador de arquivos para extração de texto."""
    
    @staticmethod
    async def process_uploaded_file(file: UploadFile) -> str:
        """Process uploaded file and extract text content."""
        try:
            if not file.filename:
                raise HTTPException(400, "Nome do arquivo não fornecido")
            
            filename = file.filename.lower()

            if not filename.endswith(('.txt', '.pdf')):
                raise HTTPException(400, "Tipo de arquivo não suportado. Use .txt ou .pdf")
            
            content = await file.read()

            if filename.endswith('.pdf'):
                text = await FileProcessor._extract_text_from_pdf(content)
            else:
                try:
                    text = content.decode('utf-8')
                except UnicodeDecodeError:
                    raise HTTPException(400, "Erro ao decodificar arquivo .txt. Use UTF-8.")

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