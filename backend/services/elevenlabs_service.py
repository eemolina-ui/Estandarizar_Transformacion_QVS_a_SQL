import logging
import requests
from core.config import settings

#logger = logging.get#logger(__name__)

async def get_voices():
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "Accept": "application/json",
        "xi-api-key": settings.ELEVEN_LABS_API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        #logger.info("Successfully retrieved voices from ElevenLabs")
        return response.json()
    except requests.RequestException as e:
        #logger.error(f"Error retrieving voices from ElevenLabs: {str(e)}")
        raise

async def text_to_speech(text: str, file_name: str):
    #logger.info(f"Converting text to speech: {text[:50]}...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": settings.ELEVEN_LABS_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        with open(file_name, 'wb') as f:
            f.write(response.content)
        #logger.info(f"Successfully generated speech and saved to {file_name}")
    except requests.RequestException as e:
        #logger.error(f"Error in text-to-speech conversion: {str(e)}")
        raise