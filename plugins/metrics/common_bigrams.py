from app.core.metrics import BaseMetric, MetricResult

"""
Métrique basée sur les bigrammes de mots.

Principe :
Chaque phrase est transformée en liste de bigrammes (paires de mots consécutifs).

Exemple :
    "le chat dort"
    → ("le", "chat"), ("chat", "dort")

On compare ensuite les ensembles de bigrammes des deux phrases en utilisant
l'indice de Jaccard :

    score = intersection / union

où :
- intersection = nombre de bigrammes communs
- union = nombre total de bigrammes distincts

Comportement :
- Phrases identiques → score = 1.0
- Aucun bigramme en commun → score = 0.0
- Si les deux phrases ne contiennent pas de bigrammes → score = 1.0
- Si une seule phrase contient des bigrammes → score = 0.0

Cette métrique permet de mesurer la similarité locale de structure
entre deux phrases.
"""

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