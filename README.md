# SimilariteSemantique

API FastAPI de calcul de similarite semantique entre phrases, avec :

- des metriques natives basees sur spaCy,
- une metrique `camembert` via `sentence-transformers`,
- un systeme de plugins charge automatiquement,
- un endpoint pour lister les metriques disponibles,
- un endpoint d'upload JSON pour traiter plusieurs paires de phrases,
- une interface web integree pour utiliser le service depuis un navigateur.

## Installation

Depuis la racine du depot :

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirementsTests.txt
```

Important :

- utiliser ensuite **le meme environnement** pour lancer l'application et les tests ;
- dans ce depot, l'environnement attendu est `.venv/` ;
- si ton IDE pointe vers `venv/bin/python` ou `/usr/bin/python3`, les metriques `camembert` et `bert_score` peuvent echouer faute de dependances.

Le fichier `requirements.txt` inclut aussi les dependances necessaires au
plugin `bert_score` :

- `torch`
- `transformers`

Verification rapide des modeles spaCy :

```bash
.venv/bin/python -c "import spacy; spacy.load('fr_core_news_md'); print('spaCy OK')"
.venv/bin/python -c "import spacy; spacy.load('en_core_web_md'); print('spaCy EN OK')"
```

## Lancer l'application

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Lancer avec Docker

Construction de l'image :

```bash
sudo docker build -t similarite-semantique .
```

Lancement du conteneur :

```bash
sudo docker run --rm -p 8000:8000 similarite-semantique
```

Interface web :

- http://127.0.0.1:8000/

Documentation interactive :

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

Important :

- `http://127.0.0.1:8000/` sert l'interface web
- pour un acces depuis une autre machine du meme reseau, utiliser `http://<ip_machine>:8000/`
- l'API JSON reste disponible en parallele

## Interface web

La page d'accueil permet :

- de comparer deux phrases avec selection des metriques et de la langue,
- d'envoyer un fichier JSON batch,
- d'afficher les resultats directement dans la page,
- de telecharger le fichier `result_<nom>.json` genere apres un batch.

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
.venv/bin/python -m pytest tests/testSchemas.py tests/testRegistry.py tests/testMetrics.py tests/testPlugins.py tests/testApi.py tests/testWeb.py -q
```

Les fichiers de test existants peuvent aussi etre lances individuellement :

```bash
.venv/bin/python -m tests.testApi
.venv/bin/python -m tests.testMetrics
.venv/bin/python -m tests.testRegistry
.venv/bin/python -m tests.testSchemas
.venv/bin/python -m pytest tests/testWeb.py -q
```

## Notes utiles

- la metrique `camembert` charge son modele au premier usage, donc le premier appel peut etre plus lent
- la metrique `bert_score` a maintenant ses dependances Python dans `requirements.txt`, mais ses modeles Hugging Face peuvent encore etre telecharges au premier appel
- le support anglais attend `en_core_web_md`, qui est maintenant installe avec les dependances du projet
- `bert_score` utilise desormais `bert_score_french` pour `fr` et `bert_score_english` pour `en`
- les plugins sont charges automatiquement au demarrage depuis `plugins/metrics/`
- les resultats batch ecrits dans `data/` sont ignores par Git

## Depannage des metriques ML

Si il y a une erreur du type :

- `La dépendance 'sentence-transformers' est absente`
- `Les dépendances 'transformers' et 'torch' sont requises`

alors le probleme vient presque toujours de l'interpreteur Python utilise au lancement.

Diagnostic rapide :

```bash
.venv/bin/python -m pip show sentence-transformers torch transformers
venv/bin/python -m pip show sentence-transformers torch transformers
python3 -m pip show sentence-transformers torch transformers
```

Sur ce depot, les dependances ML sont attendues dans `.venv`, pas dans `venv` ni dans le Python systeme.

Si besoin, reinstallez-les dans `.venv` :

```bash
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```
