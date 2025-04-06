import os
from sqlalchemy import text, create_engine
from flask_migrate import upgrade
from seeders import run_seeders
from sqlalchemy.exc import OperationalError

def create_database_if_not_exists(app):
    """Crea la base de datos en PostgreSQL si no existe"""
    print("😝 ¿Existe la DB?")

    db_url = app.config["SQLALCHEMY_DATABASE_URI"]
    temp_db_url = db_url.rsplit("/", 1)[0] + "/postgres"
    
    try:
        engine = create_engine(temp_db_url, isolation_level="AUTOCOMMIT")

        with engine.connect() as connection:
            db_name = os.getenv('COMPETITION_POSTGRES_DB')
            result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
            exists = result.scalar()

            if not exists:
                print(f"📌 Creando la base de datos {db_name}...")
                connection.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✅ Base de datos {db_name} creada exitosamente.")

                # Ejecutar migraciones usando Flask Migrate
                print("📌 Ejecutando migraciones...")
                with app.app_context():
                    try:
                        upgrade()
                        print("✅ Migraciones aplicadas correctamente.")
                        print("📌 Iniciando seeders...")
                        run_seeders()
                        print("✅ Rutina de seeders finalizada.")
                    except Exception as e:
                        print(f"❌ Error al aplicar migraciones: {e}")
            else:
                print(f"✅ La base de datos {db_name} ya existe.")

    except OperationalError as e:
        print("❌ No se pudo conectar al servidor PostgreSQL.")
        print("🔴 Asegúrate de que el servidor está corriendo (Levantar con docker-compose) y que los datos de conexión son correctos.")
        print(f"📌 Detalles: {e}")
