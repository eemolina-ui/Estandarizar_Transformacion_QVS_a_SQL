# Dockerfile para FastAPI con soporte para Chronos usando Python 3.11
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos de requerimientos e instalar dependencias
COPY ./bdd/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los archivos de la aplicación
COPY ./bdd/app /app

# Exponer el puerto de la aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

