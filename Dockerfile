FROM python:3.10

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de tu proyecto al contenedor
COPY . /app
# Copiar el archivo entrypoint.sh
COPY entrypoint.sh /app/entrypoint.sh

# Asegurar permisos de ejecución para el archivo
RUN chmod +x /app/entrypoint.sh

# # Instalar dos2unix para convertir CRLF a LF
# RUN apt-get update && apt-get install -y dos2unix && \
#     echo "Antes de conversión:" && file /app/entrypoint.sh && \
#     dos2unix -v /app/entrypoint.sh && \
#     echo "Después de conversión:" && file /app/entrypoint.sh

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

# Expón el puerto en el que el servicio de QA estará corriendo
EXPOSE 5006

# Espera a que PostgreSQL esté disponible y luego inicia la aplicación
# CMD ["dockerize", "-wait", "tcp://postgres:5432", "-timeout", "30s", "python", "run.py"]
# CMD ["dockerize", "-wait", "tcp://postgres:5432", "-timeout", "30s", "flask", "db", "upgrade",  "python", "run.py"]
# Establecer el archivo de entrada como comando principal
CMD ["/app/entrypoint.sh"]

