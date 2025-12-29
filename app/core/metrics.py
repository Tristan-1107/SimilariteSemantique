# app/core/metrics.py

def simple_tokenize(text):
    """
    Tokenisation minimale pour Sprint 2.
    (On pourra remplacer par spaCy plus tard.)
    """
    text = (text or "").strip().lower()
    if not text:
        return []
    return text.split()


def jaccard_similarity(tokens1, tokens2):
    """
    J(A,B) = |A ∩ B| / |A ∪ B|, avec A,B ensembles de tokens.
    """
    set1 = set(tokens1)
    set2 = set(tokens2)

    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    inter = set1.intersection(set2)
    union = set1.union(set2)
    return len(inter) / len(union)


class MetricResult:
    def __init__(self, name, score, detail=None):
        self.name = name
        self.score = score
        self.detail = detail


class BaseMetric:
    """
    Contrat commun (minimal) pour une métrique.
    """
    name = None
    description = None

    def compute(self, phrase1, phrase2):
        raise NotImplementedError


class JaccardMetric(BaseMetric):
    name = "jaccard"
    description = "Jaccard sur ensembles de mots (tokenisation simple)."

    def compute(self, phrase1, phrase2):
        t1 = simple_tokenize(phrase1)
        t2 = simple_tokenize(phrase2)
        score = jaccard_similarity(t1, t2)
        return MetricResult(
            name=self.name,
            score=score,
            detail={"tokens1": t1, "tokens2": t2}
        )
