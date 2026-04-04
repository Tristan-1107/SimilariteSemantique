from app.core.metrics import BaseMetric, MetricResult
from app.core.model_registry import model_registry


DEFAULT_BERT_SCORE_MODEL = "bert_score_english"


class BertScoreMetric(BaseMetric):
    name = "bert_score"
    description = "BERTScore token-level avec alignement max et score F1."

    def compute(self, phrase1, phrase2, context):
        text1 = phrase1 or ""
        text2 = phrase2 or ""

        if text1 == "" and text2 == "":
            return MetricResult(
                name=self.name,
                score=1.0,
                detail={
                    "precision": 1.0,
                    "recall": 1.0,
                    "f1": 1.0,
                    "model": self._resolve_model_name(context),
                    "token_count_1": 0,
                    "token_count_2": 0,
                },
            )

        if text1 == "" or text2 == "":
            return MetricResult(
                name=self.name,
                score=0.0,
                detail={
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "model": self._resolve_model_name(context),
                    "token_count_1": 0 if text1 == "" else None,
                    "token_count_2": 0 if text2 == "" else None,
                },
            )

        model_name = self._resolve_model_name(context)
        resource = model_registry.get(model_name)
        if resource is None:
            raise RuntimeError(f"Le modèle '{model_name}' n'est pas enregistré.")

        embeddings1 = self._extract_token_embeddings(text1, resource)
        embeddings2 = self._extract_token_embeddings(text2, resource)

        count1 = int(embeddings1.shape[0])
        count2 = int(embeddings2.shape[0])

        if count1 == 0 and count2 == 0:
            precision = recall = f1 = 1.0
        elif count1 == 0 or count2 == 0:
            precision = recall = f1 = 0.0
        else:
            similarity_matrix = embeddings1 @ embeddings2.T
            precision = float(similarity_matrix.max(dim=1).values.mean().item())
            recall = float(similarity_matrix.max(dim=0).values.mean().item())
            precision = self._clamp_score(precision)
            recall = self._clamp_score(recall)
            f1 = 0.0 if (precision + recall) == 0 else (2 * precision * recall) / (precision + recall)
            f1 = self._clamp_score(f1)

        return MetricResult(
            name=self.name,
            score=f1,
            detail={
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "model": getattr(resource, "model_name", model_name),
                "token_count_1": count1,
                "token_count_2": count2,
            },
        )

    @staticmethod
    def _resolve_model_name(context) -> str:
        configured_model = getattr(context.config, "embedding_model", None)
        if configured_model and model_registry.get_definition(configured_model):
            return configured_model
        return DEFAULT_BERT_SCORE_MODEL

    @staticmethod
    def _extract_token_embeddings(text, resource):
        encoded = resource.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            return_special_tokens_mask=True,
        )

        with resource.torch.no_grad():
            outputs = resource.model(**encoded)

        embeddings = outputs.last_hidden_state[0]
        attention_mask = encoded["attention_mask"][0].bool()
        special_tokens_mask = encoded["special_tokens_mask"][0].bool()
        keep_mask = attention_mask & ~special_tokens_mask
        filtered = embeddings[keep_mask]

        if filtered.shape[0] == 0:
            return filtered

        return resource.torch.nn.functional.normalize(filtered, p=2, dim=1)

    @staticmethod
    def _clamp_score(score: float) -> float:
        return max(0.0, min(1.0, float(score)))
