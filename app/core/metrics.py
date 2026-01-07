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

# Definition de la mesure Dice

def dice_similarity(tokens1, tokens2):
    set1 = set(tokens1)
    set2 = set(tokens2)

    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    inter = len(set1.intersection(set2))
    return (2 * inter) / (len(set1) + len(set2))


class DiceMetric(BaseMetric):
    name = "dice"
    description = "Coefficient de Dice basé sur les ensembles de mots."

    def compute(self, phrase1, phrase2):
        t1 = simple_tokenize(phrase1)
        t2 = simple_tokenize(phrase2)
        score = dice_similarity(t1, t2)
        return MetricResult(
            name=self.name,
            score=score,
            detail={"tokens1": t1, "tokens2": t2}
        )

# Definition de la mesure Levenshtein

def levenshtein_distance(s1, s2):
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            insert = curr[j] + 1
            delete = prev[j + 1] + 1
            replace = prev[j] + (c1 != c2)
            curr.append(min(insert, delete, replace))
        prev = curr
    return prev[-1]


def levenshtein_similarity(s1, s2):
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1, s2)
    return 1 - (dist / max_len)


class LevenshteinMetric(BaseMetric):
    name = "levenshtein"
    description = "Similarité Levenshtein normalisée entre deux chaînes."

    def compute(self, phrase1, phrase2):
        score = levenshtein_similarity(phrase1, phrase2)
        return MetricResult(
            name=self.name,
            score=score,
            detail=None
        )
