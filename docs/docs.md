# Fonctionnement exact du projet `SimilariteSemantique`

## 1. Objet du document

Ce document decrit l'etat reel du projet apres integration :

- du systeme de plugins existant,
- de la metrique `camembert`,
- de l'endpoint d'upload JSON batch,
- du service de traitement en lot.

L'objectif est de documenter le comportement concret du code actuel, pas seulement l'intention initiale.

## 2. Ce que fait aujourd'hui l'application

Le projet expose une API FastAPI qui sait :

- comparer deux phrases via `POST /similarity`,
- lister les langues supportees via `GET /languages`,
- traiter un fichier JSON contenant plusieurs couples de phrases via `POST /similarity/upload`.

Le moteur combine :

- des metriques natives basees sur spaCy,
- une metrique `camembert` basee sur `sentence-transformers`,
- des metriques plugin chargees automatiquement depuis `plugins/metrics/`.

## 3. Architecture actuelle

### 3.1 Dossiers utiles au runtime

| Chemin | Role exact |
| --- | --- |
| `app/main.py` | Cree l'application FastAPI, monte le routeur et charge les plugins au demarrage. |
| `app/api/endpoints.py` | Definit les endpoints `/languages`, `/similarity` et `/similarity/upload`. |
| `app/models/schemas.py` | Definit les schemas Pydantic de l'API. |
| `app/core/metrics.py` | Contient les metriques natives, dont `camembert`, et le chargement lazy du modele BERT. |
| `app/core/registry.py` | Contient le registre global des metriques. |
| `app/core/plugin_loader.py` | Charge dynamiquement les plugins depuis `plugins/metrics/` avec resolution stable du chemin. |
| `app/core/language_manager.py` | Gere les langues, le chargement spaCy et le cache des pipelines. |
| `app/core/language_config.py` | Structure declarative d'une langue supportee. |
| `app/services/processor.py` | Traite les payloads batch et calcule les scores pour plusieurs couples. |
| `plugins/metrics/*.py` | Metriques plugin chargees au demarrage. |

### 3.2 Dossiers utiles au developpement

| Chemin | Role exact |
| --- | --- |
| `tests/` | Tests unitaires et d'integration. |
| `docs/` | Documentation technique du projet. |
| `README.md` | Guide d'utilisation rapide. |

### 3.3 Dossiers et fichiers generes localement

| Chemin | Observation |
| --- | --- |
| `.venv/` | Environnement virtuel local. Ignore par Git. |
| `venv/` | Ancien environnement local. Ignore par Git. |
| `source/` | Ancien environnement local. Ignore par Git. |
| `data/` | Resultats generes par `/similarity/upload`. Ignore par Git. |

## 4. Sequence de demarrage

### 4.1 Import de `app.main`

Quand on lance :

```bash
python3 -m uvicorn app.main:app --reload
```

le module `app.main` :

1. cree l'objet `FastAPI`,
2. inclut le routeur de `app.api.endpoints`,
3. importe `language_manager`,
4. importe `load_plugins`,
5. execute `load_plugins("plugins/metrics")`.

### 4.2 Initialisation des langues

Au chargement de `app/core/language_manager.py` :

- une instance globale `language_manager` est creee,
- la langue francaise `fr` est enregistree,
- le modele spaCy cible est `fr_core_news_md`.

Le champ `embedding_model="camembert-base"` existe dans la configuration, mais il reste purement informatif. Le vrai chargement BERT se fait dans `app/core/metrics.py`.

### 4.3 Initialisation du registre

Au chargement de `app/core/registry.py`, les metriques natives suivantes sont enregistrees :

- `jaccard`
- `dice`
- `levenshtein`
- `spacy_vector`
- `camembert`

Ensuite, `app/main.py` charge les plugins presents dans `plugins/metrics/`.

### 4.4 Chargement des plugins

Le chargeur de plugins :

- accepte un chemin relatif ou absolu,
- resout les chemins relatifs depuis la racine du depot,
- decouvre les classes qui heritent de `BaseMetric`,
- les instancie,
- les enregistre dans `registry`.

Le point important est que le chargement ne depend plus du repertoire courant du processus.

### 4.5 Routes FastAPI exposees

Par defaut, FastAPI expose aussi :

- `/docs`
- `/redoc`
- `/openapi.json`

En revanche, `/` n'est pas defini et renvoie `404`.

## 5. Endpoints exposes

### 5.1 `GET /languages`

Retourne les langues declarees dans `language_manager`.

Etat actuel :

- seule la langue `fr` est active.

### 5.2 `POST /similarity`

Ce endpoint compare une seule paire de phrases.

Payload attendu :

```json
{
  "phrase1": "Le chat mange",
  "phrase2": "Le chien mange",
  "metrics": ["jaccard", "camembert"],
  "language": "fr"
}
```

Flux :

1. validation Pydantic,
2. resolution du contexte linguistique via `language_manager`,
3. recuperation des metriques dans `registry`,
4. appel de `metric.compute(phrase1, phrase2, context)`,
5. retour des scores dans `SimilarityResponse`.

Erreurs geres explicitement :

- langue inconnue -> HTTP 400,
- metrique inconnue -> HTTP 400,
- erreur de dependance BERT au runtime -> HTTP 500.

### 5.3 `POST /similarity/upload`

Ce endpoint traite un fichier JSON envoye en `multipart/form-data` sous le champ `file`.

Parametre complementaire :

- `language`, optionnel, par defaut `fr`

Formats JSON acceptes :

#### Format objet recommande

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

#### Format liste legacy

