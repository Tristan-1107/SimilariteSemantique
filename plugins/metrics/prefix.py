from app.core.metrics import BaseMetric, MetricResult

"""
Métrique basée sur le plus long préfixe commun.

Principe :
On parcourt les deux phrases caractère par caractère depuis le début
et on mesure combien de caractères consécutifs sont identiques.

Exemple :
    "bonjour monde"
    "bonjour toi"

Le préfixe commun est "bonjour " → score élevé.

Le score est ensuite normalisé par la longueur de la phrase la plus courte :

    score = longueur_prefixe_commun / longueur_phrase_plus_courte

Comportement :
- Phrases identiques → score = 1.0
- Aucun préfixe commun → score = 0.0
- Deux phrases vides → score = 1.0
- Une phrase vide → score = 0.0

Cette métrique est utile pour détecter des phrases qui commencent
de manière similaire.
"""

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