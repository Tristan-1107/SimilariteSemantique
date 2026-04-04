import re
import string


try:
    import spacy as _spacy
except Exception:
    _spacy = None


_STOP_WORDS = {
    "a",
    "au",
    "aux",
    "de",
    "des",
    "du",
    "en",
    "et",
    "il",
    "je",
    "la",
    "le",
    "les",
    "sur",
    "un",
    "une",
}


class _FallbackToken:
    def __init__(self, text: str):
        self.text = text
        self.lemma_ = text.lower()
        self.is_space = not text.strip()
        self.is_punct = all(char in string.punctuation for char in text)
        self.is_stop = self.lemma_ in _STOP_WORDS


class _FallbackVector:
    shape = (0,)


class _FallbackDoc:
    def __init__(self, text: str):
        self._tokens = [_FallbackToken(token) for token in _tokenize(text)]
        self.vector = _FallbackVector()
        self.has_vector = False

    def __iter__(self):
        return iter(self._tokens)

    def similarity(self, other) -> float:
        left = {
            token.lemma_
            for token in self._tokens
            if not token.is_stop and not token.is_punct and not token.is_space
        }
        right = {
            token.lemma_
            for token in other
            if not token.is_stop and not token.is_punct and not token.is_space
        }

        if not left and not right:
            return 1.0
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)


class _FallbackPipeline:
    def __init__(self, code: str):
        self.code = code

    def __call__(self, text: str):
        return _FallbackDoc(text or "")


class _FallbackSpacy:
    @staticmethod
    def load(model_name: str):
        raise OSError(f"Le modèle spaCy '{model_name}' est indisponible dans le fallback.")

    @staticmethod
    def blank(code: str):
        return _FallbackPipeline(code)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+|[^\w\s]", text or "", flags=re.UNICODE)


spacy = _spacy or _FallbackSpacy()