```json
[
  ["jaccard", "camembert"],
  ["chat noir", "chat blanc"],
  ["bonjour", "salut"]
]
```

Comportement :

1. verifie l'extension `.json`,
2. lit et parse le contenu,
3. passe les donnees a `process_minimal_json(...)`,
4. cree un fichier `result_<nom>.json` dans `data/` ou dans le dossier defini par `SIMILARITY_DATA_DIR`,
5. renvoie les resultats dans la reponse HTTP.

Erreurs geres explicitement :

- mauvais type de fichier -> HTTP 400,
- JSON invalide -> HTTP 400,
- metrique inconnue ou payload batch invalide -> HTTP 400,
- erreur de dependance BERT au runtime -> HTTP 500.

## 6. Service batch `app/services/processor.py`

Le service `process_minimal_json(data, default_language="fr")` :

1. accepte un objet JSON ou une liste legacy,
2. valide la presence des metriques et des couples,
3. verifie que toutes les metriques existent dans `registry`,
4. recupere un `LanguageContext` via `language_manager`,
5. calcule les scores pour chaque couple,
6. retourne :

```json
{
  "results": [
    {
      "p1": "...",
      "p2": "...",
      "scores": {
        "jaccard": 0.5
      }
    }
  ],
  "metadata": {
    "selected_metrics": ["jaccard"],
    "language": "fr"
  }
}
```

## 7. Systeme de langues

Le `LanguageManager` :

- enregistre les langues disponibles,
- charge les pipelines spaCy a la demande,
- garde ces pipelines en cache,
- sert de point unique d'acces aux ressources linguistiques.

Si `fr_core_news_md` n'est pas disponible :

- le code tombe sur `spacy.blank("fr")`,
- l'API continue de repondre,
- mais la qualite de `jaccard`, `dice` et `spacy_vector` peut diminuer.

## 8. Metriques natives

### 8.1 `jaccard`

- basee sur les lemmes spaCy,
- retire stop words, ponctuation et espaces,
- calcule `|A ∩ B| / |A ∪ B|`.

### 8.2 `dice`

- meme pretraitement que `jaccard`,
- calcule `2|A ∩ B| / (|A| + |B|)`.

### 8.3 `levenshtein`

- compare les chaines brutes,
- ne depend pas de spaCy,
- renvoie une similarite normalisee entre `0.0` et `1.0`.

### 8.4 `spacy_vector`

- compare deux `Doc` spaCy via `doc1.similarity(doc2)`,
- utilise les vecteurs du modele spaCy charge.

### 8.5 `camembert`

En pratique, cette metrique utilise :

- `sentence-transformers`
- le modele `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

et non un checkpoint CamemBERT pur. Le nom de metrique conserve `camembert` pour rester coherent avec l'intention fonctionnelle de la branche integree.

Caracteristiques :

- chargement lazy au premier appel,
- embeddings de phrases,
- score via similarite cosinus,
- score borne a `[0.0, 1.0]`.

Si `sentence-transformers` n'est pas installe, un `RuntimeError` est leve puis converti en HTTP 500 par l'API.

## 9. Plugins

Les plugins actuels sont charges depuis `plugins/metrics/`.

Leur contrat reste :

- heriter de `BaseMetric`,
- definir un `name`,
- definir `compute(self, phrase1, phrase2, context)`.

Le registre contient donc a la fois :

- les metriques natives,
- les metriques plugin.

## 10. Registre des metriques

`MetricsRegistry` :

- valide les metriques a l'enregistrement,
- stocke les instances dans un dictionnaire interne,
- expose `register`, `get` et `list`.

Les collisions de noms restent possibles :

- la derniere metrique enregistree ecrase la precedente.

## 11. Contrats API

### 11.1 `SimilarityRequest`

Definition effective :

- `phrase1: str`
- `phrase2: str`
- `metrics: list[str] = ["jaccard"]`
- `language: str = "fr"`

### 11.2 `SimilarityResponse`

Definition effective :

- `scores: dict[str, float]`
- `metadata: dict`

## 12. Tests

Le projet contient des tests pour verifier :

- le registre,
- les metriques natives,
- les plugins,
- l'API,
- l'upload batch,
- l'enregistrement de `camembert`.

Un test de `camembert` existe sans telecharger le vrai modele, grace a un mock de `get_bert_model()`.

## 13. Dependencies a jour

Le projet depend maintenant notamment de :

- `spacy>=3.7.0`
- `sentence-transformers`
- `python-multipart`
- du modele `fr_core_news_md`

`python-multipart` est necessaire pour `UploadFile` sur `/similarity/upload`.

## 14. Limites et points d'attention

- l'API n'expose toujours pas de frontend sur `/`
- le premier appel a `camembert` peut etre lent
- les sorties de `/similarity/upload` ecrivent des fichiers dans `data/`
- le nom `camembert` ne correspond pas a un vrai modele CamemBERT pur dans le code actuel
- les fichiers de tests conservent des conventions historiques non totalement homogenes

## 15. Resume mental rapide

Le projet fonctionne aujourd'hui comme suit :

1. FastAPI recoit une requete unitaire ou un fichier batch.
2. Pydantic valide l'entree unitaire.
3. Le `LanguageManager` fournit un pipeline spaCy pour `fr`.
4. Le `registry` recupere les metriques natives et plugin.
5. Chaque metrique calcule un score.
6. Le service batch reutilise exactement le meme registre et le meme contexte linguistique.
7. L'API renvoie les scores, et l'upload enregistre aussi un fichier resultat.
