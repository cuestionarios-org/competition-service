FROM python:3.10

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de tu proyecto al contenedor
COPY . /app
# Copiar el archivo entrypoint.sh
COPY entrypoint.sh /app/entrypoint.sh

# Asegurar permisos de ejecución para el archivo
RUN chmod +x /app/entrypoint.sh

# Instala las dependencias del proyecto
RUN pip install -r requirements.txt

# Instalar Dockerize para ARM64 o x86_64
RUN apt-get update && apt-get install -y curl && \
    # Comprobamos la arquitectura para descargar la versión correcta de Dockerize
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
      curl -sSL https://github.com/jwilder/dockerize/releases/download/v0.9.2/dockerize-linux-amd64-v0.9.2.tar.gz | tar xzf - -C /usr/local/bin; \
    else \
      curl -sSL https://github.com/jwilder/dockerize/releases/download/v0.9.2/dockerize-linux-arm64-v0.9.2.tar.gz | tar xzf - -C /usr/local/bin; \
    fi && \
    apt-get autoremove -yqq --purge curl && rm -rf /var/lib/apt/lists/*

# Definir el argumento COMPETITION_PORT (valor se pasa desde docker-compose)
ARG COMPETITION_PORT=5016

# Definirlo como variable de entorno
ENV PORT=$COMPETITION_PORT

# Establecer el archivo de entrada como comando principal
CMD ["/app/entrypoint.sh"]

