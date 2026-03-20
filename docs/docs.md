# Fonctionnement exact du projet `SimilariteSemantique`

## 1. Objet du document

Ce document décrit le fonctionnement reel du depot dans son etat actuel, a partir du code present dans :

- `app/`
- `plugins/`
- `tests/`
- `README.md`
- `requirements*.txt`

L'objectif n'est pas de decrire l'intention du projet de maniere abstraite, mais d'expliquer ce que le code fait exactement aujourd'hui, y compris les limites, les effets de bord, les conventions implicites et les incoherences visibles.

## 2. Ce que fait reellement l'application

Le projet expose une API FastAPI qui calcule un ou plusieurs scores de similarite entre deux phrases.

Le service accepte une requete HTTP `POST /similarity` avec :

- `phrase1`
- `phrase2`
- une liste de metriques
- une langue, par defaut `fr`

Le moteur :

1. valide le JSON entrant avec Pydantic,
2. recupere un contexte linguistique via `LanguageManager`,
3. retrouve chaque metrique dans un registre global,
4. execute `metric.compute(...)`,
5. renvoie uniquement les scores numeriques dans la reponse HTTP.

Il existe aussi un endpoint `GET /languages` qui liste les langues declarees.

## 3. Architecture du depot

### 3.1 Dossiers utiles au runtime

| Chemin | Role exact |
| --- | --- |
| `app/main.py` | Point d'entree FastAPI. Cree l'application, monte le routeur et charge les plugins au moment de l'import du module. |
| `app/api/endpoints.py` | Definit les endpoints HTTP `/languages` et `/similarity`. |
| `app/models/schemas.py` | Definit les schemas Pydantic d'entree et de sortie de l'API. |
| `app/core/metrics.py` | Contient les fonctions de calcul, la classe `MetricResult`, la classe abstraite `BaseMetric` et les 4 metriques natives. |
| `app/core/registry.py` | Contient le registre global des metriques et la validation minimale des objets enregistres. |
| `app/core/plugin_loader.py` | Charge dynamiquement les plugins Python situes dans `plugins/metrics`. |
| `app/core/language_config.py` | Structure declarative d'une langue supportee. |
| `app/core/language_manager.py` | Gere les langues, le chargement paresseux des pipelines spaCy et leur cache memoire. |
| `plugins/metrics/overlap_metric.py` | Plugin additionnel actuellement present dans le depot. |

### 3.2 Dossiers utiles au developpement

| Chemin | Role exact |
| --- | --- |
| `tests/` | Contient des tests unitaires et d'integration. Plusieurs conventions y sont non standard, voir section 11. |
| `docs/` | Dossier de documentation. Il ne contenait auparavant qu'un `.gitkeep`. |
| `README.md` | Explique l'intention generale et la maniere prevue de lancer le projet. |

### 3.3 Dossiers presents mais non applicatifs

| Chemin | Observation |
| --- | --- |
| `venv/` | Environnement virtuel local ignore par Git. |
| `source/` | Deuxieme environnement virtuel local ignore par Git. Il ne participe pas au runtime de l'application. |

## 4. Sequence de demarrage exacte

Quand on lance en theorie :

```bash
python3 -m uvicorn app.main:app --reload
```

ou l'equivalent Windows adapte, voici ce qui se passe.

### 4.1 Import de `app.main`

Le module `app.main` fait 4 choses :

1. importe `FastAPI`,
2. importe `router` depuis `app.api.endpoints`,
3. importe `language_manager` depuis `app.core.language_manager`,
4. importe `load_plugins` depuis `app.core.plugin_loader`.

Point important : l'import de `language_manager` ne sert pas directement dans `main.py`, mais force l'execution du code de module de `language_manager.py`. C'est ce qui cree l'instance globale et enregistre la langue francaise.

### 4.2 Initialisation des langues

Dans `app/core/language_manager.py`, a l'import du module :

1. une instance globale `language_manager = LanguageManager(default_language="fr")` est creee,
2. une configuration de langue francaise est enregistree avec :
   - `code="fr"`
   - `display_name="Francais"`
   - `spacy_model="fr_core_news_md"`
   - `embedding_model="camembert-base"`

Important : `embedding_model` est memorise dans la configuration, mais n'est jamais utilise ailleurs dans le code actuel.

### 4.3 Initialisation du registre de metriques natives

