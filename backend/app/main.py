from fastapi import FastAPI
from app.config import settings

from app.core.dataset_manager import dataset_manager
from app.core.session_manager import session_manager

from app.api.routes import router

from fastapi.middleware.cors import CORSMiddleware



app =  FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OK for assignment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('startup')
def startup_event():
    dataset_manager.load_titanic_dataset()
    session_manager.initialize_default_session(dataset_manager)


    

app.include_router(router)
