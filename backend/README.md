# Avatar Backend

el backend del proyecto en FastAPI y modularizado para su futura edicion y poder agregar nuevos modulos facilmente.

## Estructura del proyecto

```
de_avatar_lp_backend/
│
├── api/
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── voices.py
│
├── core/
│   ├── config.py
│   └── logging_config.py
│
├── services/
│   ├── openai_service.py
│   ├── elevenlabs_service.py
│   └── lip_sync_service.py
│
├── templates/
│   └── sys_message.py
│
├── utils/
│   └── audio_utils.py
│
├── audios/
├── .env
├── main.py
├── README.md
└── requirements.txt
```

La estructura del proyecto está diseñada para maximizar la modularidad y la separación de responsabilidades. 
* El directorio `api` contiene los endpoints de la aplicación, organizados por funcionalidad. 
* El directorio  `core` alberga configuraciones centrales y ajustes de logging. 
* El directorio  `services` encapsula la lógica de interacción con servicios externos como OpenAI y ElevenLabs. 
* El directorio  `templates` almacena prompts del sistema reutilizables.
* El directorio  `utils` contiene funciones de utilidad compartidas

![Video Thumbnail](https://img.youtube.com/vi/EzzcEL_1o9o/maxresdefault.jpg)

[Video tutorial](https://youtu.be/EzzcEL_1o9o)

The frontend is [here](https://github.com/wass08/r3f-virtual-girlfriend-frontend).

## Setup
Create a `.env` file at the root of the repository to add your **OpenAI** and **ElevenLabs API Keys**. Refer to `.env.example` for the environment variable names.

Download the **RhubarbLibrary** binary for your **OS** [here](https://github.com/DanielSWolf/rhubarb-lip-sync/releases) and ensure it's accessible in your system PATH.

Install dependencies and start the development server with:
```
pip install -r requirements.txt
uvicorn main:app --reload
```

## Running with Docker
To build and run the Docker container:

1. Build the image:
   ```
   docker build -t avatar-backend .
   ```
2. Run the container:
   ```
   docker run -p 3000:3000 avatar-backend
   ```

The API will be available at `http://localhost:3000`. You can access the interactive API documentation at `http://localhost:3000/docs`.