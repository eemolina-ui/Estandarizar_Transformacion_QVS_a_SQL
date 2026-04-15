# Imagen base
FROM python:3.11-bookworm

WORKDIR /app

# ==========================================================
# INYECCIÓN DEL CERTIFICADO DE CADENA COMPLETA (Solución SSL)
# Asegúrate que 'cadena.crt' esté en el mismo directorio.
COPY cadena.crt /usr/local/share/ca-certificates/cadena.crt
# Fuerza la actualización de los certificados del sistema para confiar en 'cadena.crt'
RUN update-ca-certificates --fresh
 
# Variable de entorno que indica a Python/Requests usar el almacén del sistema
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
# ==========================================================

# Dependencias del sistema
# Nota: en Debian 12 (bookworm) existe libssl3; en Debian 11 usar libssl1.1
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    openssl \
    libcurl4 \
    libnss3 \
    libgssapi-krb5-2 \
    libasound2 \
    libasound2-plugins \
    libpulse0 \
    ffmpeg \
    unzip \
    wget \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# (Opcional) Rhubarb Lip Sync
RUN wget https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.13.0/Rhubarb-Lip-Sync-1.13.0-Linux.zip && \
 unzip Rhubarb-Lip-Sync-1.13.0-Linux.zip && \
 mkdir -p /opt/rhubarb && \
 mv Rhubarb-Lip-Sync-1.13.0-Linux/* /opt/rhubarb/ && \
 chmod +x /opt/rhubarb/rhubarb && \
 echo 'export PATH=$PATH:/opt/rhubarb' > /etc/profile.d/rhubarb.sh && \
 rm Rhubarb-Lip-Sync-1.13.0-Linux.zip && \
 rm -rf Rhubarb-Lip-Sync-1.13.0-Linux* 
ENV PATH="/opt/rhubarb:${PATH}"

# Verificar la instalación de Rhubarb
RUN rhubarb --version

# Dependencias Python
COPY backend/requirements.txt .
# Asegúrate que aquí tengas azure-cognitiveservices-speech>=1.38.0
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

EXPOSE 3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]
