from fastapi import FastAPI

from app.api.endpoints import router
from app.core.language_loader import load_languages
from app.core.model_loader import load_models
from app.core.plugin_loader import load_plugins


app = FastAPI(title="Semantic Similarity API")
app.include_router(router)

# Chargement déclaratif au démarrage, sans chargement ML lourd.
load_languages("plugins/languages")
load_models("plugins/models")
load_plugins("plugins/metrics")
