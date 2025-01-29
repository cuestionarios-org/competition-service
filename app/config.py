# app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv('COMPETITION_POSTGRES_USER',"admin")
POSTGRES_PASSWORD = os.getenv('COMPETITION_POSTGRES_PASSWORD',"admin1234")
POSTGRES_HOST = os.getenv('COMPETITION_POSTGRES_HOST',"localhost")
POSTGRES_PORT = os.getenv('COMPETITION_POSTGRES_PORT',"5433")
POSTGRES_DB = os.getenv('COMPETITION_POSTGRES_DB',"competition")

class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SEED_DB = os.getenv("COMPETITION_SEED_DB", "no")



class DevelopmentConfig(Config):
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    DEBUG = True

class TestingConfig(Config):
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    TESTING = True

class ProductionConfig(Config):
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    DEBUG = False

config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
