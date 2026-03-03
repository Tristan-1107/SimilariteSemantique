# plugins/metrics/overlap_metric.py
from app.core.metrics import BaseMetric, MetricResult


class WordOverlapMetric(BaseMetric):
    """
    Taux de mots en commun normalisé par la phrase la plus courte.
    Plus permissif que Jaccard : un mot commun sur 2 donne 0.5,
    même si les deux phrases ont des tailles très différentes.
    """
    name = "word_overlap"
    description = "Recouvrement de mots normalisé par la phrase la plus courte."

    def compute(self, phrase1, phrase2, context):
        t1 = set((phrase1 or "").lower().split())
        t2 = set((phrase2 or "").lower().split())

        if not t1 and not t2:
            return MetricResult(name=self.name, score=1.0)
        if not t1 or not t2:
            return MetricResult(name=self.name, score=0.0)

        common = len(t1 & t2)
        score = common / min(len(t1), len(t2))
        return MetricResult(name=self.name, score=round(score, 4))