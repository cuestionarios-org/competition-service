#!/bin/bash

echo "<<<<<<<<< ${COMPETITION_POSTGRES_HOST} >>>>>>>>>"


# Verifica que las variables necesarias estén configuradas
if [[ -z "$COMPETITION_POSTGRES_HOST" || -z "$COMPETITION_POSTGRES_PORT" || -z "$COMPETITION_POSTGRES_DB" ]]; then
    echo "Error: Las variables POSTGRES_HOST, POSTGRES_PORT o POSTGRES_DB no están configuradas."
    exit 1
fi


# Espera a que PostgreSQL esté disponible
echo "⏳ Esperando a que PostgreSQL esté listo..."
dockerize -wait tcp://$COMPETITION_POSTGRES_HOST:5432 -timeout 30s
if [ $? -ne 0 ]; then
    echo "Error: No se pudo conectar a PostgreSQL en $COMPETITION_POSTGRES_HOST:5432"
    exit 1
fi
echo "⏳ Esperando a que PostgreSQL esté listo..."


# Inicia la aplicación
python run.py
