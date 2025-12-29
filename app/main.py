# app/main.py
from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI(title="Semantic Similarity API")
app.include_router(router)
