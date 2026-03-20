# plugins/metrics/common_bigrams.py
from app.core.metrics import BaseMetric, MetricResult


class CommonBigramsMetric(BaseMetric):
    """
    Similarité Jaccard sur bigrammes de mots.
    Exemple: "le chat dort" -> ("le","chat"), ("chat","dort")
    """
    name = "common_bigrams"
    description = "Jaccard sur bigrammes de mots."

    def compute(self, phrase1, phrase2, context):
        def bigrams(text: str):
            tokens = [t for t in (text or "").lower().split() if t]
            if len(tokens) < 2:
                return set()
            return set(zip(tokens, tokens[1:]))

        b1 = bigrams(phrase1)
        b2 = bigrams(phrase2)

        if not b1 and not b2:
            return MetricResult(name=self.name, score=1.0)
        if not b1 or not b2:
            return MetricResult(name=self.name, score=0.0)

        inter = len(b1 & b2)
        union = len(b1 | b2)
        score = inter / union if union else 0.0
        return MetricResult(name=self.name, score=round(score, 4))