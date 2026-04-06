# Documentation technique du projet `SimilariteSemantique`

## 1. Objet du document

Ce document decrit l'etat reel du projet tel qu'il fonctionne aujourd'hui.
Il couvre :

- l'architecture FastAPI,
- les registres et loaders du noyau,
- les langues, modeles et metriques,
- le systeme de plugins,
- les endpoints exposes,
- les dependances et warnings possibles,
- les tests disponibles.

L'objectif est d'expliquer le projet de bout en bout a partir du code actuel.

## 2. Resume fonctionnel

`SimilariteSemantique` est une API FastAPI qui compare des phrases a l'aide
de plusieurs metriques de similarite.

L'application expose trois endpoints principaux :

- `GET /languages`
- `POST /similarity`
- `POST /similarity/upload`

Le moteur combine trois couches extensibles :

- des langues, gerees par `LanguageManager`,
- des modeles ML, geres par `ModelRegistry`,
- des metriques, gerees par `MetricsRegistry`.

Ces trois couches peuvent etre enrichies par plugins charges
automatiquement au demarrage.

## 3. Vue d'ensemble de l'architecture

### 3.1 Fichiers principaux du runtime

| Chemin | Role |
| --- | --- |
| `app/main.py` | Cree l'application FastAPI et declenche le chargement des plugins. |
| `app/api/endpoints.py` | Definit les endpoints `/languages`, `/similarity` et `/similarity/upload`. |
| `app/models/schemas.py` | Definit les schemas Pydantic de l'API. |
| `app/services/processor.py` | Gere le traitement batch des payloads JSON. |
| `app/core/language_config.py` | Structure declarative d'une langue. |
| `app/core/language_manager.py` | Gere les langues, les pipelines spaCy et leur cache. |
| `app/core/language_loader.py` | Charge des langues plugin depuis `plugins/languages/`. |
| `app/core/model_definition.py` | Definit le contrat d'une definition de modele. |
| `app/core/model_registry.py` | Registre global des definitions de modeles et des ressources chargees. |
| `app/core/model_loader.py` | Charge des definitions de modeles depuis `plugins/models/`. |
| `app/core/metrics.py` | Contient les metriques natives et les classes de base. |
| `app/core/registry.py` | Registre global des metriques. |
| `app/core/plugin_loader.py` | Charge les metriques plugin depuis `plugins/metrics/`. |
| `app/core/loader_utils.py` | Fournit la resolution de chemins stable et l'import dynamique commun. |
| `app/core/spacy_compat.py` | Fournit `spaCy` si disponible, sinon un fallback minimal. |

### 3.2 Repertoires de plugins

| Dossier | Contenu |
| --- | --- |
| `plugins/languages/` | Declarations de langues via `LanguageConfig`. |
| `plugins/models/` | Definitions de modeles legeres, chargees en lazy au premier usage. |
| `plugins/metrics/` | Metriques de similarite supplementaires. |

### 3.3 Repertoires utilitaires

| Dossier | Role |
| --- | --- |
| `tests/` | Tests unitaires et tests d'integration. |
| `docs/` | Documentation technique. |
| `data/` | Sortie des traitements batch uploades. |

## 4. Sequence exacte de demarrage

Quand on lance :

```bash
python -m uvicorn app.main:app
```

`app/main.py` execute les operations suivantes :

1. creation de l'objet `FastAPI`,
2. inclusion du routeur de `app.api.endpoints`,
3. chargement des plugins de langues via `load_languages("plugins/languages")`,
4. chargement des plugins de modeles via `load_models("plugins/models")`,
5. chargement des plugins de metriques via `load_plugins("plugins/metrics")`.

Important :

- l'import de `app.api.endpoints` importe deja `registry` et `language_manager`,
- cela enregistre les metriques natives et la langue native `fr`,
- aucun modele ML lourd n'est charge au demarrage,
- seuls les objets declaratifs legers sont enregistres.

## 5. Resolution des chemins et imports dynamiques

