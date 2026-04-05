# SimilariteSemantique

API FastAPI de calcul de similarite semantique entre phrases, avec :

- des metriques natives basees sur spaCy,
- une metrique `camembert` via `sentence-transformers`,
- un systeme de plugins charge automatiquement,
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
- si l'IDE pointe vers `venv/bin/python` ou `/usr/bin/python3`, les metriques `camembert` et `bert_score` peuvent echouer faute de dependances.

Verification rapide du modele spaCy :

```bash
.venv/bin/python -c "import spacy; spacy.load('fr_core_news_md'); print('spaCy OK')"
```

## Lancer l'application

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interface web :

- `http://127.0.0.1:8000/`

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
- les plugins sont charges automatiquement au demarrage depuis `plugins/metrics/`
- les resultats batch ecrits dans `data/` sont ignores par Git

## Depannage des metriques ML

Si tu vois une erreur du type :

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

Si besoin, reinstalle-les dans `.venv` :

```bash
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Version statique GitHub Pages

Le depot contient maintenant une version statique du site dans `site/` :

- `site/index.html`
- `site/styles.css`

Cette version est adaptee a GitHub Pages : quand l'URL du site est ouverte, GitHub Pages sert automatiquement `index.html`.

Workflow ajoute :

- `.github/workflows/deploy-pages.yml`

Ce workflow publie uniquement le dossier `site/` vers GitHub Pages.

URL attendue pour ce depot :

- `https://tristan-1107.github.io/SimilariteSemantique/`

Important :

- GitHub Pages heberge seulement des fichiers statiques ;
- le backend FastAPI dans `app/` ne s'execute donc pas sur `github.io` ;
- pour avoir les calculs semantiques en ligne, il faudra heberger l'API sur un serveur separe puis connecter le site statique a cette API.

### Activer GitHub Pages

1. pousser les fichiers sur GitHub ;
2. ouvrir `Settings > Pages` dans le depot GitHub ;
3. dans `Build and deployment`, choisir `GitHub Actions` comme source ;
4. lancer ou laisser se lancer automatiquement le workflow `Deploy static site to GitHub Pages`.
