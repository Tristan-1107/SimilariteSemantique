# SimilariteSemantique

API FastAPI de calcul de similarite semantique entre phrases, avec :

- des metriques natives basees sur spaCy,
- une metrique `camembert` via `sentence-transformers`,
- un systeme de plugins charge automatiquement,
- un endpoint pour lister les metriques disponibles,
- un endpoint d'upload JSON pour traiter plusieurs paires de phrases.

## Installation

Depuis la racine du depot :

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirementsTests.txt
```

Le fichier `requirements.txt` inclut aussi les dependances necessaires au
plugin `bert_score` :

- `torch`
- `transformers`

Verification rapide des modeles spaCy :

```bash
python3 -c "import spacy; spacy.load('fr_core_news_md'); print('spaCy OK')"
python3 -c "import spacy; spacy.load('en_core_web_md'); print('spaCy EN OK')"
```

## Lancer l'API

```bash
python3 -m uvicorn app.main:app --reload
```

Documentation interactive :

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

Important :

- `http://127.0.0.1:8000/` ne sert pas de page web et renvoie `404`
- l'application expose une API, pas un frontend

## Endpoint principal

### `GET /metrics`

Retourne les metriques actuellement enregistrees dans l'API.

En cas d'erreur, l'API renvoie des erreurs structurees dans `detail` :

```json
{
  "detail": {
    "code": "unknown_metric",
    "message": "Métrique inconnue : super_metric_qui_nexiste_pas"
  }
}
```

### `POST /similarity`

Exemple de payload :

```json
{
  "phrase1": "chat noir",
  "phrase2": "chat blanc",
  "metrics": ["jaccard", "dice", "levenshtein", "spacy_vector", "camembert"],
  "language": "fr"
}
```

Metriques natives disponibles :

- `jaccard`
- `dice`
- `levenshtein`
- `spacy_vector`
- `camembert`

Des metriques plugin peuvent aussi etre disponibles selon le contenu de `plugins/metrics/`.

## Traitement batch par upload

### `POST /similarity/upload`

Cet endpoint attend un fichier JSON envoye en `multipart/form-data` sous le champ `file`.

Le contenu JSON supporte deux formats.

### Format objet recommande

```json
{
  "metrics": ["jaccard", "camembert"],
  "language": "fr",
  "pairs": [
    ["chat noir", "chat blanc"],
    ["bonjour", "salut"]
  ]
}
```

### Format liste legacy accepte

```json
[
  ["jaccard", "camembert"],
  ["chat noir", "chat blanc"],
  ["bonjour", "salut"]
]
```

Exemple `curl` :

```bash
curl -X POST "http://127.0.0.1:8000/similarity/upload?language=fr" \
  -F "file=@pairs.json;type=application/json"
```

Comportement :

- le fichier est traite,
- la reponse HTTP retourne les resultats,
- un fichier `result_<nom>.json` est aussi ecrit dans le dossier `data/`

Le dossier de sortie peut etre surcharge via la variable d'environnement `SIMILARITY_DATA_DIR`.

## Tests

Campagne recommande :

```bash
python3 -m pytest tests/testSchemas.py tests/testRegistry.py tests/testMetrics.py tests/testPlugins.py tests/testApi.py -q
```

Les fichiers de test existants peuvent aussi etre lances individuellement :

```bash
python3 -m tests.testApi
python3 -m tests.testMetrics
python3 -m tests.testRegistry
python3 -m tests.testSchemas
```

## Notes utiles

- la metrique `camembert` charge son modele au premier usage, donc le premier appel peut etre plus lent
- la metrique `bert_score` a maintenant ses dependances Python dans `requirements.txt`, mais ses modeles Hugging Face peuvent encore etre telecharges au premier appel
- le support anglais attend `en_core_web_md`, qui est maintenant installe avec les dependances du projet
- `bert_score` utilise desormais `bert_score_french` pour `fr` et `bert_score_english` pour `en`
- les plugins sont charges automatiquement au demarrage depuis `plugins/metrics/`
- les resultats batch ecrits dans `data/` sont ignores par Git