Tous les loaders utilisent le meme pattern via `app/core/loader_utils.py` :

- un chemin absolu est utilise tel quel,
- un chemin relatif est resolu depuis la racine du depot,
- l'import dynamique ne depend pas du repertoire courant du processus.

Cela garantit que les dossiers :

- `plugins/languages/`,
- `plugins/models/`,
- `plugins/metrics/`

peuvent etre charges proprement meme si l'application est demarree
depuis un autre repertoire.

## 6. Systeme de langues

### 6.1 `LanguageConfig`

Une langue est decrite par `LanguageConfig` :

- `code`
- `display_name`
- `spacy_model`
- `embedding_model`

`embedding_model` est un nom declaratif pouvant etre exploite par
une metrique pour choisir un modele adapte.

### 6.2 `LanguageManager`

`LanguageManager` est le point central d'acces aux ressources linguistiques.
Il :

- enregistre les langues supportees,
- valide les declarations,
- charge les pipelines spaCy a la demande,
- garde les pipelines en cache,
- retourne un `LanguageContext` passe ensuite aux metriques.

Le `LanguageContext` contient :

- la configuration de langue,
- le pipeline spaCy charge.

### 6.3 Langue native

Au chargement de `app/core/language_manager.py`, la langue suivante est
enregistree nativement :

- `fr` -> `Francais` -> `fr_core_news_md`

Cette langue existe meme sans plugin.

### 6.4 Langues plugin actuellement presentes

Le depot contient aujourd'hui :

- `plugins/languages/english.py` -> `en`
- `plugins/languages/test_language.py` -> `xx`

`en` est la langue anglaise utilisable notamment avec `bert_score`.
`xx` est une langue factice de demonstration/test.

### 6.5 Chargement spaCy et fallback

Le chargement de pipeline suit ce comportement :

1. `LanguageManager` tente `spacy.load(config.spacy_model)`,
2. si le modele est introuvable, un warning est affiche,
3. le code tombe sur `spacy.blank(config.code)`.

Exemple de message :

```text
ATTENTION: Le modele spaCy 'en_core_web_md' est introuvable. Utilisation d'un modele vide pour 'en'.
```

Ce fallback maintient l'application operationnelle, mais peut reduire
la qualite de certaines metriques basees sur spaCy.

## 7. Compatibilite spaCy

`app/core/spacy_compat.py` tente d'importer le vrai package `spaCy`.
Si cet import echoue, le projet utilise un fallback minimal qui fournit :

- un pipeline factice,
- des tokens simples,
- une similarite rudimentaire basee sur le recouvrement.

Ce mecanisme existe pour conserver un comportement testable meme dans des
environnements ou les binaires natifs de spaCy ne sont pas disponibles.

En environnement normal, le vrai spaCy reste prioritaire.

## 8. Systeme de modeles

### 8.1 Objectif

Le systeme de modeles permet de :

- enregistrer des definitions legeres au demarrage,
- charger la ressource reelle uniquement au premier usage,
- reutiliser la meme ressource ensuite via cache.

### 8.2 Contrat d'un modele

Un plugin modele doit heriter de `BaseModelDefinition` et definir :

- `name`
- `description`
- `load(self)`

La methode `load()` ne doit etre appelee qu'au premier `model_registry.get(name)`.

### 8.3 `ModelRegistry`

`ModelRegistry` garde deux structures distinctes :

- `_definitions` : definitions legeres,
- `_loaded_models` : ressources effectivement chargees.

Semantique exacte :

1. au demarrage, seules les definitions sont enregistrees,
2. au premier `get("nom")`, la definition charge la ressource reelle,
3. les acces suivants reutilisent l'objet mis en cache.

Si le chargement echoue au premier acces, un `RuntimeError` explicite est leve.

### 8.4 Modele natif

Le registre de modeles contient nativement :

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Ce modele est utilise par la metrique native `camembert`.

### 8.5 Modeles plugin actuellement presents

Le depot contient aujourd'hui :

- `dummy_echo_model`
- `bert_score_english`

