import re
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """Processamento de texto otimizado para classificação de emails."""

    def __init__(self):
        # Stopwords leves e otimizadas (não dependem do NLTK)
        self.stop_words = {
            'para','com','de','da','do','em','um','uma','os','as','ao','aos','na','nas','no','nos',
            'por','pelo','pelos','pela','pelas','esse','essa','isso','aquele','aquela','aquilo',
            'meu','minha','meus','minhas','seu','sua','seus','suas','nosso','nossa',
            'que','quem','onde','quando','como','porque','porquê','então','mas','e','ou','pois',
            'logo','portanto','também','já','ainda','só','sempre','nunca','agora','depois','antes'
        }

        # Regex comuns
        self.email_pattern = re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w+\b')
        self.url_pattern = re.compile(r'https?://\S+')
        self.phone_pattern = re.compile(r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}')

        # Palavras-chave com peso
        self.productive_keywords = {
            'problema': 2.0, 'erro': 2.0, 'falha': 2.0, 'defeito': 2.0,
            'suporte': 1.5, 'ajuda': 1.5, 'assistência': 1.5,
            'solicitação': 1.8, 'pedido': 1.8, 'requisição': 1.8,
            'status': 1.6, 'andamento': 1.6, 'atualização': 1.6,
            'pagamento': 1.7, 'transação': 1.7, 'reembolso': 1.7,
            'login': 1.3, 'senha': 1.3, 'acesso': 1.3
        }

        self.improductive_keywords = {
            'obrigado': 1.5, 'agradeço': 1.5, 'grato': 1.5,
            'parabéns': 1.8, 'feliz': 1.8, 'natal': 2.0, 'ano novo': 2.0,
            'feriado': 1.6, 'cumprimentos': 1.4
        }

    # ----------------------------------------------------------------------
    # PREPROCESSAMENTO
    # ----------------------------------------------------------------------
    def preprocess(self, text: str) -> str:
        """Limpa e prepara texto para análise."""
        if not text:
            return ""

        try:
            text = self._clean_text(text)

            # Tokenização simples
            tokens = re.findall(r'\b[\wçáàâãéêíóôõú]+(?:-[\w]+)?\b', text.lower())

            # Remove stopwords e tokens curtos
            tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]

            # Lematização simples (plural → singular)
            tokens = [self._simple_lemmatize(t) for t in tokens]

            return " ".join(tokens)
        except Exception as e:
            logger.error(f"Erro no preprocessamento: {e}")
            return text

    def _clean_text(self, text: str) -> str:
        """Remove emails, URLs, telefones e caracteres indesejados."""
        text = self.email_pattern.sub("", text)
        text = self.url_pattern.sub("", text)
        text = self.phone_pattern.sub("", text)
        text = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ!?.,\s-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _simple_lemmatize(self, token: str) -> str:
        """Lematização simples: plural → singular."""
        if token.endswith("s") and len(token) > 3:
            return token[:-1]
        return token

    # ----------------------------------------------------------------------
    # FEATURES POR PALAVRAS-CHAVE
    # ----------------------------------------------------------------------
    def extract_keyword_features(self, text: str) -> dict:
        """Calcula scores de palavras-chave produtivas e improdutivas."""
        text_lower = text.lower()
        productive_score = sum(
            len(re.findall(rf"\b{re.escape(kw)}\b", text_lower)) * weight
            for kw, weight in self.productive_keywords.items()
        )
        improductive_score = sum(
            len(re.findall(rf"\b{re.escape(kw)}\b", text_lower)) * weight
            for kw, weight in self.improductive_keywords.items()
        )

        total = productive_score + improductive_score
        if total == 0:
            return {"productive_score": 0.5, "improductive_score": 0.5, "keyword_confidence": 0.05}

        return {
            "productive_score": productive_score / total,
            "improductive_score": improductive_score / total,
            "keyword_confidence": min(total / 8, 1.0)
        }

    # ----------------------------------------------------------------------
    # DETECÇÃO DE TÓPICOS
    # ----------------------------------------------------------------------
    def detect_topics(self, text: str) -> list:
        """Detecta tópicos relevantes no email."""
        text_lower = text.lower()
        topics = []

        topic_categories = {
            'suporte técnico': ['problema', 'erro', 'falha', 'bug', 'sistema', 'aplicação'],
            'financeiro': ['pagamento', 'fatura', 'reembolso', 'transação'],
            'acesso': ['login', 'senha', 'conta', 'acesso'],
            'cumprimentos': ['obrigado', 'parabéns', 'feliz', 'saudações'],
        }

        for topic, keywords in topic_categories.items():
            if any(re.search(rf"\b{kw}\b", text_lower) for kw in keywords):
                topics.append(topic)

        return topics[:3]
