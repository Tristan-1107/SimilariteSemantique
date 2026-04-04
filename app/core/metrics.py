from app.core.model_registry import CAMEMBERT_MODEL_NAME, model_registry


def spacy_preprocess(text: str, pipeline) -> list[str]:
    """
    Tokenisation avancée.
    Transforme le texte en liste de lemmes en retirant
    la ponctuation et les mots vides.
    """
    doc = pipeline((text or "").lower())
    return [
        token.lemma_
        for token in doc
        if not token.is_stop and not token.is_punct and not token.is_space
    ]


def jaccard_similarity(tokens1, tokens2):
    set1, set2 = set(tokens1), set(tokens2)
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)


def dice_similarity(tokens1, tokens2):
    set1, set2 = set(tokens1), set(tokens2)
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    return (2 * len(set1 & set2)) / (len(set1) + len(set2))


def levenshtein_distance(s1, s2):
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def levenshtein_similarity(s1, s2):
    s1, s2 = s1 or "", s2 or ""
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    return 1 - levenshtein_distance(s1, s2) / max_len


class MetricResult:
    def __init__(self, name, score, detail=None):
        self.name = name
        self.score = score
        self.detail = detail


class BaseMetric:
    name: str = None
    description: str = None

    def compute(self, phrase1: str, phrase2: str, context) -> MetricResult:
        raise NotImplementedError


class JaccardMetric(BaseMetric):
    name = "jaccard"
    description = "Jaccard sur lemmes (via spaCy) : intersection / union."

    def compute(self, phrase1, phrase2, context):
        t1 = spacy_preprocess(phrase1, context.pipeline)
        t2 = spacy_preprocess(phrase2, context.pipeline)
        return MetricResult(
            name=self.name,
            score=jaccard_similarity(t1, t2),
            detail={"tokens1": t1, "tokens2": t2},
        )


class DiceMetric(BaseMetric):
    name = "dice"
    description = "Coefficient de Dice sur lemmes (via spaCy)."

    def compute(self, phrase1, phrase2, context):
        t1 = spacy_preprocess(phrase1, context.pipeline)
        t2 = spacy_preprocess(phrase2, context.pipeline)
        return MetricResult(
            name=self.name,
            score=dice_similarity(t1, t2),
            detail={"tokens1": t1, "tokens2": t2},
        )


class LevenshteinMetric(BaseMetric):
    name = "levenshtein"
    description = "Distance d'édition normalisée (basée sur les caractères)."

    def compute(self, phrase1, phrase2, context):
        return MetricResult(
            name=self.name,
            score=levenshtein_similarity(phrase1, phrase2),
        )


class SpacyVectorMetric(BaseMetric):
    name = "spacy_vector"
    description = "Similarité cosinus basée sur les vecteurs sémantiques (Word Embeddings)."

    def compute(self, phrase1, phrase2, context):
        doc1 = context.pipeline(phrase1 or "")
        doc2 = context.pipeline(phrase2 or "")
        return MetricResult(
            name=self.name,
            score=doc1.similarity(doc2),
            detail={
                "vector_size": doc1.vector.shape[0],
                "has_vector": doc1.has_vector and doc2.has_vector,
            },
        )


class CamembertMetric(BaseMetric):
    name = "camembert"
    description = "Similarité sémantique via Sentence-BERT/CamemBERT compatible."

    def compute(self, phrase1, phrase2, context):
        resource = model_registry.get(CAMEMBERT_MODEL_NAME)
        if resource is None:
            raise RuntimeError(
                f"Le modèle '{CAMEMBERT_MODEL_NAME}' n'est pas enregistré."
            )

        embeddings = resource.encoder.encode(
            [phrase1 or "", phrase2 or ""],
            convert_to_tensor=True,
        )
        score = resource.util.cos_sim(embeddings[0], embeddings[1]).item()
        score = max(0.0, min(1.0, float(score)))

        vector_dim = None
        shape = getattr(embeddings, "shape", None)
        if shape and len(shape) > 1:
            vector_dim = int(shape[1])

        return MetricResult(
            name=self.name,
            score=score,
            detail={
                "model": getattr(resource, "model_name", CAMEMBERT_MODEL_NAME),
                "vector_dim": vector_dim,
            },
        )
