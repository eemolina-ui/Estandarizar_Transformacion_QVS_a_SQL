from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv, find_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv(find_dotenv())

def is_noise(text_linea, polygon, page_height, page_width):
    """
    Función para determinar si un texto es ruido o no relevante.
    Para ello revisa:
     1. si el texto esta muy arriba 
     2. Si el texto esta muy abajo de la página
     3. Si el texto esta dentro de la lista de textos no relevantes
    """
    # Patrones de texto no relevante
    noise_keywords = ['g.c.a.b.a. | ministerio de educación', 'volver al itinerario de actividades']
    
    # Obtener coordenadas, solo nos interesa y
    y = polygon[0].y
    
    # Normalizar coordenadas a porcentajes
    relative_y = y / page_height if page_height > 0 else 0

    # 1. Filtrar si está muy arriba (top 11% = 0.11)
    if relative_y < 0.11:
        return True  # Encabezado/banner
    
    # 2. Filtrar si está muy abajo (bottom 8% = 0.92)
    if relative_y > 0.92:
        return True  # Pie de página
    
    # 3. Filtrar por contenido no relevante
    content = text_linea.lower()
    
    if any(keyword in content for keyword in noise_keywords):
        return True
    
    return False

class ExtractionConfig:
    """
    Configuración de cómo procesar el PDF.
    - skip_first_n_pages: cuántas páginas iniciales NO procesar (0 = ninguna).
    - skip_last_page: si se debe saltar la última página procesada.
    - use_noise_filter: si se aplica el filtro is_noise.
    """
    def __init__(self, skip_first_n_pages: int = 5, skip_last_page: bool = True, use_noise_filter: bool = True):
        self.skip_first_n_pages = skip_first_n_pages
        self.skip_last_page = skip_last_page
        self.use_noise_filter = use_noise_filter

def build_extraction_config(pdf_path):
    """
    Devuelve la configuración de extracción según el nombre del archivo.

    Regla de ejemplo:
    - Si el nombre empieza con 'doc-externa_', NO se saltan páginas ni se aplica is_noise.
    - Para el resto, se aplican las reglas actuales (saltear primeras 5, saltear última, usar is_noise).
    """
    filename = os.path.basename(pdf_path).lower()
    
    if filename.startswith("doc-externa_"):
        return ExtractionConfig(
            skip_first_n_pages=0,
            skip_last_page=False,
            use_noise_filter=False,
        )
    
    # Configuración por defecto
    return ExtractionConfig()

def extract_text_with_azure_math(pdf_path):
    """
    Extrae texto de un PDF usando Azure Document Intelligence,
    filtrando líneas no relevantes basadas en su posición y contenido.
    
    Returns:
        list[dict]: Lista de diccionarios con formato {'text': str, 'page': int}

    NOTAS:
    - Se procesan solo las páginas desde la 5 en adelante.
    - Se omite la última página del documento ya que tiene solo un banner.
    - Por el momento solo puede procesar documentos de matematica del volumne 4, si se quiere usar otros documentos habria que validar si sigue la misma estructura.
    """
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Obtener configuración según el nombre del archivo
    config = build_extraction_config(pdf_path)

    pages_param = None
    if config.skip_first_n_pages > 0:
        start_page = config.skip_first_n_pages
        pages_param = f"{start_page}-"

    with open(pdf_path, "rb") as f:
        if pages_param:
            poller = client.begin_analyze_document(
                "prebuilt-read",
                document=f,
                pages=pages_param
            )
        else:
            # Procesar todas las páginas
            poller = client.begin_analyze_document(
                "prebuilt-read",
                document=f
            )

    result = poller.result()

    ultima_pagina = result.pages[-1].page_number

    # Retornar lista de diccionarios con texto y número de página
    pages_data = []
    for page in result.pages:
        if config.skip_last_page:
            # Saltar la última página
            if page.page_number == ultima_pagina:
                continue
        
        page_lines = []
        
        # Iterar sobre cada línea de texto
        for line in page.lines:

            # Aplicar filtro de ruido si está habilitado
            if config.use_noise_filter:
            # Llamar a is_noise con los parámetros correctos
                if is_noise(
                    text_linea=line.content,      # El texto de la línea
                    polygon=line.polygon,          # Las coordenadas de la línea
                    page_height=page.height,       # Alto de la página (14.2222 inches)
                    page_width=page.width          # Ancho de la página (10.6667 inches)
                ):
                    continue  # Saltar esta línea (es basura)
            
            # Línea válida - agregar al resultado
            page_lines.append(line.content)
        
        # Agregar el texto de la página con su número
        if page_lines:
            pages_data.append({
                'text': "\n".join(page_lines),
                'page': page.page_number
            })
    
    return pages_data