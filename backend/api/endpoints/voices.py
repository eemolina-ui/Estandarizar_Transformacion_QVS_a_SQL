import logging
from fastapi import APIRouter, HTTPException
from services.elevenlabs_service import get_voices

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/voices")
async def voices():
    #logger.info("Received request to /voices endpoint")
    try:
        return await get_voices()
    except Exception as e:
        logger.error(f"Error retrieving voices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve voices")