#### `dummy_echo_model`

Plugin purement demonstratif, sans dependance externe.

#### `bert_score_english`

Plugin BERT anglais qui :

- charge `bert-base-uncased`,
- cree un tokenizer Hugging Face,
- charge le modele Transformers,
- met le modele en mode `eval()`.

Dependencies supplementaires requises pour ce plugin :

- `torch`
- `transformers`

Ces dependances sont maintenant listees dans `requirements.txt`.

## 9. Systeme de metriques

### 9.1 Contrat

Une metrique doit :

- heriter de `BaseMetric`,
- definir `name`,
- definir `description`,
- implementer `compute(self, phrase1, phrase2, context)`.

La methode `compute(...)` retourne un `MetricResult` contenant :

- `name`
- `score`
- `detail`

### 9.2 `MetricsRegistry`

`MetricsRegistry` :

- valide les metriques au moment de l'enregistrement,
- stocke les instances dans un dictionnaire,
- expose `register`, `get` et `list`.

En cas de collision de noms :

- la derniere metrique enregistree ecrase la precedente.

### 9.3 Metriques natives

Le registre natif contient :

- `jaccard`
- `dice`
- `levenshtein`
- `spacy_vector`
- `camembert`

#### `jaccard`

- pretraitement via spaCy,
- suppression des stop words, ponctuation et espaces,
- calcul de `|A inter B| / |A union B|`.

#### `dice`

- meme pretraitement que `jaccard`,
- calcul de `2|A inter B| / (|A| + |B|)`.

#### `levenshtein`

- compare les chaines brutes,
- ne depend pas du pipeline spaCy,
- renvoie une similarite normalisee entre `0.0` et `1.0`.

#### `spacy_vector`

- appelle `doc1.similarity(doc2)`,
- depend de la presence de vecteurs utiles dans le modele spaCy charge.

#### `camembert`

Le nom historique est `camembert`, mais la metrique utilise en realite
le modele :

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Fonctionnement :

- recupere la ressource via `model_registry`,
- encode les deux phrases,
- calcule une similarite cosinus,
- borne le score a `[0.0, 1.0]`.

Si `sentence-transformers` n'est pas disponible, un `RuntimeError`
est leve puis converti en HTTP 500 par l'API.

### 9.4 Metriques plugin actuellement presentes

Le depot contient aujourd'hui :

- `word_overlap`
- `length_ratio`
- `prefix`
- `common_bigrams`
- `bert_score`

#### `bert_score`

`bert_score` est une metrique plugin basee sur des embeddings contextuels
au niveau token.

Principe :

1. tokenisation avec le tokenizer du modele BERT,
2. suppression des tokens speciaux,
3. extraction des embeddings contextuels de chaque token,
4. normalisation L2 des vecteurs,
5. matrice de similarite par produit scalaire,
6. precision = meilleur alignement de chaque token de la phrase 1,
7. rappel = meilleur alignement de chaque token de la phrase 2,
8. score final = F1.

Le `score` renvoye par l'API est donc le `f1`.
Le detail contient aussi :

- `precision`
- `recall`
- `f1`
- `model`
- `token_count_1`
- `token_count_2`

Cas limites geres explicitement :

- deux phrases vides -> score `1.0`,
- une phrase vide -> score `0.0`.

Resolution du modele :

- si `context.config.embedding_model` correspond a un modele enregistre,
  `bert_score` l'utilise,
- sinon, la metrique tombe sur `bert_score_english`.

Consequence pratique :

- pour `en`, le plugin langue declare `embedding_model="bert_score_english"`,
- pour `fr`, la configuration native utilise `camembert-base`, qui n'est pas
  un modele enregistre dans `ModelRegistry`,
- donc appeler `bert_score` en `fr` retombera aujourd'hui sur
  `bert_score_english`.

Le plugin `bert_score` est donc pense en priorite pour l'anglais.

## 10. Systeme de plugins

### 10.1 Plugins de langues

Loader :

