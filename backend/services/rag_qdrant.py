from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain_qdrant import Qdrant
from langchain.schema import Document
from services.azure_document_intelligence import extract_text_with_azure_math
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)    

def validate_and_create_collection(client,collection_name,vector_size): 
    try:
        client.get_collection(collection_name)
        logger.info(f" La Coleccion '{collection_name}' ya existe ")
    except UnexpectedResponse as e:
        logger.info(f" La Coleccion '{collection_name}' NO existe ")
        if "not found" in str(e).lower():
            try:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
                )
                logger.info("Coleccion '{collection_name}' creada exitosamente")
            except Exception as e:
                logger.error(f"Error al crear la coleccion {collection_name}:{e}")
                raise
        else:
            logger.error(f"Error Inesperado:{e}")
            raise
    except Exception as e: 
        logger.error(f"No se comprobo que la coleccion '{collection_name}' exista")
        raise
        
import tempfile
        
def load_and_split_documents(folder_path):
    try:
        print(f"Cargando y fragmentando documentos desde: {folder_path}")
        split_docs = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
        
        for filename in os.listdir(folder_path):
            print("Procesando archivo:", filename )
            if filename.endswith('.pdf'):
                file_path = os.path.join(folder_path, filename)
                try:
                    # extract_text_with_azure_math retorna lista de {text, page}
                    pages_data = extract_text_with_azure_math(file_path)
                    if not pages_data:
                        logger.error(f"Sin páginas extraídas de {file_path}.")
                        continue

                    # Procesar cada página individualmente
                    for page_data in pages_data:
                        page_text = page_data['text']
                        page_num = page_data['page']
                        
                        if not page_text.strip():
                            continue
                        
                        # Crear documento con metadata: source y page
                        document = Document(
                            page_content=page_text,
                            metadata={"source": filename, "page": page_num}
                        )
                        # Fragmentar y extender
                        split_docs.extend(text_splitter.split_documents([document]))
                    
                    logger.info(f"Procesado {filename}: {len(pages_data)} páginas")
                except Exception as file_e:
                    logger.error(f"Error al cargar '{file_path}': {file_e}")
                    raise
        if not split_docs:
            raise ValueError("Documentos sin fragmentar.")
        logger.info(f"Total fragmentos creados: {len(split_docs)}")
        return split_docs
    except Exception as e:
        logger.error(f"Error al cargar y fragmentar archivos '{folder_path}': {e}")
        raise

def generate_embeddings(documents,azure_key,expected_dimension=1536):
    
    try:
        
        texts = [document.page_content for document in documents]
        embeddings = azure_key.embed_documents(texts)
        logger.info(f"Generated embeddings for {len(documents)} documents.")
    

        for embedding in embeddings:
            if len(embedding) != expected_dimension:
                raise ValueError(f"Generando la dimension del embedding {len(embedding)} no es igual a {expected_dimension}")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise

from qdrant_client.models import PointStruct


def upsert_documents(client, collection_name, embeddings, documents):
    try:
        if not embeddings or not documents:
            raise ValueError("Embeddings or Documents vacios")
        points = []
        for i, (embedding, doc) in enumerate(zip(embeddings, documents)):
            # Crear payload con page_content y TODOS los metadatos
            payload = {
                "page_content": doc.page_content,
                "metadata": doc.metadata  # Incluye source, page, etc.
            }
            point = PointStruct(
                id=i,
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        client.upsert(collection_name=collection_name, points=points)
        logger.info(f"Upserted {len(points)} documents into the collection '{collection_name}'.")
    except Exception as e:
        logger.error(f"Failed to upsert documents into the collection '{collection_name}': {e}")
        raise

def initializate_qdrant(client,collection_name,embedding_function):
    logger.info("  def initializate_qdrant(client,collection_name,embedding_function): ")
    logger.info(f" initializate_qdrant.cliente de Qdrant: {client}")
    logger.info(f" initializate_qdrant.Inicializando Qdrant para la colección '{collection_name}'")
    logger.info(f" initializate_qdrant.Embedding function: {embedding_function}")
    try:
        qdrant = Qdrant(
            client=client,
            collection_name=collection_name,    
            embeddings=embedding_function,
            content_payload_key="page_content",
            metadata_payload_key="metadata"  # Tomar metadatos de la llave metadata
        )
        logger.info(f"  initializate_qdrant.Qdrant Inizialidado para la coleccion '{collection_name}'")
        return qdrant
    except Exception as e:
        logger.error(f'  initializate_qdrant.Fallo al inicializar Qdrant:{e}')
        raise
