# Usar una imagen base de Node.js con Alpine
FROM node:current-alpine

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar package.json y package-lock.json (si existe)
COPY frontend/package*.json ./

# Instalar dependencias de Node.js
RUN npm install
# RUN npm update

# Copiar el resto de los archivos de la aplicación
COPY frontend .

# Exponer el puerto
EXPOSE 5173

# Comando para ejecutar la aplicación
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]