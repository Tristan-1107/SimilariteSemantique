# plugins/metrics/prefix.py
from app.core.metrics import BaseMetric, MetricResult


class PrefixMetric(BaseMetric):
    """
    Longueur du plus long préfixe commun, normalisée par la plus courte phrase.
    1.0 si identiques, 0.0 si aucun préfixe commun.
    """
    name = "prefix"
    description = "Préfixe commun normalisé."

    def compute(self, phrase1, phrase2, context):
        s1 = (phrase1 or "")
        s2 = (phrase2 or "")

        if s1 == "" and s2 == "":
            return MetricResult(name=self.name, score=1.0)
        if s1 == "" or s2 == "":
            return MetricResult(name=self.name, score=0.0)

        n = min(len(s1), len(s2))
        i = 0
        while i < n and s1[i] == s2[i]:
            i += 1

        score = i / n if n > 0 else 0.0
        return MetricResult(name=self.name, score=round(score, 4))