from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import router
from app.core.loader_utils import PROJECT_ROOT
from app.core.language_loader import load_languages
from app.core.model_loader import load_models
from app.core.plugin_loader import load_plugins
from app.web.routes import router as web_router


app = FastAPI(title="Semantic Similarity API")
app.mount(
    "/static",
    StaticFiles(directory=str(PROJECT_ROOT / "app" / "static")),
    name="static",
)
app.include_router(router)
app.include_router(web_router)

# Chargement déclaratif au démarrage, sans chargement ML lourd.
load_languages("plugins/languages")
load_models("plugins/models")
load_plugins("plugins/metrics")
