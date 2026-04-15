from openai import AzureOpenAI
from qdrant_client import QdrantClient

print("Generando embedding con Azure OpenAI...")

QDRANT_URL = "http://localhost:6333"
COLLECTION = "asistente_corporativo"

client = AzureOpenAI(
    api_key="5Ii96AvSXS8KjcOScYaKaWo9LbXz2nxF0gZZZCIABoTz6eODX5PcJQQJ99BKACYeBjFXJ3w3AAAAACOGdgmk",
    azure_endpoint="https://goed-avatar-foundry.cognitiveservices.azure.com/",
    api_version="2024-12-01-preview"
)

def generar_embedding(texto):
    resp = client.embeddings.create(
        model="alicia-embeddings",
        input=texto )
    vector = resp.data[0].embedding    
    return vector

# ---- 2. Hacer búsqueda en Qdrant (opcional) ----
def buscar_en_qdrant(query_vector, top_k=5):
    qdrant = QdrantClient(url=QDRANT_URL)
    
    resultado = qdrant.query_points(query=query_vector, collection_name=COLLECTION, limit=top_k)

    print("\n=== RESULTADOS DE LA BÚSQUEDA EN QDRANT ===\n")

    for point in resultado.points:
        print("ID:", point.id)
        print("Score:", point.score)
        print("Payload:", point.payload)
        print("-------------------------")        
            
  

# ----------- Prueba -------------- ----

texto = "me podrías ayudar con la leyenda del familiar"
vector = generar_embedding(texto)
buscar_en_qdrant(vector)


