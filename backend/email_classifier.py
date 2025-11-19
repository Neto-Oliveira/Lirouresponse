import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import logging
import re
from typing import Dict, Any
import gc

from text_processor import TextProcessor
from models import EmailCategory

logger = logging.getLogger(__name__)

class EmailClassifier:
    """Classificador otimizado para produção"""

    def __init__(self, use_ml_models: bool = True):
        self.text_processor = TextProcessor()
        self.use_ml_models = use_ml_models
        self.primary_classifier = None
        self.sentence_model = None
        self.prod_ref_emb = None
        self.improd_ref_emb = None
        
        if self.use_ml_models:
            self._setup_optimized_models()
        else:
            logger.info("🔧 Modo sem ML ativado - usando regras baseadas")

    def _setup_optimized_models(self):
        """Carrega modelos otimizados para baixa memória"""
        try:
            logger.info("🔄 Carregando modelos otimizados...")
            
            # Modelo mais leve para sentiment analysis
            self.primary_classifier = pipeline(
                "text-classification",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=-1,
                torch_dtype=torch.float32
            )

            # Sentence transformer menor
            self.sentence_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                device='cpu'
            )

            # Referências otimizadas
            productive_references = [
                "problema erro sistema suporte técnico ajuda",
                "solicitação pedido status andamento protocolo",
                "reembolso pagamento transação defeito falha",
                "urgente crítico não funciona quebrado"
            ]

            improductive_references = [
                "obrigado agradeço parabéns feliz natal",
                "cumprimentos saudações bom dia boa tarde",
                "ano novo feriado fim de semana comemoração",
                "elogios felicitações votos sucesso"
            ]

            # Embeddings pré-computados
            with torch.no_grad():
                self.prod_ref_emb = self.sentence_model.encode(
                    productive_references,
                    convert_to_tensor=True
                )
                self.improd_ref_emb = self.sentence_model.encode(
                    improductive_references,
                    convert_to_tensor=True
                )

            logger.info("✅ Modelos otimizados carregados com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelos: {e}")
            self.use_ml_models = False
            logger.info("🔄 Fallback para modo sem ML")

    def classify(self, text: str) -> Dict[str, Any]:
        """Classificação otimizada"""
        if not text or not isinstance(text, str):
            return self._default_response()

        try:
            processed_text = self.text_processor.preprocess(text)
            if not processed_text.strip():
                return self._default_response()

            if self.use_ml_models and self.primary_classifier:
                # Classificação com ML otimizada
                primary_result = self._primary_classification(processed_text)
                similarity_result = self._semantic_similarity(processed_text)
                keyword_features = self.text_processor.extract_keyword_features(text)
                
                final_category, confidence = self._combine_ml_results(
                    primary_result,
                    similarity_result,
                    keyword_features,
                    text  # ⬅️ AGORA PASSAMOS O TEXTO ORIGINAL
                )
            else:
                # Classificação baseada em regras
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
        """Classificação usando modelo leve"""
        try:
            truncated = text[:512]
            result = self.primary_classifier(truncated)[0]

            # Mapear sentimentos do modelo leve
            sentiment_map = {"negative": 1, "neutral": 2, "positive": 3}
            sentiment = sentiment_map.get(result["label"], 2)
            prob = result.get("score", 0.5)

            if sentiment <= 2:
                category = EmailCategory.PRODUTIVO
                score = min(1.0, 0.7 + (2 - sentiment) * 0.15)
            else:
                category = EmailCategory.IMPRODUTIVO
                score = min(1.0, 0.6 + (sentiment - 2) * 0.15)

            return {"category": category, "score": float(score)}

        except Exception as e:
            logger.error(f"Erro classificação primária: {e}")
            return {"category": EmailCategory.PRODUTIVO, "score": 0.5}

    def _semantic_similarity(self, text: str) -> Dict[str, Any]:
        """Similaridade semântica otimizada"""
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
            logger.error(f"Erro similaridade: {e}")
            return {"category": EmailCategory.PRODUTIVO, "score": 0.5}

    def _combine_ml_results(self, primary, sim, keywords, original_text):
        """Combina resultados dos métodos com pesos ajustados"""
        
        # AUMENTAR peso dos keywords para agradecimentos
        weights = {"primary": 0.45, "similarity": 0.25, "keywords": 0.30}  # ⬅️ Ajustado
        
        def as_prod_score(result):
            return result["score"] if result["category"] == EmailCategory.PRODUTIVO else (1 - result["score"])

        final_prod_score = (
            as_prod_score(primary) * weights["primary"] +
            as_prod_score(sim) * weights["similarity"] +
            keywords["productive_score"] * weights["keywords"]
        )

        # REGRA ESPECIAL para agradecimentos
        text_lower = original_text.lower()
        if any(word in text_lower for word in ['obrigado', 'agradeço', 'grato', 'obrigada']):
            final_prod_score -= 0.3  # Penaliza score produtivo
        
        # Garantir que o score fique entre 0 e 1
        final_prod_score = max(0.0, min(1.0, final_prod_score))
        
        if final_prod_score >= 0.5:
            return EmailCategory.PRODUTIVO, final_prod_score
        else:
            return EmailCategory.IMPRODUTIVO, 1 - final_prod_score

    def _rule_based_classification(self, text: str):
        """Classificação baseada em regras"""
        return self.text_processor.extract_keyword_features(text)

    def _default_response(self):
        return {
            "category": EmailCategory.PRODUTIVO,
            "confidence": 0.5,
            "primary_model_score": 0.5,
            "similarity_score": 0.5,
            "keyword_score": 0.5,
            "detected_topics": [],
            "tokens_processed": 0
        }

    def cleanup(self):
        """Limpeza de memória"""
        if hasattr(self, 'sentence_model'):
            del self.sentence_model
        if hasattr(self, 'primary_classifier'):
            del self.primary_classifier
            
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()