import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from dotenv import load_dotenv, find_dotenv
import os
from typing import Optional

# Cargar variables de entorno
load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)

def download_blob_to_file(storage_account_name, storage_account_key, container_name, blob_name, local_path):
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=storage_account_key
    )
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    
    with open(local_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())

def list_blobs_flat(storage_account_name, storage_account_key, container_name):
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=storage_account_key
    )
    container_client = blob_service_client.get_container_client(container_name)
    return container_client.list_blobs()

def download_pdf_from_blob(storage_account_name, storage_account_key, container_name, blob_name, local_path):
    try:
        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=storage_account_key
        )
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        if os.path.getsize(local_path) == 0:
            raise ValueError(f"El archivo descargado '{local_path}' está vacío.")
    except ResourceNotFoundError:
        print(f"El blob '{blob_name}' no existe en el contenedor '{container_name}'.")
    except ClientAuthenticationError as e:
        print(f"Error de autenticación: {e}")
    except Exception as e:
        print(f"Error descargando el blob: {e}")

# --- Inicio :: FUNCIONES LOCALES (Simulación de "descarga") ---

def list_files_local(local_source_dir):
    # Imprime el directorio de trabajo actual
    current_dir = os.getcwd()
    logger.info(f"--- Directorio de trabajo actual (CWD): {current_dir}")
    # Verifica la ruta absoluta que intenta buscar
    absolute_source = os.path.abspath(local_source_dir)
    logger.info(f"--- INFO: Buscando archivos en ruta absoluta: {absolute_source} ---")
    if not os.path.exists(local_source_dir):
        logger.error(f"El directorio local de origen '{local_source_dir}' no existe.")
        exit(1)
    for f in os.listdir(local_source_dir):
        file_path = os.path.join(local_source_dir, f)
        if os.path.isfile(file_path):
            logger.info(f"Archivo encontrado: {file_path}")
    return [f for f in os.listdir(local_source_dir) if os.path.isfile(os.path.join(local_source_dir, f))]

# def copy_local_file(source_dir, file_name, dest_path):
#     os.makedirs(os.path.dirname(dest_path), exist_ok=True)
#     shutil.copy2(os.path.join(source_dir, file_name), dest_path)
#     #shutil ::  Está pensado para automatizar tareas más complejas que el modulo os,
#     #          como copiar archivos con metadatos, mover directorios completos, etc. 
#     #         Es más robusto y maneja mejor los errores que simplemente abrir y escribir archivos.

# --- Fin :: FUNCIONES LOCALES (Simulación de "descarga") ---


#if __name__ == "__main__":
def main_download(download_dir:Optional[str]=None, storage_account_name:Optional[str]=None, storage_account_key:Optional[str]=None, container_name:Optional[str]=None, blob_prefix:Optional[str]=None):
    if not storage_account_name:
        storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    if not storage_account_key:
        storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    if not container_name:
        container_name = os.getenv("AZURE_CONTAINER_NAME")
    if not download_dir:
        download_dir = os.getenv("DOWNLOAD_DIR")

    if not all([storage_account_name, storage_account_key, container_name, download_dir]):
        print("Por favor, asegúrate de que las siguientes variables de entorno estén definidas: AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_ACCOUNT_KEY, AZURE_CONTAINER_NAME, DOWNLOAD_DIR")
        exit(1)
    
    try:
        blob_names = list(list_blobs_flat(storage_account_name, storage_account_key, container_name))
        logging.info(f"Número total de blobs encontrados: {len(blob_names)}")
        logging.info(f"Nombres de blobs: {[blob.name for blob in blob_names]}")
        
        for blob in blob_names:
            blob_name = blob.name
            
            # Filtrar por prefijo si se especifica
            if blob_prefix and not blob_name.startswith(blob_prefix):
                logging.info(f"Saltando blob '{blob_name}' (no coincide con prefijo '{blob_prefix}')")
                continue
            
            print(f"Descargando blob: {blob_name}")
            download_file_path = os.path.join(download_dir, os.path.basename(blob_name))
            download_pdf_from_blob(storage_account_name, storage_account_key, container_name, blob_name, download_file_path)
    except ClientAuthenticationError as e:
        print(f"Error de autenticación: {e}")
    except Exception as e:
        print(f"Error al listar o descargar blobs: {e}")
