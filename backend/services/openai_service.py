import json
import logging
from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)
#logger = logging.get#logger(__name__)

async def generate_chat_response(user_message: str, image_data: str, system_message: str):
    #logger.info("Sending request to OpenAI")
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": [
                    {
                        'type': 'text',
                        'text': user_message
                    },
                    {
                        'type': 'image_url',
                        'image_url': {'url': f'{image_data}'} if image_data else None
                    }
                    ]
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.6, 
            n=1
        )
        #logger.info("Received response from OpenAI")

        messages = json.loads(chat_completion.choices[0].message.content)
        if 'messages' in messages:
            messages = messages['messages']
        
        return messages
    except Exception as e:
        raise