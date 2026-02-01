# app/core/metrics.py
import spacy

# --- Chargement du modèle spaCy ---
# On tente de charger le modèle français "medium" qui contient les vecteurs.
# Si le modèle n'est pas trouvé, on charge un modèle vide pour éviter que l'API plante au démarrage.
try:
    nlp = spacy.load("fr_core_news_md")
except OSError:
    print("ATTENTION: Le modèle 'fr_core_news_md' n'est pas trouvé.")
    print("Veuillez l'installer via : pip install -r requirements.txt")
    nlp = spacy.blank("fr")


def spacy_preprocess(text):
    """
    Tokenisation avancée pour le Sprint 3.
    Transforme le texte en liste de lemmes (racines) en retirant
    la ponctuation et les mots vides (stop words).
    """
    # La syntaxe (text or "") gère le cas où text est None
    doc = nlp((text or "").lower())
    
    tokens = [
        token.lemma_ 
        for token in doc 
        if not token.is_stop and not token.is_punct and not token.is_space
    ]
    return tokens


# --- Fonctions Mathématiques (Jaccard, Dice, Levenshtein) ---

def jaccard_similarity(tokens1, tokens2):
    set1 = set(tokens1)
    set2 = set(tokens2)
    
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
        
    inter = set1.intersection(set2)
    union = set1.union(set2)
    return len(inter) / len(union)


def dice_similarity(tokens1, tokens2):
    set1 = set(tokens1)
    set2 = set(tokens2)

    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    inter = len(set1.intersection(set2))
    return (2 * inter) / (len(set1) + len(set2))


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
    # Sécurité pour éviter None sur len()
    s1 = s1 or ""
    s2 = s2 or ""
    
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1, s2)
    return 1 - (dist / max_len)


# --- Classes de Métriques ---

class MetricResult:
    def __init__(self, name, score, detail=None):
        self.name = name
        self.score = score
        self.detail = detail


class BaseMetric:
    name = None
    description = None

    def compute(self, phrase1, phrase2):
        raise NotImplementedError


class JaccardMetric(BaseMetric):
    name = "jaccard"
    description = "Jaccard sur lemmes (via spaCy) : intersection / union."

    def compute(self, phrase1, phrase2):
        # Utilisation du pré-traitement spaCy
        t1 = spacy_preprocess(phrase1)
        t2 = spacy_preprocess(phrase2)
        score = jaccard_similarity(t1, t2)
        return MetricResult(
            name=self.name,
            score=score,
            detail={"tokens1": t1, "tokens2": t2}
        )


class DiceMetric(BaseMetric):
    name = "dice"
    description = "Coefficient de Dice sur lemmes (via spaCy)."

    def compute(self, phrase1, phrase2):
        # Utilisation du pré-traitement spaCy
        t1 = spacy_preprocess(phrase1)
        t2 = spacy_preprocess(phrase2)
        score = dice_similarity(t1, t2)
        return MetricResult(
            name=self.name,
            score=score,
            detail={"tokens1": t1, "tokens2": t2}
        )


class LevenshteinMetric(BaseMetric):
    name = "levenshtein"
    description = "Distance d'édition normalisée (basée sur les caractères)."

    def compute(self, phrase1, phrase2):
        # Levenshtein travaille sur les chaînes brutes, pas les tokens
        score = levenshtein_similarity(phrase1, phrase2)
        return MetricResult(
            name=self.name,
            score=score,
            detail=None
        )


class SpacyVectorMetric(BaseMetric):
    name = "spacy_vector"
    description = "Similarité cosinus basée sur les vecteurs sémantiques (Word Embeddings)."

    def compute(self, phrase1, phrase2):
        # On traite les phrases complètes pour obtenir leur vecteur contextuel
        doc1 = nlp(phrase1 or "")
        doc2 = nlp(phrase2 or "")
        
        # spaCy gère le calcul du cosinus entre les vecteurs des deux docs
        # Note : Si un vecteur est vide, spaCy peut renvoyer 0.0 avec un warning
        score = doc1.similarity(doc2)
        
        return MetricResult(
            name=self.name,
            score=score,
            detail={
                "vector_size": doc1.vector.shape[0],
                "has_vector": doc1.has_vector and doc2.has_vector
            }
        )