import random
import time
from typing import Dict, List
import logging
from .models import EmailCategory

logger = logging.getLogger(__name__)


class ResponseGenerator:
    def __init__(self):
        self._setup_response_templates()

    # ----------------------------------------------------------
    # CONFIGURAÇÃO DOS TEMPLATES - SUPER ATUALIZADO
    # ----------------------------------------------------------
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
            },
            {
                "template": (
                    "Caro(a) cliente,\n\n"
                    "Seu relato sobre {assunto} foi recebido e está em análise por nossa equipe técnica. Retornaremos "
                    "com uma solução em até {prazo}. Para referência, utilize o protocolo {protocolo}.\n\n"
                    "Atenciosamente,\nSuporte Técnico"
                ),
                "context": ["suporte", "assistência", "ajuda", "socorro", "suport", "help"],
                "priority": 1
            },
            {
                "template": (
                    "Prezado(a),\n\n"
                    "Informamos que sua demanda sobre {assunto} foi catalogada e está em processamento. Tempo estimado "
                    "para resolução: {prazo}. Número do protocolo: {protocolo}.\n\n"
                    "Atenciosamente,\nDepartamento de Atendimento"
                ),
                "context": ["status", "andamento", "situação", "atualização"],
                "priority": 1
            },
            {
                "template": (
                    "Prezado(a),\n\n"
                    "Recebemos sua solicitação de reembolso referente a {assunto}. Sua solicitação foi registrada "
                    "sob o protocolo {protocolo} e será analisada por nossa equipe financeira em até {prazo}.\n\n"
                    "Atenciosamente,\nEquipe Financeira"
                ),
                "context": ["reembolso", "estorno", "devolução"],
                "priority": 3  # Alta prioridade para reembolso
            },
            {
                "template": (
                    "Prezado(a),\n\n"
                    "Identificamos seu problema com {assunto}. Sua solicitação de reembolso foi registrada sob o "
                    "protocolo {protocolo} e será analisada por nossa equipe financeira. Prazo: {prazo}.\n\n"
                    "Atenciosamente,\nSetor Financeiro"
                ),
                "context": ["pagamento", "transação", "fatura", "cartão", "dinheiro", "valor", "pagar", "cobrança"],
                "priority": 2
            },
            {
                "template": (
                    "Prezado(a),\n\n"
                    "Recebemos sua solicitação de {assunto}. Sua demanda foi registrada sob o protocolo "
                    "{protocolo} e será atendida por nossa equipe de acesso em até {prazo}.\n\n"
                    "Atenciosamente,\nEquipe de Acesso e Segurança"
                ),
                "context": ["acesso", "login", "senha", "conta", "cadastro", "entrar", "logar", "acessar"],
                "priority": 2
            },
            {
                "template": (
                    "Prezado(a),\n\n"
                    "URGENTE: Sua solicitação sobre {assunto} foi recebida com prioridade máxima. "
                    "Protocolo: {protocolo}. Nossa equipe já foi acionada e retornará em até {prazo}.\n\n"
                    "Atenciosamente,\nEquipe de Emergência"
                ),
                "context": ["urgente", "crítico", "emergência", "prioridade", "imediato", "urgent", "emergency"],
                "priority": 4  # Máxima prioridade
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
            },
            {
                "template": (
                    "Olá!\n\nQue alegria receber sua mensagem {assunto}! Muito obrigado pelo carinho e atenção. "
                    "Desejamos tudo de bom!\n\nAtenciosamente,\nNossa Equipe"
                ),
                "context": ["parabéns", "felicitações", "comemoração", "congratulations", "feliz"],
                "priority": 2
            },
            {
                "template": (
                    "Caro(a) colaborador(a),\n\nAgradecemos suas {assunto}. Sua mensagem foi muito apreciada "
                    "por toda a equipe. Conte sempre conosco!\n\nAtenciosamente,\nGestão"
                ),
                "context": ["cumprimentos", "saudações", "saudação", "cumprimento", "saudaçoes"],
                "priority": 1
            },
            {
                "template": (
                    "Prezado(a),\n\nFicamos muito felizes com sua mensagem {assunto}. Seu feedback é muito importante "
                    "para nós. Desejamos um ótimo {periodo}!\n\nAtenciosamente,\nTime de Relacionamento"
                ),
                "context": ["feliz", "comemorativo", "festivo", "feedback", "elogio"],
                "priority": 1
            },
            {
                "template": (
                    "Prezado(a),\n\nQue honra receber seus {assunto}!\n\n"
                    "Agradecemos de coração suas palavras e desejamos um maravilhoso {periodo}!\n\n"
                    "Com gratidão,\nToda a Equipe"
                ),
                "context": ["honra", "felicitações especiais", "parabéns especial"],
                "priority": 3
            }
        ]

        # Tempos padrão
        self.time_frames = {
            "urgent": "2 horas úteis",
            "high": "4 horas úteis", 
            "medium": "24 horas úteis",
            "low": "48 horas úteis"
        }

    # ----------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ----------------------------------------------------------
    def generate(self, category: EmailCategory, original_text: str, classification_data: Dict = None) -> str:
        """Gera a resposta completa baseada na categoria."""
        try:
            if category == EmailCategory.PRODUTIVO:
                return self._generate_productive_response(original_text, classification_data)

            return self._generate_improductive_response(original_text, classification_data)

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._generate_fallback_response(category)

    # ----------------------------------------------------------
    # RESPOSTAS PRODUTIVAS - INTELIGENTE
    # ----------------------------------------------------------
    def _generate_productive_response(self, text: str, classification_data: Dict) -> str:
        subject = self._extract_subject(text)
        contexts = self._identify_context(text)
        urgency = self._assess_urgency(text, classification_data)

        template = self._select_productive_template(contexts, text)
        protocol = self._generate_protocol()
        prazo = self._get_time_frame(urgency)

        return template.format(
            assunto=subject or "sua solicitação",
            protocolo=protocol,
            prazo=prazo
        )

    # ----------------------------------------------------------
    # RESPOSTAS IMPRODUTIVAS
    # ----------------------------------------------------------
    def _generate_improductive_response(self, text: str, classification_data: Dict) -> str:
        subject = self._extract_subject(text)
        contexts = self._identify_context(text)
        period = self._identify_period(text)

        template = self._select_improductive_template(contexts)

        return template.format(
            assunto=subject or "amável",
            periodo=period or "dia"
        )

    # ----------------------------------------------------------
    # EXTRAÇÃO DE DADOS DO TEXTO - OTIMIZADO
    # ----------------------------------------------------------
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

        # fallback: primeira linha curta e significativa
        first_line = lines[0].strip()
        if (0 < len(first_line) < 100 and 
            not first_line.lower().startswith(("from:", "para:", "to:", "subject:", "sent:", "enviado:"))):
            return first_line

        return "sua mensagem"

    def _identify_context(self, text: str) -> List[str]:
        ctx = []
        text_lower = text.lower()

        # Mapeamento expandido e mais preciso
        mapping = {
            'problema': ['problema', 'erro', 'bug', 'defeito', 'falha', 'não funciona', 'quebrado', 'travado', 'lento'],
            'solicitação': ['solicito', 'solicitação', 'pedido', 'requisição', 'peço', 'solicitar', 'gostaria'],
            'suporte': ['suporte', 'ajuda', 'assistência', 'socorro', 'suport', 'help', 'auxílio'],
            'reembolso': ['reembolso', 'estorno', 'devolução', 'reembolsar', 'restituição'],
            'financeiro': ['pagamento', 'transação', 'fatura', 'cartão', 'dinheiro', 'valor', 'pagar', 'cobrança', 'débito'],
            'acesso': ['login', 'senha', 'conta', 'acesso', 'cadastro', 'entrar', 'logar', 'acessar', 'usuário'],
            'urgente': ['urgente', 'crítico', 'emergência', 'prioridade', 'imediato', 'urgent', 'emergency', 'critical', 'asap'],
            'agradecimento': ['obrigado', 'agradeço', 'grato', 'agradecimento', 'thanks', 'thank you', 'gratidão'],
            'parabéns': ['parabéns', 'felicitações', 'comemoração', 'congratulations', 'feliz aniversário'],
            'cumprimentos': ['cumprimentos', 'saudações', 'saudação', 'cumprimento', 'saudaçoes', 'saudacoes'],
            'festivo': ['natal', 'ano novo', 'réveillon', 'festas', 'feriado', 'comemoração']
        }

        for context, keywords in mapping.items():
            if any(k in text_lower for k in keywords):
                ctx.append(context)

        return ctx

    def _identify_period(self, text: str) -> str:
        text_lower = text.lower()

        checks = [
            ("Natal", ['natal', 'noel', 'christmas']),
            ("Ano Novo", ['ano novo', 'réveillon', 'year', 'new year']),
            ("fim de semana", ['fim de semana', 'sábado', 'domingo', 'weekend', 'sabado']),
            ("feriado", ['feriado', 'holiday', 'feriadão']),
            ("semana", ['semana', 'week']),
            ("tarde", ['tarde', 'afternoon']),
            ("noite", ['noite', 'night']),
            ("dia", ['dia', 'day', 'hoje', 'today'])
        ]

        for period, words in checks:
            if any(w in text_lower for w in words):
                return period

        return "dia"

    def _assess_urgency(self, text: str, classification_data: Dict) -> str:
        text_lower = text.lower()

        urgent = ['urgente', 'crítico', 'emergência', 'prioridade', 'imediato', 'urgent', 'emergency', 'critical', 'asap']
        high = ['importante', 'necessário', 'essencial', 'fundamental', 'important', 'necessary', 'preciso']

        if any(w in text_lower for w in urgent):
            return "urgent"
        if any(w in text_lower for w in high):
            return "high"
        if classification_data and classification_data.get("confidence", 0) > 0.8:
            return "medium"
        return "low"

    # ----------------------------------------------------------
    # ESCOLHA DE TEMPLATE - SUPER INTELIGENTE
    # ----------------------------------------------------------
    def _select_productive_template(self, contexts: List[str], original_text: str = "") -> str:
        text_lower = original_text.lower()
        
        # 1. PRIORIDADE MÁXIMA: Contextos específicos
        priority_order = ['urgente', 'reembolso', 'financeiro', 'acesso', 'problema', 'suporte', 'solicitação']
        
        for priority_context in priority_order:
            if priority_context in contexts:
                # Encontra templates com este contexto
                matching_templates = [
                    t for t in self.productive_templates 
                    if priority_context in t["context"]
                ]
                if matching_templates:
                    # Ordena por prioridade e escolhe o mais adequado
                    matching_templates.sort(key=lambda x: x.get("priority", 1), reverse=True)
                    return matching_templates[0]["template"]
        
        # 2. Fallback: qualquer template que combine
        all_matches = []
        for context in contexts:
            for template in self.productive_templates:
                if context in template["context"]:
                    all_matches.append(template)
        
        if all_matches:
            all_matches.sort(key=lambda x: x.get("priority", 1), reverse=True)
            return all_matches[0]["template"]
        
        # 3. Fallback final
        return random.choice([t["template"] for t in self.productive_templates])

    def _select_improductive_template(self, contexts: List[str]) -> str:
        # Ordena por prioridade
        matches = []
        for context in contexts:
            for template in self.improductive_templates:
                if context in template["context"]:
                    matches.append(template)
        
        if matches:
            matches.sort(key=lambda x: x.get("priority", 1), reverse=True)
            return matches[0]["template"]
        
        return random.choice([t["template"] for t in self.improductive_templates])

    # ----------------------------------------------------------
    # UTILIDADES
    # ----------------------------------------------------------
    def _generate_protocol(self) -> str:
        return f"PRT-{int(time.time())}-{random.randint(1000, 9999)}"

    def _get_time_frame(self, urgency: str) -> str:
        return self.time_frames.get(urgency, "24 horas úteis")

    # ----------------------------------------------------------
    # FALLBACK
    # ----------------------------------------------------------
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