- `app/core/language_loader.py`

Contrat :

- exposer une ou plusieurs instances de `LanguageConfig` dans le module,
- le loader les decouvre puis les enregistre dans `language_manager`.

Gestion des erreurs :

- fichier invalide -> warning et on continue,
- declaration invalide -> warning et on continue.

### 10.2 Plugins de modeles

Loader :

- `app/core/model_loader.py`

Contrat :

- exposer une ou plusieurs classes qui heritent de `BaseModelDefinition`,
- le loader les instancie,
- les definitions sont enregistrees sans charger le modele.

Gestion des erreurs :

- import ou instanciation impossible -> warning et on continue.

### 10.3 Plugins de metriques

Loader :

- `app/core/plugin_loader.py`

Contrat :

- exposer une ou plusieurs classes qui heritent de `BaseMetric`,
- le loader les instancie,
- les metriques sont enregistrees dans `registry`.

Gestion des erreurs :

- import ou instanciation impossible -> warning et on continue.

## 11. Endpoints exposes

### 11.1 `GET /languages`

Retourne les langues actuellement enregistrees dans `language_manager`.

Exemple de reponse :

```json
{
  "languages": [
    {"code": "fr", "display_name": "Francais"},
    {"code": "en", "display_name": "English"},
    {"code": "xx", "display_name": "Langue de test"}
  ]
}
```

### 11.2 `POST /similarity`

Compare une seule paire de phrases.

Payload :

```json
{
  "phrase1": "The cat is sleeping on the sofa",
  "phrase2": "A cat sleeps on the couch",
  "metrics": ["bert_score"],
  "language": "en"
}
```

Flux interne :

1. validation Pydantic via `SimilarityRequest`,
2. recuperation du `LanguageContext`,
3. recuperation de chaque metrique dans `registry`,
4. execution de `metric.compute(...)`,
5. conversion en `SimilarityResponse`.

Erreurs :

- langue inconnue -> HTTP 400,
- metrique inconnue -> HTTP 400,
- erreur runtime dans le chargement d'un modele -> HTTP 500.

### 11.3 `POST /similarity/upload`

Accepte un fichier JSON envoye en `multipart/form-data`
sous le champ `file`.

Deux formats sont acceptes.

#### Format objet recommande

```json
{
  "metrics": ["jaccard", "bert_score"],
  "language": "en",
  "pairs": [
    ["The cat is sleeping on the sofa", "A cat sleeps on the couch"],
    ["hello world", "hello there"]
  ]
}
```

#### Format liste legacy

```json
[
  ["jaccard", "bert_score"],
  ["The cat is sleeping on the sofa", "A cat sleeps on the couch"],
  ["hello world", "hello there"]
]
```

Comportement :

1. verification de l'extension `.json`,
2. lecture et parse du contenu,
3. delegation a `process_minimal_json(...)`,
4. ecriture du resultat dans `data/` ou dans `SIMILARITY_DATA_DIR`,
5. retour du resultat dans la reponse HTTP.

## 12. Service batch

`app/services/processor.py` fournit `process_minimal_json(...)`.

Ce service :

- parse le payload objet ou liste,
- valide les metriques demandees,
- valide chaque couple de phrases,
- recupere un `LanguageContext`,
- calcule les scores pour chaque metrique de chaque couple,
- retourne un objet `results + metadata`.

Le meme registre et le meme contexte linguistique sont reutilises
pour tous les couples du batch.

## 13. Schemas API

### 13.1 `SimilarityRequest`

Definition effective :

- `phrase1: str`
- `phrase2: str`
- `metrics: list[str] = ["jaccard"]`
- `language: str = "fr"`

### 13.2 `SimilarityResponse`

Definition effective :

- `scores: dict[str, float]`
- `metadata: dict`

## 14. Dependances

### 14.1 Dependances de base declarees

`requirements.txt` contient aujourd'hui :

- `fastapi`
- `uvicorn`
- `httpx`
- `pydantic`
- `spacy>=3.7.0`
- `sentence-transformers`
- `torch`
- `transformers`
- `python-multipart`
- le wheel `fr_core_news_md`