Dans `app/core/registry.py`, a l'import du module :

1. une instance globale `registry = MetricsRegistry()` est creee,
2. quatre metriques natives sont immediatement instanciees et enregistrees :
   - `JaccardMetric()`
   - `DiceMetric()`
   - `LevenshteinMetric()`
   - `SpacyVectorMetric()`

Donc, rien qu'en important `registry`, le noyau de metriques est deja pret.

### 4.4 Creation de l'application FastAPI

Toujours dans `app/main.py` :

1. `app = FastAPI(title="Semantic Similarity API")`
2. `app.include_router(router)`

Il n'y a pas de hook `startup` explicite. Le chargement des composants se fait par import et par execution immediate du code de module.

Comme aucun `docs_url`, `redoc_url` ou `openapi_url` n'est surcharge, FastAPI expose aussi par defaut :

- `/docs`
- `/redoc`
- `/openapi.json`

### 4.5 Chargement des plugins

Enfin, `load_plugins("plugins/metrics")` est execute tout de suite dans `app/main.py`.

Consequences directes :

- les plugins sont charges au moment de l'import de `app.main`,
- donc `from app.main import app` dans un test charge aussi les plugins,
- si on importe plusieurs fois `app.main` dans le meme processus ou si on rappelle `load_plugins(...)`, les metriques portant le meme nom sont re-enregistrees en ecrasant les precedentes,
- le chemin `"plugins/metrics"` est relatif au repertoire courant du processus, pas au fichier `main.py`.

Cela signifie que le projet suppose implicitement qu'on lance le serveur depuis la racine du depot.

## 5. Flux complet d'une requete `POST /similarity`

### 5.1 Format d'entree attendu

Le schema Pydantic `SimilarityRequest` accepte :

```json
{
  "phrase1": "Le chat mange",
  "phrase2": "Le chien mange",
  "metrics": ["jaccard"],
  "language": "fr"
}
```

Regles exactes :

- `phrase1` est obligatoire,
- `phrase2` est obligatoire,
- `metrics` est facultatif et vaut `["jaccard"]` par defaut,
- `language` est facultatif et vaut `"fr"` par defaut.

Nuances importantes :

- `Field(..., min_length=0)` sur `phrase1` et `phrase2` rend le champ obligatoire, mais autorise une chaine vide,
- une phrase absente declenche une erreur de validation avant d'entrer dans la logique du endpoint,
- une phrase vide est acceptee et traitee par les metriques.

### 5.2 Resolution du contexte linguistique

Le endpoint appelle :

```python
context = language_manager.get_context(payload.language)
```

Le comportement exact de `get_context` est :

1. si aucun code n'est fourni, la langue par defaut `fr` est utilisee,
2. si le code n'existe pas dans `_configs`, une `ValueError` est levee,
3. si le pipeline spaCy de cette langue n'est pas encore en cache, `_load_pipeline(...)` est appelee,
4. un `LanguageContext(config=..., pipeline=...)` est renvoye.

Le endpoint convertit la `ValueError` en `HTTPException(400)`.

Donc :

- langue non supportee -> HTTP 400,
- langue supportee mais modele spaCy absent -> pas d'erreur HTTP ; le code bascule sur un pipeline spaCy vide via `spacy.blank(code)`.

### 5.3 Recuperation des metriques

Pour chaque nom de metrique dans `payload.metrics`, le endpoint fait :

```python
metric = registry.get(metric_name)
```

Si la metrique n'existe pas :

- une `HTTPException(400)` est levee,
- le message est `Unknown metric: <nom>`.

Important :

- il n'existe pas d'endpoint pour lister les metriques disponibles,
- le registre contient a la fois les metriques natives et les plugins charges,
- les objets stockes sont des instances partagees globalement dans le processus.

### 5.4 Calcul effectif

Chaque metrique recoit :

```python
metric.compute(payload.phrase1, payload.phrase2, context)
```

Le contrat de fait est :

- `phrase1`: `str`
- `phrase2`: `str`
- `context`: `LanguageContext`

Chaque `compute(...)` renvoie un objet `MetricResult(name, score, detail=None)`.

Le endpoint n'utilise que `result.score`.

Le champ `detail` est actuellement calcule par plusieurs metriques, mais n'est jamais expose dans la reponse HTTP.

