import logging
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from pydantic import BaseModel
from typing import List, AsyncGenerator
from langchain_core.messages import AIMessage, HumanMessage
from services.azure_tts_service import azure_t2speech_streaming
from services.register_data_service import register_contact_data
import json
import base64
from agents.agents import MultiAgentsBot
from qdrant_client import QdrantClient
from services.download_pdfs_from_azure import main_download
from services.rag_qdrant import (validate_and_create_collection, 
                                         load_and_split_documents,
                                         generate_embeddings,
                                         upsert_documents,
                                         initializate_qdrant)
import os
import re

router = APIRouter()
logger = logging.getLogger(__name__)

logger.info("Initializing chat endpoint...")

async def stream_response(generator: AsyncGenerator) -> AsyncGenerator[bytes, None]:
    """
    Wrapper to properly format and validate each streamed response
    """
    try:
        async for message in generator:
            if isinstance(message, dict):
                # Ensure message has all required fields
                required_fields = {'text', 'audio', 'lipsync', 'facialExpression', 'animation'}
                for field in required_fields:
                    if field not in message:
                        message[field] = None
                
                # Convert to JSON and encode
                yield (json.dumps(message, ensure_ascii=False) + '\n').encode('utf-8')
            elif isinstance(message, bytes):
                # Already encoded message
                yield message
            else:
                logging.warning(f"Unexpected message type: {type(message)}")
                continue
    except Exception as e:
        logging.error(f"Error in stream_response: {str(e)}")
        error_message = {
            'text': 'Lo siento, hubo un error en el procesamiento.',
            'facialExpression': 'sad',
            'animation': 'Talking_0',
            'error': True
        }
        yield (json.dumps(error_message, ensure_ascii=False) + '\n').encode('utf-8')

router = APIRouter()
logger = logging.getLogger(__name__)

CLIENTE_QDRANT_HOST=os.environ.get('QDRANT_HOST', 'qdrant')
CLIENTE_QDRANT_PORT=int(os.environ.get('QDRANT_PORT', 6333))
CLIENTE_QDRANT_COLLECTION_NAME=os.environ.get('QDRANT_COLLECTION_NAME', 'corporativo')

print(f"CLIENTE_QDRANT_HOST={CLIENTE_QDRANT_HOST}")
print(f"CLIENTE_QDRANT_PORT={CLIENTE_QDRANT_PORT}")
print(f"CLIENTE_QDRANT_COLLECTION_NAME={CLIENTE_QDRANT_COLLECTION_NAME}")

client = QdrantClient(host=CLIENTE_QDRANT_HOST, port=CLIENTE_QDRANT_PORT, timeout=60.0)

PseudoAgentsIngrid = MultiAgentsBot(vdb_client=client, data_analyst=None)
embeddings_model_runnable = PseudoAgentsIngrid.embeddings_model_runnable

# Cargamos en qdrant coleccion corporativa
COLLECTION_CORPORATIVO = os.environ.get('QDRANT_COLLECTION_CORPORATIVO', 'asistente_corporativo')

# Número de vecinos a recuperar de Qdrant
QDRANT_K = int(os.environ.get('QDRANT_K', 8))
logger.info(f"Using QDRANT_K={QDRANT_K}")

qdrant_corporativo = initializate_qdrant(client, COLLECTION_CORPORATIVO, embeddings_model_runnable)
retriever_corporativo = qdrant_corporativo.as_retriever(search_kwargs={"k": QDRANT_K})

# corporativo
validate_and_create_collection(collection_name=COLLECTION_CORPORATIVO, vector_size=1536, client=client)
document_count_lit = client.get_collection(COLLECTION_CORPORATIVO).points_count

if document_count_lit > 0:
    print(f"La colección '{COLLECTION_CORPORATIVO}' ya tiene {document_count_lit} documentos.")
else:
    corporativo_dir = os.path.join(os.environ['DOWNLOAD_DIR'], 'literatura')
    main_download(download_dir=corporativo_dir, blob_prefix='literatura/')
    
    split_documents_lit = load_and_split_documents(corporativo_dir)
    embeddings_lit = generate_embeddings(documents=split_documents_lit, azure_key=embeddings_model_runnable, expected_dimension=1536)
    upsert_documents(client, COLLECTION_CORPORATIVO, embeddings_lit, split_documents_lit)

chat_history = dict({})

class ChatRequest(BaseModel):
    message: str
    image: str
    coordinates: str=None
    userId: str=None


class ChatResponse(BaseModel):
    messages: list[dict]

