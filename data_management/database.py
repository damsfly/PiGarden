import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import load_config

# Charger la configuration
config = load_config()
db_config = config['database']
DATABASE_URL = f"mariadb+mariadbconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

# Configurer SQLAlchemy
Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    pool_recycle=1800,  # Réutiliser les connexions toutes les 1800 secondes (30 minutes)
    pool_pre_ping=True, # Vérifie la connexion avant de l'utiliser
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_database():
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("La base de données a été créée et mise à jour avec succès.")
    except Exception as error:
        logging.error(f"Erreur lors de la création de la base de données: {error}")