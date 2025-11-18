# response_generator.py
import random
import time
import logging
from typing import Dict, List
from models import EmailCategory

logger = logging.getLogger(__name__)


class ResponseGenerator:
    def __init__(self):
        self._setup_response_templates()

    def _setup_response_templates(self):
        """Define templates de respostas para emails produtivos e improdutivos."""
        self.productive_templates = [
            {
                "template": (
                    "Prezado(a),\n\n"
                    "Agradecemos seu contato sobre {assunto}. Sua solicitação foi registrada sob o protocolo "
                    "{protocolo} e será analisada por nossa equipe especializada. Previsão de retorno: {prazo}.\n\n"
                    "Atenciosamente,\nEquipe de Suporte"
                ),
                "context": ["problema", "erro", "defeito", "falha", "bug", "não funciona", "quebrado"],
                "priority": 1
            },
            {
                "template": (
                    "Olá!\n\n"
                    "Confirmamos o recebimento de sua solicitação referente a {assunto}. Nossa equipe já foi acionada "
                    "e você receberá uma atualização em até {prazo}. Protocolo: {protocolo}.\n\n"
                    "Atenciosamente,\nCentral de Atendimento"
                ),
                "context": ["solicitação", "pedido", "requisição", "peço", "solicitar"],
                "priority": 1
            }
        ]

        self.improductive_templates = [
            {
                "template": (
                    "Prezado(a),\n\nAgradecemos profundamente sua mensagem {assunto}. "
                    "Ficamos muito contentes com seu contato e desejamos um excelente {periodo}!\n\n"
                    "Atenciosamente,\nEquipe"
                ),
                "context": ["agradecimento", "obrigado", "grato", "agradeço", "thanks", "thank you"],
                "priority": 1
            }
        ]

        self.time_frames = {
            "urgent": "2 horas úteis",
            "high": "4 horas úteis", 
            "medium": "24 horas úteis",
            "low": "48 horas úteis"
        }

    def generate(self, category: EmailCategory, original_text: str, classification_data: Dict = None) -> str:
        """Gera a resposta completa baseada na categoria."""
        try:
            text_lower = original_text.lower()
            
            if category == EmailCategory.PRODUTIVO:
                return self._generate_productive_response(text_lower, original_text)
            else:
                return self._generate_improductive_response(text_lower, original_text)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._generate_fallback_response(category)

    def _generate_productive_response(self, text_lower: str, original_text: str) -> str:
        """Gera resposta para emails produtivos."""
        if 'reembolso' in text_lower or 'estorno' in text_lower:
            return (
                "Prezado(a),\n\n"
                "Recebemos sua solicitação de reembolso. Sua solicitação foi registrada sob o protocolo "
                f"REF-{int(time.time())} e será analisada por nossa equipe financeira. "
                "O prazo para análise é de até 5 dias úteis.\n\n"
                "Atenciosamente,\nEquipe Financeira"
            )
        elif any(word in text_lower for word in ['login', 'senha', 'acesso', 'conta']):
            return (
                "Prezado(a),\n\n"
                "Identificamos sua solicitação de acesso. Sua demanda foi registrada sob o protocolo "
                f"ACS-{int(time.time())} e será atendida por nossa equipe de segurança em até 24 horas.\n\n"
                "Atenciosamente,\nEquipe de Acesso"
            )
        elif 'urgente' in text_lower or 'emergência' in text_lower or 'crítico' in text_lower:
            return (
                "Prezado(a),\n\n"
                "URGENTE: Sua solicitação foi recebida com prioridade máxima. "
                f"Protocolo: URG-{int(time.time())}. Nossa equipe já foi acionada e retornará em até 2 horas.\n\n"
                "Atenciosamente,\nEquipe de Emergência"
            )
        else:
            return self._generate_generic_productive_response(original_text)

    def _generate_improductive_response(self, text_lower: str, original_text: str) -> str:
        """Gera resposta para emails improdutivos."""
        if any(word in text_lower for word in ['obrigado', 'agradeço', 'grato', 'obrigada']):
            return (
                "Prezado(a),\n\n"
                "Agradecemos profundamente suas palavras! Ficamos muito felizes em saber "
                "que nosso atendimento foi satisfatório. Conte sempre conosco!\n\n"
                "Atenciosamente,\nNossa Equipe"
            )
        elif any(word in text_lower for word in ['parabéns', 'felicitações', 'congratulations']):
            return (
                "Prezado(a),\n\n"
                "Que alegria receber suas felicitações! Muito obrigado pelo carinho e atenção. "
                "Desejamos tudo de bom para você também!\n\n"
                "Atenciosamente,\nNossa Equipe"
            )
        elif any(word in text_lower for word in ['natal', 'ano novo', 'réveillon']):
            return (
                "Prezado(a),\n\n"
                "Agradecemos seus votos! Desejamos a você e sua família um excelente "
                "natal e um próspero ano novo repleto de realizações!\n\n"
                "Atenciosamente,\nToda a Equipe"
            )
        else:
            return self._generate_generic_improductive_response(original_text)

    def _generate_generic_productive_response(self, text: str) -> str:
        """Gera resposta genérica para emails produtivos."""
        subject = self._extract_subject(text)
        protocol = self._generate_protocol()
        prazo = self._get_time_frame("medium")

        return (
            "Prezado(a),\n\n"
            "Agradecemos seu contato. Sua solicitação foi registrada e será analisada "
            f"por nossa equipe especializada. Previsão de retorno: {prazo}. "
            f"Protocolo: {protocol}.\n\n"
            "Atenciosamente,\nEquipe de Suporte"
        )

    def _generate_generic_improductive_response(self, text: str) -> str:
        """Gera resposta genérica para emails improdutivos."""
        return (
            "Prezado(a),\n\n"
            "Agradecemos profundamente sua mensagem! Ficamos muito contentes com seu contato "
            "e desejamos um excelente dia!\n\n"
            "Atenciosamente,\nNossa Equipe"
        )

    def _extract_subject(self, text: str) -> str:
        """Tenta detectar o assunto no corpo do e-mail."""
        lines = text.splitlines()
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["assunto:", "subject:", "titulo:", "title:"]):
                try:
                    subject = line.split(":", 1)[1].strip()
                    return subject if subject else "sua mensagem"
                except:
                    return "sua mensagem"
        return "sua mensagem"

    def _generate_protocol(self) -> str:
        return f"PRT-{int(time.time())}-{random.randint(1000, 9999)}"

    def _get_time_frame(self, urgency: str) -> str:
        return self.time_frames.get(urgency, "24 horas úteis")

    def _generate_fallback_response(self, category: EmailCategory) -> str:
        if category == EmailCategory.PRODUTIVO:
            return (
                "Prezado(a),\n\nAgradecemos seu contato. Sua mensagem foi recebida e será "
                "processada por nossa equipe em breve.\n\nAtenciosamente,\nEquipe de Atendimento"
            )
        return (
            "Prezado(a),\n\nAgradecemos sua mensagem! Ficamos felizes com seu contato.\n\n"
            "Atenciosamente,\nNossa Equipe"
        )