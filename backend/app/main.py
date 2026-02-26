from fastapi import FastAPI
from app.config import settings
from app.core.dataset_manager import dataset_manager
from app.api.routes import router

app =  FastAPI(title=settings.APP_NAME)

@app.on_event('startup')
def startup_event():
    dataset_manager.load_titanic_dataset()

app.include_router(router)
