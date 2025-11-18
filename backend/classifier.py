import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import logging
import re
from typing import Dict, Any

from .text_processor import TextProcessor
from .models import EmailCategory

logger = logging.getLogger(__name__)

class EmailClassifier:
    """Classificador de emails PRODUTIVO vs IMPRODUTIVO."""

    def __init__(self):
        self.text_processor = TextProcessor()
        self._setup_models()

    def _setup_models(self):
        """Carrega modelos de ML necessários."""
        try:
            # Modelo BERT Multilingue para sentimento
            self.primary_classifier = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                tokenizer="nlptown/bert-base-multilingual-uncased-sentiment",
                device=-1  # CPU, alterar para 0 se GPU estiver disponível
            )

            # Sentence Transformer para similaridade semântica
            self.sentence_model = SentenceTransformer(
                "paraphrase-multilingual-MiniLM-L12-v2"
            )

            # Referências de emails produtivos e improdutivos
            self.productive_references = [
                "Preciso de ajuda com um problema no sistema",
                "Solicito suporte técnico para resolver um erro",
                "Gostaria de saber o status do meu pedido",
                "Estou com dificuldade para acessar minha conta",
                "Preciso de informações sobre minha transação",
                "Solicito reembolso de um pagamento realizado",
                "Reporto um defeito na aplicação",
                "Preciso de assistência urgente"
            ]

            self.improductive_references = [
                "Agradeço pelo atendimento de ontem",
                "Parabéns pelo aniversário da empresa",
                "Desejo um feliz natal para toda a equipe",
                "Agradeço a todos pelo trabalho",
                "Bom fim de semana para todos",
                "Muito obrigado pela ajuda",
                "Feliz ano novo para a equipe",
                "Cumprimentos a todos os colaboradores"
            ]

            # Pré-encode das referências (otimização importante!)
            with torch.no_grad():
                self.prod_ref_emb = self.sentence_model.encode(
                    self.productive_references,
                    convert_to_tensor=True
                )
                self.improd_ref_emb = self.sentence_model.encode(
                    self.improductive_references,
                    convert_to_tensor=True
                )

            logger.info("Modelos de ML carregados com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao carregar modelos: {e}")
            raise RuntimeError("Falha ao inicializar EmailClassifier") from e

    # -------------------------------------------------------------------------
    # CLASSIFICAÇÃO PRINCIPAL
    # -------------------------------------------------------------------------
    def classify(self, text: str) -> Dict[str, Any]:
        """Classifica um email como PRODUTIVO ou IMPRODUTIVO."""
        if not text or not isinstance(text, str):
            return self._default_response()

        try:
            processed_text = self.text_processor.preprocess(text)
            if not processed_text.strip():
                return self._default_response()

            # 1) Modelo primário
            primary_result = self._primary_classification(processed_text)

            # 2) Similaridade semântica
            similarity_result = self._semantic_similarity(processed_text)

            # 3) Features baseadas em palavras-chave
            keyword_features = self.text_processor.extract_keyword_features(text)

            # 4) Combinação final
            final_category, confidence = self._combine_results(
                primary_result,
                similarity_result,
                keyword_features
            )

            topics = self.text_processor.detect_topics(text)

            return {
                "category": final_category,
                "confidence": confidence,
                "primary_model_score": primary_result["score"],
                "similarity_score": similarity_result["score"],
                "keyword_score": keyword_features["productive_score"],
                "detected_topics": topics,
                "tokens_processed": len(processed_text.split())
            }

        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return self._default_response()

    # -------------------------------------------------------------------------
    # MODELO BERT PRINCIPAL
    # -------------------------------------------------------------------------
    def _primary_classification(self, text: str) -> Dict[str, Any]:
        """Classificação usando sentimento como proxy de produtividade."""
        try:
            truncated = text[:512]
            result = self.primary_classifier(truncated)[0]

            # Extrai número do label (ex: "1 star" → 1)
            sentiment_match = re.search(r'\d+', result["label"])
            sentiment = int(sentiment_match.group()) if sentiment_match else 3
            prob = result.get("score", 0.5)

            # Interpretação: 1-2 → PRODUTIVO, 4-5 → IMPRODUTIVO
            if sentiment <= 2:
                category = EmailCategory.PRODUTIVO
                score = min(1.0, 0.7 + (2 - sentiment) * 0.15)
            else:
                category = EmailCategory.IMPRODUTIVO
                score = min(1.0, 0.6 + (sentiment - 3) * 0.15)

            return {"category": category, "score": float(score)}

        except Exception:
            return {"category": EmailCategory.PRODUTIVO, "score": 0.5}

    # -------------------------------------------------------------------------
    # SIMILARIDADE SEMÂNTICA
    # -------------------------------------------------------------------------
    def _semantic_similarity(self, text: str) -> Dict[str, Any]:
        """Calcula similaridade semântica com referências."""
        try:
            with torch.no_grad():
                emb = self.sentence_model.encode(text, convert_to_tensor=True)

            prod_sim = util.pytorch_cos_sim(emb, self.prod_ref_emb)
            impr_sim = util.pytorch_cos_sim(emb, self.improd_ref_emb)

            avg_prod = float(torch.mean(prod_sim))
            avg_impr = float(torch.mean(impr_sim))

            total = avg_prod + avg_impr
            if total == 0:
                return {"category": EmailCategory.PRODUTIVO, "score": 0.5}

            prod_score = avg_prod / total
            if prod_score >= 0.5:
                return {"category": EmailCategory.PRODUTIVO, "score": prod_score}
            else:
                return {"category": EmailCategory.IMPRODUTIVO, "score": 1 - prod_score}

        except Exception:
            return {"category": EmailCategory.PRODUTIVO, "score": 0.5}

    # -------------------------------------------------------------------------
    # COMBINAÇÃO FINAL
    # -------------------------------------------------------------------------
    def _combine_results(self, primary, sim, keywords):
        """Combina resultados dos 3 métodos em um score final."""
        weights = {"primary": 0.55, "similarity": 0.30, "keywords": 0.15}

        def as_prod_score(result):
            return result["score"] if result["category"] == EmailCategory.PRODUTIVO else (1 - result["score"])

        final_prod_score = (
            as_prod_score(primary) * weights["primary"]
            + as_prod_score(sim) * weights["similarity"]
            + keywords["productive_score"] * weights["keywords"]
        )

        if final_prod_score >= 0.5:
            return EmailCategory.PRODUTIVO, final_prod_score
        else:
            return EmailCategory.IMPRODUTIVO, 1 - final_prod_score

    # -------------------------------------------------------------------------
    # RESPOSTA PADRÃO
    # -------------------------------------------------------------------------
    def _default_response(self):
        """Resposta padrão caso algo falhe."""
        return {
            "category": EmailCategory.PRODUTIVO,
            "confidence": 0.5,
            "primary_model_score": 0.5,
            "similarity_score": 0.5,
            "keyword_score": 0.5,
            "detected_topics": [],
            "tokens_processed": 0
        }
