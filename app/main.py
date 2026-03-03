# app/main.py
from fastapi import FastAPI
from app.api.endpoints import router
from app.core.language_manager import language_manager  # init langues
from app.core.plugin_loader import load_plugins          # charge les plugins

app = FastAPI(title="Semantic Similarity API")
app.include_router(router)

# Chargement des plugins au démarrage
load_plugins("plugins/metrics")