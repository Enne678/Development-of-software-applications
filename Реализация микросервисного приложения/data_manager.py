# Импорт FastAPI, SQLAlchemy-моделей и зависимостей
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

# Импорт конфигурации БД и модели Currency
import database
from database import Base, engine, SessionLocal
from currency_manager import Currency # переиспользуем модель

# Создание таблицы на всякий случай (она уже есть)
Base.metadata.create_all(bind=engine)

# Создаём приложение FastAPI
app = FastAPI(title="Data Manager")

# Зависимость: получение сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт списка всех валют
@app.get("/currencies", status_code=200)
def list_currencies(db: Session = Depends(get_db)):
    rows = db.query(Currency).all()
    return [{"currency_name": c.currency_name, "rate": float(c.rate)} for c in rows]

# Эндпоинт конвертации суммы в рубли
@app.get("/convert", status_code=200)
def convert(currency_name: str, amount: float, db: Session = Depends(get_db)):
    curr = db.query(Currency).filter_by(currency_name=currency_name).first()
    if not curr:
        raise HTTPException(status_code=404, detail="Currency not found")
    result = float(curr.rate) * amount
    return {"currency_name": currency_name, "amount": amount, "result": result}