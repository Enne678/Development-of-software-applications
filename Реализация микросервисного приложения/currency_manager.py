# Импорт FastAPI, Pydantic, SQLAlchemy-моделей и схем
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, condecimal
from sqlalchemy.orm import Session

# Импорт конфигурации БД и базового класса
import database
from database import Base, engine, SessionLocal

# Определение модели таблицы currencies
from sqlalchemy import Column, Integer, String, Numeric

class Currency(Base):
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True, index=True)
    currency_name = Column(String(50), unique=True, index=True, nullable=False)
    rate = Column(Numeric(18,6), nullable=False)

# Создание таблицы при старте приложения
Base.metadata.create_all(bind=engine)

# Pydantic-схемы для запросов
class CurrencyCreate(BaseModel):
    currency_name: str
    rate: condecimal(max_digits=18, decimal_places=6)

class CurrencyUpdate(BaseModel):
    currency_name: str
    rate: condecimal(max_digits=18, decimal_places=6)

class CurrencyDelete(BaseModel):
    currency_name: str

# Создаём приложение FastAPI
app = FastAPI(title="Currency Manager")

# Зависимость: получение сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт загрузки новой валюты
@app.post("/load", status_code=200)
def load_currency(data: CurrencyCreate, db: Session = Depends(get_db)):
    exists = db.query(Currency).filter_by(currency_name=data.currency_name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Currency exists")
    curr = Currency(currency_name=data.currency_name, rate=data.rate)
    db.add(curr)
    db.commit()
    return {"status": "OK"}

# Эндпоинт обновления курса валюты
@app.post("/update_currency", status_code=200)
def update_currency(data: CurrencyUpdate, db: Session = Depends(get_db)):
    curr = db.query(Currency).filter_by(currency_name=data.currency_name).first()
    if not curr:
        raise HTTPException(status_code=404, detail="Currency not found")
    curr.rate = data.rate
    db.commit()
    return {"status": "OK"}

# Эндпоинт удаления валюты
@app.post("/delete", status_code=200)
def delete_currency(data: CurrencyDelete, db: Session = Depends(get_db)):
    curr = db.query(Currency).filter_by(currency_name=data.currency_name).first()
    if not curr:
        raise HTTPException(status_code=404, detail="Currency not found")
    db.delete(curr)
    db.commit()
    return {"status": "OK"}