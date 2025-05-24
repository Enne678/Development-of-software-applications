from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
import uvicorn
import logging
from decimal import Decimal

# Импорт конфигурации БД и модели
from database import Base, engine, get_db, Currency
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CurrencyResponse(BaseModel):
    id: int
    currency_name: str
    rate: Decimal

    class Config:
        from_attributes = True


class ConvertResponse(BaseModel):
    currency_name: str
    amount: float
    rate: Decimal
    result: Decimal


# Создаём приложение FastAPI
app = FastAPI(title="Data Manager Service", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Verifying database connection for data-manager...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database connection verified.")
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")


@app.get("/")
async def root():
    return {"message": "Data Manager Service is running"}


# Эндпоинт GET /currencies
@app.get("/currencies", status_code=200, response_model=List[CurrencyResponse])
def list_all_currencies(db: Session = Depends(get_db)):
    """Возвращает все добавленные ранее в таблицу currencies"""
    try:
        currencies = db.query(Currency).order_by(Currency.currency_name).all()
        return currencies
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Эндпоинт GET /convert
@app.get("/convert", status_code=200, response_model=ConvertResponse)
def convert_currency_to_rub(
        currency_name: str = Query(..., description="Наименование валюты"),
        amount: float = Query(..., gt=0, description="Сумма для конвертации"),
        db: Session = Depends(get_db)
):
    """Конвертация суммы в указанной валюте в рубли"""
    currency_name_upper = currency_name.upper()
    try:
        # 1. Проверка, что такая валюта существует в БД
        currency = db.query(Currency).filter(
            Currency.currency_name == currency_name_upper
        ).first()

        if not currency:
            raise HTTPException(
                status_code=404,
                detail=f"Currency {currency_name_upper} not found"
            )

        # 2. Получение курса из БД для заданной валюты
        rate = currency.rate

        # 3. Конвертация и ответ 200 ОК, в теле которого содержится JSON с конвертированным значением
        amount_decimal = Decimal(str(amount))
        result = (rate * amount_decimal).quantize(Decimal("0.01"))

        return ConvertResponse(
            currency_name=currency.currency_name,
            amount=amount,
            rate=rate,
            result=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    # Микросервис запускается на порту 5002
    uvicorn.run(app, host="0.0.0.0", port=5002, log_level="info")