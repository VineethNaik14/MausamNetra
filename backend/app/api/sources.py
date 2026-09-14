from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db_session
from app.repositories.source_repository import SourceRepository
from app.schemas.common import ApiResponse
from app.schemas.source import SourceRead

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=ApiResponse[list[SourceRead]], summary="List active report sources")
def list_sources(db: Session = Depends(get_db_session)):
    sources = SourceRepository(db).list_active()
    return ApiResponse(data=[SourceRead.model_validate(s) for s in sources])