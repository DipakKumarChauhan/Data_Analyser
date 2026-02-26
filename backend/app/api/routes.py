
from fastapi import APIRouter
from app.core.dataset_manager import dataset_manager

router = APIRouter()


@router.get('/health')
def health_check():
    return {"status": "ok"}

@router.get('/dataset-schema')

def dataset_schema():
    schema = dataset_manager.get_schema()
    return schema


