from fastapi import APIRouter, Query
from typing import Optional, List

from models import WordEntry, ProverbEntry
from data_loader import get_words, get_proverbs, get_districts

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/districts", response_model=List[str])
def list_districts():
    return get_districts()


@router.get("/words", response_model=List[WordEntry])
def list_words(district: Optional[str] = Query(default=None)):
    return get_words(district)


@router.get("/proverbs", response_model=List[ProverbEntry])
def list_proverbs(district: Optional[str] = Query(default=None)):
    return get_proverbs(district)
