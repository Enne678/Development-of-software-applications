# Импорт SQLAlchemy и настройка подключения к файлу SQLite
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Подключаемся к файлу database.db в текущей папке
SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"

# Создаём движок и сессии
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()