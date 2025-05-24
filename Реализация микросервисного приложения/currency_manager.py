from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, condecimal, Field
from sqlalchemy.orm import Session
from typing import Optional
import uvicorn
import logging

# Импорт конфигурации БД
from database import Base, engine, get_db, Currency

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Pydantic-схемы для запросов
class CurrencyCreate(BaseModel):
    currency_name: str = Field(..., examples=["USD"])
    rate: condecimal(max_digits=18, decimal_places=6) = Field(..., examples=[75.50])


class CurrencyUpdate(BaseModel):
    currency_name: str = Field(..., examples=["USD"])
    rate: condecimal(max_digits=18, decimal_places=6) = Field(..., examples=[76.00])


class CurrencyDelete(BaseModel):
    currency_name: str = Field(..., examples=["USD"])


class StatusResponse(BaseModel):
    status: str
    message: str
    currency_id: Optional[int] = None


# Создаём приложение FastAPI
app = FastAPI(title="Currency Manager Service", version="1.0.0")


# Создание таблицы при старте приложения
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully.")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")


@app.get("/")
async def root():
    return {"message": "Currency Manager Service is running"}


# Эндпоинт POST /load
@app.post("/load", response_model=StatusResponse, status_code=200)
def load_currency(data: CurrencyCreate, db: Session = Depends(get_db)):
    """Добавление новой валюты в базу данных"""
    currency_name_upper = data.currency_name.upper()
    try:
        # 1. Проверка того, что такой валюты нет в БД
        existing_currency = db.query(Currency).filter(
            Currency.currency_name == currency_name_upper
        ).first()

        if existing_currency:
            raise HTTPException(
                status_code=400,
                detail=f"Currency {currency_name_upper} already exists"
            )

        # 2. Выполняется сохранение валюты в таблицу currencies
        new_currency = Currency(
            currency_name=currency_name_upper,
            rate=data.rate
        )

        db.add(new_currency)
        db.commit()
        db.refresh(new_currency)

        # 3. Возвращается ответ 200 ОК
        return {
            "status": "OK",
            "message": f"Currency {currency_name_upper} successfully added",
            "currency_id": new_currency.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Эндпоинт POST /update_currency
@app.post("/update_currency", response_model=StatusResponse, status_code=200)
def update_currency_rate(data: CurrencyUpdate, db: Session = Depends(get_db)):
    """Обновление курса существующей валюты"""
    currency_name_upper = data.currency_name.upper()
    try:
        # 1. Проверка того, что такая валюта существует в БД
        currency = db.query(Currency).filter(
            Currency.currency_name == currency_name_upper
        ).first()

        if not currency:
            raise HTTPException(
                status_code=404,
                detail=f"Currency {currency_name_upper} not found"
            )

        # 2. Выполняется обновление данных валюты в таблицу currencies
        old_rate = currency.rate
        currency.rate = data.rate
        db.commit()

        # 3. Возвращается ответ 200 ОК
        return {
            "status": "OK",
            "message": f"Currency {currency_name_upper} rate updated from {old_rate} to {data.rate}"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Эндпоинт POST /delete
@app.post("/delete", response_model=StatusResponse, status_code=200)
def delete_currency_entry(data: CurrencyDelete, db: Session = Depends(get_db)):
    """Удаление валюты из базы данных"""
    currency_name_upper = data.currency_name.upper()
    try:
        # 1. Проверка того, что такая валюта существует в БД
        currency = db.query(Currency).filter(
            Currency.currency_name == currency_name_upper
        ).first()

        if not currency:
            raise HTTPException(
                status_code=404,
                detail=f"Currency {currency_name_upper} not found"
            )

        # 2. Выполняется удаление валюты из таблицы currencies
        db.delete(currency)
        db.commit()

        # 3. Возвращается ответ 200 ОК
        return {
            "status": "OK",
            "message": f"Currency {currency_name_upper} successfully deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    # Микросервис запускается на порту 5001
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")