### 5.5 Construction de la reponse

Le endpoint renvoie :

```json
{
  "scores": {
    "jaccard": 0.5
  },
  "metadata": {
    "selected_metrics": ["jaccard"],
    "language": "fr"
  }
}
```

Observations exactes :

- `scores` est construit dans l'ordre de la liste `payload.metrics`,
- si la meme metrique apparait deux fois, elle est calculee deux fois, mais la cle finale dans `scores` ecrase la precedente,
- `metadata.selected_metrics` conserve la liste d'origine, y compris d'eventuels doublons,
- `metadata` n'a pas de schema strict : c'est juste `dict`.

## 6. Endpoint `GET /languages`

Le endpoint `/languages` appelle :

```python
language_manager.list_languages()
```

Il renvoie une liste de dictionnaires de la forme :

```json
{
  "languages": [
    {
      "code": "fr",
      "display_name": "Francais"
    }
  ]
}
```

Etat actuel du depot :

- une seule langue est declaree : `fr`,
- l'architecture prevoit des ajouts futurs, mais aucun autre code langue n'est actif.

## 7. Systeme de langues en detail

### 7.1 `LanguageConfig`

`LanguageConfig` est une simple dataclass declarative.

Elle contient :

- `code`
- `display_name`
- `spacy_model`
- `embedding_model`

Le moteur n'utilise actuellement que :

- `code`
- `display_name`
- `spacy_model`

`embedding_model` est du stockage de configuration en avance de phase.

### 7.2 `LanguageManager`

`LanguageManager` encapsule deux dictionnaires internes :

- `_configs`: definitions statiques des langues,
- `_pipelines`: cache des pipelines spaCy deja charges.

Le chargement est paresseux :

- le modele spaCy n'est pas charge au demarrage,
- il est charge a la premiere requete qui demande la langue,
- il reste ensuite en memoire pour le reste de la vie du processus.

Il n'existe pas :

- de mecanisme d'eviction de cache,
- de rechargement explicite,
- de verrou de synchronisation,
- de persistance disque de ce cache.

### 7.3 Fallback spaCy

Si `spacy.load(config.spacy_model)` echoue avec `OSError`, le code fait :

```python
return spacy.blank(config.code)
```

Donc le service reste fonctionnel, mais la qualite peut fortement changer selon la metrique :

- `jaccard` et `dice` dependent de la tokenisation, des lemmes et des stop words disponibles dans le pipeline,
- `spacy_vector` depend de vecteurs semantiques qui peuvent etre absents dans un pipeline vide,
- `levenshtein` ne depend pas de spaCy,
- le plugin `word_overlap` ne depend pas de spaCy.

## 8. Systeme de metriques natives

Le fichier `app/core/metrics.py` contient a la fois :

- des fonctions de pretraitement,
- des fonctions mathematiques,
- la structure de retour,
- l'interface de metrique,
- les implementations natives.

### 8.1 `spacy_preprocess(text, pipeline)`

Cette fonction :

1. remplace `None` par `""`,
2. met le texte en minuscules,
3. passe le texte dans le pipeline spaCy,
4. retourne la liste des `lemma_`,
5. filtre :
   - les stop words,
   - la ponctuation,
   - les espaces.

Consequence importante :

- `jaccard` et `dice` travaillent sur des lemmes en minuscules,
- les repetitions de mots sont perdues plus tard, car les fonctions de similarite utilisent des ensembles,
- la normalisation appliquee n'est pas la meme selon les metriques.

### 8.2 `JaccardMetric`

Nom de registre : `jaccard`

Pipeline :

1. pretraitement spaCy de `phrase1`,
2. pretraitement spaCy de `phrase2`,
3. conversion implicite en ensembles dans `jaccard_similarity`,
4. calcul :

```text
|A ∩ B| / |A ∪ B|
```

Cas limites exacts :

- deux ensembles vides -> `1.0`,
- un seul ensemble vide -> `0.0`.

Effet de bord mathematique :

- les doublons n'ont aucun effet sur le score.

Exemple :

- `"chat chat"` et `"chat"` donnent le meme ensemble,
- donc la similarite peut etre `1.0`.

### 8.3 `DiceMetric`

Nom de registre : `dice`

Pretraitement identique a `jaccard`, mais formule :

```text
2|A ∩ B| / (|A| + |B|)
```

