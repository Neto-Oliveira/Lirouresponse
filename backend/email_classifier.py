# email_classifier.py
import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import logging
import re
from typing import Dict, Any

from text_processor import TextProcessor
from models import EmailCategory

logger = logging.getLogger(__name__)


class EmailClassifier:
    """Classificador de emails PRODUTIVO vs IMPRODUTIVO."""

    def __init__(self, use_ml_models: bool = True):
        self.text_processor = TextProcessor()
        self.use_ml_models = use_ml_models
        self.primary_classifier = None
        self.sentence_model = None
        self.prod_ref_emb = None
        self.improd_ref_emb = None
        
        if self.use_ml_models:
            self._setup_ml_models()
        else:
            logger.info("Modo sem ML ativado - usando apenas regras baseadas em palavras-chave")

    def _setup_ml_models(self):
        """Carrega modelos de ML necessários."""
        try:
            logger.info("Carregando modelo BERT para análise de sentimento...")
            self.primary_classifier = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                tokenizer="nlptown/bert-base-multilingual-uncased-sentiment",
                device=-1
            )

            logger.info("Carregando Sentence Transformer para similaridade semântica...")
            self.sentence_model = SentenceTransformer(
                "paraphrase-multilingual-MiniLM-L12-v2"
            )

            productive_references = [
                "Preciso de ajuda com um problema no sistema",
                "Solicito suporte técnico para resolver um erro",
                "Gostaria de saber o status do meu pedido",
                "Estou com dificuldade para acessar minha conta",
                "Preciso de informações sobre minha transação",
                "Solicito reembolso de um pagamento realizado",
                "Reporto um defeito na aplicação",
                "Preciso de assistência urgente"
            ]

            improductive_references = [
                "Agradeço pelo atendimento de ontem",
                "Parabéns pelo aniversário da empresa",
                "Desejo um feliz natal para toda a equipe",
                "Agradeço a todos pelo trabalho",
                "Bom fim de semana para todos",
                "Muito obrigado pela ajuda",
                "Feliz ano novo para a equipe",
                "Cumprimentos a todos os colaboradores"
            ]

            logger.info("Pré-processando referências para similaridade semântica...")
            with torch.no_grad():
                self.prod_ref_emb = self.sentence_model.encode(
                    productive_references,
                    convert_to_tensor=True
                )
                self.improd_ref_emb = self.sentence_model.encode(
                    improductive_references,
                    convert_to_tensor=True
                )

            logger.info("✅ Modelos de ML carregados com sucesso.")

        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelos ML: {e}")
            self.use_ml_models = False
            logger.info("🔄 Fallback para modo sem ML (apenas regras)")

    def classify(self, text: str) -> Dict[str, Any]:
        """Classifica um email como PRODUTIVO ou IMPRODUTIVO."""
        if not text or not isinstance(text, str):
            return self._default_response()

        try:
            processed_text = self.text_processor.preprocess(text)
            if not processed_text.strip():
                return self._default_response()

            if self.use_ml_models and self.primary_classifier:
                # Classificação com ML
                logger.debug("Usando modelos ML para classificação")
                primary_result = self._primary_classification(processed_text)
                similarity_result = self._semantic_similarity(processed_text)
                keyword_features = self.text_processor.extract_keyword_features(text)
                
                final_category, confidence = self._combine_ml_results(
                    primary_result,
                    similarity_result,
                    keyword_features
                )
            else:
                # Classificação baseada apenas em regras
                logger.debug("Usando regras baseadas para classificação")
                final_category, confidence = self._rule_based_classification(text)

            topics = self.text_processor.detect_topics(text)

            return {
                "category": final_category,
                "confidence": confidence,
                "primary_model_score": confidence,
                "similarity_score": 0.7,
                "keyword_score": confidence,
                "detected_topics": topics,
                "tokens_processed": len(processed_text.split())
            }

        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return self._default_response()

    def _primary_classification(self, text: str) -> Dict[str, Any]:
        """Classificação usando sentimento como proxy de produtividade."""
        try:
            truncated = text[:512]
            result = self.primary_classifier(truncated)[0]

            sentiment_match = re.search(r'\d+', result["label"])
            sentiment = int(sentiment_match.group()) if sentiment_match else 3

            if sentiment <= 2:
                category = EmailCategory.PRODUTIVO
                score = min(1.0, 0.7 + (2 - sentiment) * 0.15)
            else:
                category = EmailCategory.IMPRODUTIVO
                score = min(1.0, 0.6 + (sentiment - 3) * 0.15)

            return {"category": category, "score": float(score)}

        except Exception as e:
            logger.error(f"Erro na classificação primária: {e}")
            return {"category": EmailCategory.PRODUTIVO, "score": 0.5}

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

        except Exception as e:
            logger.error(f"Erro na similaridade semântica: {e}")
            return {"category": EmailCategory.PRODUTIVO, "score": 0.5}

    def _combine_ml_results(self, primary, sim, keywords):
        """Combina resultados dos 3 métodos em um score final."""
        weights = {"primary": 0.55, "similarity": 0.30, "keywords": 0.15}

        def as_prod_score(result):
            return result["score"] if result["category"] == EmailCategory.PRODUTIVO else (1 - result["score"])

        final_prod_score = (
            as_prod_score(primary) * weights["primary"] +
            as_prod_score(sim) * weights["similarity"] +
            keywords["productive_score"] * weights["keywords"]
        )

        if final_prod_score >= 0.5:
            return EmailCategory.PRODUTIVO, final_prod_score
        else:
            return EmailCategory.IMPRODUTIVO, 1 - final_prod_score

    def _rule_based_classification(self, text: str):
        """Classificação baseada em regras e palavras-chave."""
        text_lower = text.lower()
        
        productive_keywords = {
            'problema': 2.0, 'erro': 2.0, 'suporte': 1.8, 'solicitação': 1.8, 
            'pedido': 1.8, 'ajuda': 1.7, 'urgente': 2.2, 'reembolso': 2.0,
            'pagamento': 1.9, 'transação': 1.8, 'defeito': 2.0, 'falha': 2.0,
            'não funciona': 2.1, 'status': 1.6, 'andamento': 1.6, 'protocolo': 1.5,
            'chamado': 1.5, 'suporte técnico': 1.9, 'resolver': 1.7, 'conserto': 1.8
        }
        
        improductive_keywords = {
            'obrigado': 3.0, 'agradeço': 3.0, 'grato': 2.8, 'obrigada': 3.0,
            'parabéns': 2.5, 'feliz': 2.0, 'natal': 2.2, 'ano novo': 2.2, 
            'cumprimentos': 2.0, 'saudações': 1.8, 'bom dia': 1.6, 'boa tarde': 1.6
        }
        
        productive_score = sum(
            weight for word, weight in productive_keywords.items() 
            if word in text_lower
        )
        
        improductive_score = sum(
            weight for word, weight in improductive_keywords.items() 
            if word in text_lower
        )

        # Lógica corrigida: agradecimentos são improdutivos
        if improductive_score > productive_score:
            confidence = min(0.95, 0.7 + improductive_score * 0.05)
            return EmailCategory.IMPRODUTIVO, confidence
        elif productive_score > 0:
            confidence = min(0.95, 0.6 + productive_score * 0.06)
            return EmailCategory.PRODUTIVO, confidence
        else:
            # Fallback
            if any(word in text_lower for word in ['?', 'problema', 'ajuda', 'solicito', 'preciso']):
                return EmailCategory.PRODUTIVO, 0.6
            else:
                return EmailCategory.IMPRODUTIVO, 0.6

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