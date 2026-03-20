# plugins/metrics/length_ratio.py
from app.core.metrics import BaseMetric, MetricResult


class LengthRatioMetric(BaseMetric):
    """
    Ratio de longueur entre deux phrases (min / max).
    1.0 si mêmes longueurs, proche de 0 si très déséquilibrées.
    """
    name = "length_ratio"
    description = "Ratio de longueur (min/max)."

    def compute(self, phrase1, phrase2, context):
        s1 = (phrase1 or "")
        s2 = (phrase2 or "")

        a = len(s1)
        b = len(s2)

        if a == 0 and b == 0:
            return MetricResult(name=self.name, score=1.0)
        if a == 0 or b == 0:
            return MetricResult(name=self.name, score=0.0)

        score = min(a, b) / max(a, b)
        return MetricResult(name=self.name, score=round(score, 4))