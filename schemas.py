from pydantic import BaseModel, Field
from typing import Optional, List

class Station(BaseModel):
    name: str = Field(..., description="Station display name")
    city: str = Field(..., description="City name")
    latitude: float = Field(...)
    longitude: float = Field(...)
    power_kw: int = Field(..., ge=3, le=350)
    price_tnd_per_kwh: float = Field(..., ge=0)
    capacity: int = Field(..., ge=1, description="Total number of connectors")
    brand: Optional[str] = Field(None)

class ChargingSession(BaseModel):
    station_id: str
    kwh: float = Field(..., gt=0)
    amount_tnd: float = Field(..., ge=0)
    status: str = Field("pending")

class PaymentIntentIn(BaseModel):
    station_id: str
    kwh: float = Field(..., gt=0)
    price_tnd_per_kwh: float = Field(..., ge=0)

class PaymentIntentOut(BaseModel):
    client_secret: str
    amount_tnd: float
    currency: str = "TND"

class PaymentConfirmIn(BaseModel):
    client_secret: str
    card_number: str
    exp_month: int
    exp_year: int
    cvc: str

class PaymentResult(BaseModel):
    status: str
    transaction_id: Optional[str] = None
    message: Optional[str] = None