Cas limites exacts :

- deux ensembles vides -> `1.0`,
- un seul ensemble vide -> `0.0`.

Comme pour Jaccard :

- les doublons sont ignores,
- la casse est neutralisee,
- la ponctuation et les stop words sont retirees.

### 8.4 `LevenshteinMetric`

Nom de registre : `levenshtein`

Cette metrique n'utilise pas spaCy pour le calcul, mais accepte quand meme `context` pour respecter l'interface.

Le score est :

```text
1 - distance_edition(s1, s2) / max(len(s1), len(s2))
```

Le comportement exact est :

- `None` est remplace par `""`,
- si les deux chaines sont vides -> `1.0`,
- si les chaines sont identiques -> `1.0`,
- sinon la distance d'edition est calculee par programmation dynamique caractere par caractere.

Point important :

- aucune mise en minuscules,
- aucune suppression de ponctuation,
- aucune lemmatisation,
- la metrique est sensible a la casse et a la forme brute de la chaine.

### 8.5 `SpacyVectorMetric`

Nom de registre : `spacy_vector`

Cette metrique :

1. passe `phrase1` telle quelle dans `context.pipeline`,
2. passe `phrase2` telle quelle dans `context.pipeline`,
3. renvoie `doc1.similarity(doc2)`.

Nuances importantes :

- contrairement a `jaccard` et `dice`, il n'y a pas de passage prealable en minuscules,
- le score n'est pas force dans `[0.0, 1.0]`,
- selon spaCy et le modele charge, `Doc.similarity(...)` repose sur des vecteurs et peut etre fortement degrade si ceux-ci sont absents,
- la valeur de `detail["vector_size"]` est prise sur `doc1.vector.shape[0]`,
- `detail["has_vector"]` vaut `doc1.has_vector and doc2.has_vector`.

Le `detail` n'est pas renvoye par l'API, donc ces informations restent internes.

## 9. Plugin actuel : `word_overlap`

Le seul plugin effectivement present dans `plugins/metrics/` est `WordOverlapMetric`.

Nom de registre : `word_overlap`

Son comportement exact est different des metriques natives :

1. remplace `None` par `""`,
2. met en minuscules,
3. decoupe simplement avec `.split()` sur les espaces,
4. transforme les listes en ensembles,
5. calcule :

```text
nombre_de_mots_communs / min(taille_ensemble_1, taille_ensemble_2)
```

Cas limites :

- deux ensembles vides -> `1.0`,
- un seul ensemble vide -> `0.0`.

Nuances importantes :

- pas de spaCy,
- pas de lemmatisation,
- pas de suppression de ponctuation,
- pas de suppression de stop words,
- les doublons sont ignores,
- le score est arrondi avec `round(score, 4)`.

Autrement dit, `word_overlap` n'est pas aligne sur le pretraitement linguistique des metriques `jaccard` et `dice`.

## 10. Registre des metriques

### 10.1 Structure

`MetricsRegistry` stocke les metriques dans `self._metrics`, un dictionnaire Python.

Le registre expose :

- `register(metric)`
- `get(name)`
- `list()`

### 10.2 Validation reelle

`register(metric)` appelle `_validate(metric)` puis fait :

```python
self._metrics[metric.name] = metric
```

La validation impose seulement :

- un attribut `name` non vide et de type `str`,
- une methode `compute` callable.

La description :

- est recommandee,
- mais non obligatoire,
- son absence provoque seulement un `print` d'avertissement.

Nuance importante :

- `MetricsRegistry` fonctionne en duck typing,
- un objet n'a pas besoin d'heriter de `BaseMetric` pour etre enregistre manuellement,
- en revanche, le chargeur automatique de plugins ne decouvre que des classes qui heritent de `BaseMetric`.

### 10.3 Collisions de noms

Si deux metriques ont le meme `name` :

- la derniere enregistree ecrase la precedente,
- aucune exception n'est levee,
- aucun message d'alerte specifique n'est emis.

Cela permet a un plugin d'ecraser une metrique native si le meme nom est reuse.

## 11. Chargeur de plugins

### 11.1 Strategie de decouverte

`load_plugins(plugins_dir="plugins/metrics")` :

