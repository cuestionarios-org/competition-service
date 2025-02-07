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


# Expón el puerto en el que el servicio de QA estará corriendo
EXPOSE 5006

# Establecer el archivo de entrada como comando principal
CMD ["/app/entrypoint.sh"]

