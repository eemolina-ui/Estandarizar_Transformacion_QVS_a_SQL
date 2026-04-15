from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import chat, voices
from core.config import settings
from core.logging_config import setup_logging

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar logging
setup_logging()

# Incluir routers
app.include_router(chat.router)
app.include_router(voices.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Avatar API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)    