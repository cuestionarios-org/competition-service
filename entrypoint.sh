#!/bin/bash

echo "<<<<<<<<< ${COMPETITION_POSTGRES_HOST} >>>>>>>>>"


# Verifica que las variables necesarias estén configuradas
if [[ -z "$COMPETITION_POSTGRES_HOST" || -z "$COMPETITION_POSTGRES_PORT" || -z "$COMPETITION_POSTGRES_DB" ]]; then
    echo "Error: Las variables POSTGRES_HOST, POSTGRES_PORT o POSTGRES_DB no están configuradas."
    exit 1
fi


# Espera a que PostgreSQL esté disponible
dockerize -wait tcp://$COMPETITION_POSTGRES_HOST:$COMPETITION_POSTGRES_PORT -timeout 30s
if [ $? -ne 0 ]; then
    echo "Error: No se pudo conectar a PostgreSQL en $COMPETITION_POSTGRES_HOST:$COMPETITION_POSTGRES_PORT"
    exit 1
fi


flask init_db
echo "Base de datos inicializada"


# Ejecuta las migraciones de la base de datos
flask db upgrade
echo "Base de datos disponible"


# Inicia la aplicación
python run.py
