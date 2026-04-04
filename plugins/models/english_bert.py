from dataclasses import dataclass
from typing import Any

from app.core.model_definition import BaseModelDefinition


@dataclass
class BertModelResource:
    model_name: str
    tokenizer: Any
    model: Any
    torch: Any


class BertScoreEnglishModelDefinition(BaseModelDefinition):
    name = "bert_score_english"
    description = "Modèle BERT anglais pour la métrique bert_score."

    def load(self) -> BertModelResource:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "Les dépendances 'transformers' et 'torch' sont requises "
                "pour utiliser la métrique 'bert_score'."
            ) from exc

        model_name = "bert-base-uncased"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.eval()

        return BertModelResource(
            model_name=model_name,
            tokenizer=tokenizer,
            model=model,
            torch=torch,
        )