#@router.post("/chat", response_model=ChatResponse)
async def chat_streaming(chat_request: ChatRequest):
    logger.info(f"Received chat request: {chat_request.message}")
    if chat_request.userId not in chat_history:
        chat_history[chat_request.userId] = []
    chat_history[chat_request.userId].append(HumanMessage(chat_request.message))
    
    
    leng_history_limit = int(os.getenv('CONVERSATION_HISTORY_LENGTH', 16))

    option_bools = {
        'Inicio':False,
        'Rag_corporativo':False,
        'Generic':False,
        }

    case = PseudoAgentsIngrid.query_classifier(query=chat_request.message)
    logger.info("case= " + case)
    option_bools[case] = True
    
    async def process_intermediate_message(text):
            messages = {'text': text}
            audio, lipsync = azure_t2speech_streaming(messages['text'])
            messages['audio'] = base64.b64encode(audio).decode('utf-8')
            messages['lipsync'] = lipsync
            messages['facialExpression'] = 'default'
            messages['animation'] = 'Talking_0'
            yield (json.dumps(messages) + '\n').encode('utf-8')
    
    if option_bools['Inicio']:
        logger.info(">Inicio ")
        response = PseudoAgentsIngrid.query_waving(chat_history[chat_request.userId][-leng_history_limit:])
    elif option_bools['Generic']:
        logger.info(">Generic ")
        response = PseudoAgentsIngrid.query_generic(chat_history[chat_request.userId][-leng_history_limit:])
    elif option_bools['Rag_corporativo']:
        logger.info(">Rag_corporativo ")
        response = PseudoAgentsIngrid.query_rag(
            str(chat_history[chat_request.userId][-leng_history_limit:]), 
            retriever_corporativo,
        )
    else:
        logger.info(">Default ")
        messages = {'text':'No comprendo tu pregunta. ¿Podrías reformularla por favor?'}
        audio, lipsync = azure_t2speech_streaming(messages['text'])
        
        messages['audio'] = base64.b64encode(audio).decode('utf-8')
        messages['lipsync'] = lipsync
        messages['facialExpression'] = 'default'
        messages['animation'] = 'Talking_0'
        yield (json.dumps(messages) + '\n').encode('utf-8')

    logger.info("Conversation: " + str(chat_history[chat_request.userId][-8:]))
    logger.info("Response: " + str(response))
    
    # Extraer sources si existen (de respuestas RAG)
    sources = []
    if isinstance(response, dict) and 'sources' in response:
        sources = response['sources']
        response = response['answer']
    
    if isinstance(response, str):
        try:
            messages = json.loads(response)
        except:
            logger.warning("Response is not a JSON")
            logger.warning("Response: ", response)
            try:
                messages = re.sub(r"```json\{.*\})```", r"\1", response)
                messages = json.loads(messages)
                logger.info(f"Messages: {messages}")
            except:
                logger.error("Response is not a JSON")
                messages = {'text':response}
    if isinstance(response, dict):
        messages = response
    
    # Agregar sources al mensaje
    messages['sources'] = sources
    try:
        audio, lipsync = azure_t2speech_streaming(messages['text'])

        messages['audio'] = base64.b64encode(audio).decode('utf-8')
        messages['lipsync'] = lipsync
        messages['facialExpression'] = messages.get('facialExpression', 'default')
        messages['animation'] = messages.get('animation', 'Talking_0')
        chat_history[chat_request.userId].append(AIMessage(content=messages['text']))
        
        # Log del historial después de agregar respuesta de la IA
        logger.info(f"[MEMORY TRACKING] Response added | User: {chat_request.userId[:8]}... | Total messages: {len(chat_history[chat_request.userId])}")
        logger.info(f"[MEMORY TRACKING] Recent context (last 8): {[msg.content[:50] + '...' if len(msg.content) > 50 else msg.content for msg in chat_history[chat_request.userId][-8:]]}")
        
        yield (json.dumps(messages) + '\n').encode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred processing your request: {e}")


@router.post("/chat")
async def chat(chat_request: ChatRequest):
    try:
        # Set response headers for proper streaming
        headers = {
            'Content-Type': 'application/x-ndjson',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
        
        return StreamingResponse(
            stream_response(chat_streaming(chat_request)),
            headers=headers,
            media_type="application/x-ndjson"
        )
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        error_message = {
            'text': 'No comprendo tu pregunta. ¿Podrías reformularla por favor?',
            'facialExpression': 'sad',
            'animation': 'Talking_0',
            'error': True
        }
        return Response(
            content=json.dumps(error_message, ensure_ascii=False),
            media_type="application/json"
        )