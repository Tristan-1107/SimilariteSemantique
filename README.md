# SimilariteSemantique
Ce projet consiste à développer une plateforme web capable de calculer la similarité sémantique entre deux phrases en langue française. L’objectif est de proposer un service en ligne qui combine plusieurs approches du Traitement Automatique des Langues afin de mesurer à quel point deux phrases expriment un sens proche.


INSTRUCTIONS D’UTILISATION DU PROJET

Après avoir cloné le dépôt Git :

1) Se placer à la racine du projet
cd SimilariteSemantique

2) Créer et activer l’environnement virtuel
python3 -m venv venv
source venv/bin/activate

3) Installer les dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt

4) Lancer l’API
python3 -m uvicorn app.main:app --reload

5) Accéder à l’API
http://127.0.0.1:8000/docs

6) Tester l’API (exemple)
POST /similarity
{
  "phrase1": "chat noir",
  "phrase2": "chat blanc",
  "metrics": ["jaccard", "dice", "levenshtein"]
}

7) Lancer les tests (depuis la racine du projet)
python3 -m tests.testApi
python3 -m tests.testMetrics
python3 -m tests.testRegistry
python3 -m tests.testSchemas

IMPORTANT :
Les tests doivent être lancés avec "python3 -m".
Ne pas utiliser "python3 fichier.py".
