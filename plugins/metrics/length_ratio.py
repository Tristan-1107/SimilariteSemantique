from app.core.metrics import BaseMetric, MetricResult

"""
Métrique basée sur la longueur des deux phrases.

Principe :
On compare la longueur des deux chaînes de caractères et on calcule
le ratio entre la plus courte et la plus longue :

    score = min(len(s1), len(s2)) / max(len(s1), len(s2))

Comportement :
- Si les deux phrases ont la même longueur → score = 1.0
- Si une phrase est beaucoup plus longue que l'autre → score proche de 0
- Si les deux phrases sont vides → score = 1.0
- Si une seule phrase est vide → score = 0.0

Cette métrique ne mesure pas le sens des phrases mais uniquement
leur similarité structurelle en termes de taille.
"""

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