1. construit `Path(plugins_dir)`,
2. verifie que le dossier existe,
3. liste les fichiers `*.py`,
4. trie ces fichiers,
5. ignore les fichiers dont le nom commence par `_`,
6. importe chaque fichier dynamiquement,
7. extrait les classes valides,
8. les instancie sans argument,
9. les enregistre dans `registry`.

Consignes implicites pour un plugin :

- etre un fichier Python directement dans `plugins/metrics/`,
- ne pas etre dans un sous-dossier,
- contenir au moins une classe definie localement,
- heriter de `BaseMetric`,
- pouvoir etre instanciee sans parametre,
- fournir un `name`,
- fournir une methode `compute`.

### 11.2 Import dynamique

Le module est importe avec un nom de type :

```text
plugins.metrics.<nom_du_fichier>
```

Avant le chargement, si ce nom existe deja dans `sys.modules`, il est supprime. Cela permet de recharger le module proprement dans le meme processus.

### 11.3 Extraction des classes

`_extract_metrics(module)` ne retient que les classes qui :

- sont des classes Python,
- sont des sous-classes de `BaseMetric`,
- ne sont pas `BaseMetric` elle-meme,
- sont definies dans le module courant.

Consequence :

- un fichier plugin qui importe une classe depuis un autre module et la re-exporte ne sera pas pris en compte.

### 11.4 Tolerance aux erreurs

Le chargeur est tolerant :

- si un fichier plugin casse a l'import -> fichier ignore, chargement continue,
- si une classe plugin echoue a l'instanciation ou a l'enregistrement -> classe ignoree, chargement continue.

En revanche :

- si `compute(...)` plante plus tard pendant une requete, le endpoint ne l'intercepte pas,
- on obtient alors une erreur serveur.

A la fin du chargement, le code affiche aussi un bilan console du type :

```text
Plugins : X charge(s), Y ignore(s).
```

## 12. Contrats de schemas API

### 12.1 `SimilarityRequest`

Definition effective :

- `phrase1: str`
- `phrase2: str`
- `metrics: list[str] = ["jaccard"]`
- `language: str = "fr"`

Bon point technique :

- `metrics` utilise `default_factory`, ce qui evite le piege du mutable par defaut partage entre instances.

Point exact du comportement :

- aucune contrainte ne force `metrics` a etre non vide,
- une requete avec `"metrics": []` renverra donc `200` avec `scores={}`.

### 12.2 `SimilarityResponse`

Definition effective :

- `scores: dict[str, float]`
- `metadata: dict = {}`

Ce schema reste assez permissif :

- `metadata` n'a pas de structure imposee,
- l'API n'expose pas les details des metriques,
- seul le score final est publie.

## 13. Gestion des erreurs et cas limites

### 13.1 Cas geres explicitement

| Situation | Comportement |
| --- | --- |
| `phrase1` ou `phrase2` absente | Erreur de validation FastAPI/Pydantic avant l'execution du endpoint. |
| langue inconnue | HTTP 400 avec message explicite. |
| metrique inconnue | HTTP 400 avec `Unknown metric: ...`. |
| modele spaCy absent | Fallback vers `spacy.blank(...)`, pas d'erreur HTTP. |
| plugin mal forme au chargement | Ignore avec message de console. |

### 13.2 Cas non geres explicitement

| Situation | Comportement probable |
| --- | --- |
| exception levee dans `metric.compute(...)` | Erreur serveur non interceptee. |
| collision de noms de metriques | Ecrasement silencieux. |
| chemin de plugins invalide a cause d'un mauvais repertoire courant | Aucun plugin charge, seulement un message `INFO` en console. |
| absence de vecteurs semantiques utiles pour `spacy_vector` | Score potentiellement peu informatif. |

## 14. Differences de normalisation entre metriques

Le projet ne calcule pas toutes les similarites sur la meme representation du texte.

| Metrique | Minuscules | Lemmatisation | Stop words retires | Ponctuation retiree | Doublons ignores | Depend spaCy |
| --- | --- | --- | --- | --- | --- | --- |
| `jaccard` | Oui | Oui | Oui | Oui | Oui | Oui |
| `dice` | Oui | Oui | Oui | Oui | Oui | Oui |
| `levenshtein` | Non | Non | Non | Non | Non | Non |
| `spacy_vector` | Non | Pipeline spaCy interne seulement | Non explicitement | Non explicitement | Non | Oui |
| `word_overlap` | Oui | Non | Non | Non | Oui | Non |