### 14.2 Dependances Python pour `bert_score`

Les dependances Python du plugin `bert_score` sont incluses dans
`requirements.txt`.

### 14.3 Telechargements au premier usage

Le premier appel a certaines metriques peut declencher des chargements
externes :

- `camembert` peut charger son modele `sentence-transformers`,
- `bert_score` peut telecharger `bert-base-uncased` depuis Hugging Face.

Des warnings peuvent apparaitre au premier chargement, par exemple :

- modele spaCy introuvable,
- requete Hugging Face non authentifiee,
- rapport de chargement BERT.

Ces messages ne signifient pas forcement un echec. Ce qui compte est
le code de reponse final et la presence d'un score.

## 15. Lancer l'application

Commande de base :

```bash
python -m uvicorn app.main:app
```

Routes utiles exposees par FastAPI :

- `/docs`
- `/redoc`
- `/openapi.json`

Le chemin `/` n'est pas defini et renvoie `404`.

Pour utiliser `bert_score`, il est recommande de :

- installer les dependances de `requirements.txt`,
- demarrer sans `--reload` lors du premier test sur Windows,
- attendre le premier chargement du modele.

## 16. Tests

Le dossier `tests/` couvre plusieurs couches :

- `testSchemas.py` -> schemas Pydantic,
- `testRegistry.py` -> registre de metriques,
- `testMetrics.py` -> metriques natives, dont `camembert`,
- `testPlugins.py` -> plugins de metriques,
- `testApi.py` -> endpoints FastAPI,
- `testModelLoader.py` -> registre/loader de modeles,
- `testLanguageLoader.py` -> loader de langues,
- `testBertScorePlugin.py` -> enregistrement et calcul de `bert_score`.

Les tests de modeles lourds utilisent des mocks ou doubles de test :

- aucun telechargement reel n'est necessaire pour valider `bert_score`,
- aucun vrai modele ML n'est necessaire dans la suite de tests.

## 17. Erreurs et warnings a connaitre

### 17.1 Fichiers plugin invalides

Si un fichier plugin de langue, modele ou metrique est invalide :

- un warning est logue,
- le chargement continue pour les autres fichiers.

### 17.2 Chargement reel d'un modele en echec

Si un modele echoue au premier acces :

- le registre leve un `RuntimeError` explicite,
- l'endpoint convertit cette erreur en HTTP 500.

### 17.3 Warnings spaCy

Si le modele spaCy cible est absent :

- la langue reste disponible,
- un modele vide `spacy.blank(...)` est utilise,
- certaines metriques spaCy peuvent devenir moins pertinentes.

### 17.4 Premier chargement BERT

Au premier appel a `bert_score`, il est normal d'observer :

- telechargement de fichiers Hugging Face,
- temps de reponse plus long,
- messages d'information sur le chargement des poids.

## 18. Inventaire actuel des plugins du depot

### 18.1 Langues

- `en`
- `xx`

### 18.2 Modeles

- `dummy_echo_model`
- `bert_score_english`

### 18.3 Metriques

- `word_overlap`
- `length_ratio`
- `prefix`
- `common_bigrams`
- `bert_score`

## 19. Resume mental rapide

Le projet fonctionne aujourd'hui comme suit :

1. FastAPI recoit une requete unitaire ou un fichier batch.
2. Le routeur demande un `LanguageContext` a `LanguageManager`.
3. Les metriques demandees sont recuperees dans `MetricsRegistry`.
4. Si une metrique a besoin d'un modele, elle le demande a `ModelRegistry`.
5. Le modele n'est charge qu'au premier usage, puis reste en cache.
6. La metrique calcule son score et le retourne.
7. L'API renvoie les scores a l'utilisateur.

Le coeur du projet est donc un moteur a trois registres logiques :

- langues,
- modeles,
- metriques,

avec une extension par plugins et un lazy loading sur les ressources lourdes.