C'est un point essentiel pour comprendre les resultats :

- deux metriques demandees sur la meme paire de phrases ne comparent pas toujours la meme representation du texte,
- le mot "chat" avec et sans repetition n'a aucun impact sur `jaccard`, `dice` et `word_overlap`,
- la casse impacte `levenshtein`, mais pas `jaccard`, `dice` ni `word_overlap`.

## 15. Etat actuel des tests

### 15.1 Ce que les tests cherchent a verifier

Le dossier `tests/` couvre en theorie :

- la validation des schemas,
- la presence de metriques dans le registre,
- des proprietes de score sur les metriques natives,
- le comportement du endpoint API,
- le chargement et la validation de plugins.

### 15.2 Particularites reelles des fichiers de test

Le depot contient notamment :

- `tests/testApi.py`
- `tests/testMetrics.py`
- `tests/testRegistry.py`
- `tests/testShemas.py`
- `tests/testsPlugins.py`

Nuances importantes :

- plusieurs noms de fichiers ne suivent pas la convention pytest standard `test_*.py`,
- aucune configuration `pytest.ini` n'est presente pour elargir la decouverte,
- plusieurs fichiers appellent directement leurs fonctions de test en bas du module,
- `testShemas.py` contient une faute dans le nom (`Shemas` au lieu de `Schemas`),
- `tests/testsPlugins.py` attend des plugins qui ne sont pas presents dans le depot actuel : `length_ratio`, `prefix`, `common_bigrams`.

Consequence :

- l'etat des tests tel qu'ecrit ne constitue pas une suite pytest proprement normalisee,
- certains tests semblent penses pour etre lances a la main, comme le README l'indique,
- la couverture plugin decrite par `tests/testsPlugins.py` est en decalage avec le contenu reel de `plugins/metrics/`.

## 16. Ce que le projet fait bien

- L'architecture est simple a suivre.
- Le coeur metrique est separe des endpoints HTTP.
- Le systeme de langues est extensible sans refonte majeure.
- Le chargement des pipelines spaCy est paresseux.
- Le systeme de plugins permet d'ajouter des metriques sans toucher au routeur API.
- Les metriques natives respectent toutes la meme signature `compute(...)`.

## 17. Limites et zones d'attention du depot actuel

### 17.1 Limites fonctionnelles

- Une seule langue est effectivement active.
- `embedding_model` n'est pas exploite.
- L'API ne renvoie pas les `detail` calcules par les metriques.
- Il n'existe pas d'endpoint pour lister les metriques disponibles.
- Il n'existe pas de persistance, d'authentification, ni d'interface front.

### 17.2 Limites techniques

- Le chemin des plugins depend du repertoire de lancement.
- Les logs sont de simples `print(...)`.
- Les collisions de noms de metriques ne sont pas surveillees.
- Les objets metriques sont globaux et partages.
- Le fallback spaCy vide peut changer fortement le sens des resultats.

### 17.3 Limites de qualite logicielle

- La suite de tests n'est pas parfaitement alignee avec les conventions pytest.
- Certains tests ciblent des plugins absents du depot actuel.
- Le comportement de runtime d'un plugin n'est pas protege par un `try/except` dans le endpoint.

## 18. Resume mental tres court

Si on reduit tout le projet a un schema simple, il fonctionne comme ceci :

1. FastAPI recoit deux phrases et une liste de metriques.
2. Pydantic valide la charge utile.
3. `LanguageManager` fournit un pipeline spaCy pour la langue demandee.
4. `registry` retrouve les metriques natives ou plugin.
5. Chaque metrique calcule un score selon sa propre logique de normalisation.
6. L'API ne renvoie que les scores et un minimum de metadonnees.

## 19. Conclusion

Le projet est aujourd'hui une API de calcul de similarite textuelle basee sur :

- un noyau FastAPI minimal,
- un registre global de metriques,
- un gestionnaire de langues avec chargement paresseux spaCy,
- des metriques natives heterogenes,
- un mecanisme de plugins dynamiques.

Le point le plus important a retenir est le suivant :

le projet parait uniforme vu de l'exterieur, mais en interne chaque metrique travaille sur une representation differente du texte, et plusieurs details de fonctionnement reposent sur des effets de bord d'import, des objets globaux et des conventions implicites de lancement.
