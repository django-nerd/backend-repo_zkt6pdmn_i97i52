import os
import math
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Station, PaymentIntentIn, PaymentIntentOut, PaymentConfirmIn, PaymentResult

app = FastAPI(title="ChargeTunis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Utilities ---

def luhn_check(card_number: str) -> bool:
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 12:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

# --- Seed stations on startup if collection empty ---

SEED_STATIONS: List[Dict[str, Any]] = [
    {
        "name": "Lac 1 Supercharger",
        "city": "Tunis",
        "latitude": 36.849,
        "longitude": 10.283,
        "power_kw": 120,
        "price_tnd_per_kwh": 1.2,
        "capacity": 6,
        "brand": "ChargeTunis"
    },
    {
        "name": "La Marsa Marina",
        "city": "La Marsa",
        "latitude": 36.878,
        "longitude": 10.325,
        "power_kw": 50,
        "price_tnd_per_kwh": 1.0,
        "capacity": 4,
        "brand": "ChargeTunis"
    },
    {
        "name": "Sfax City Center",
        "city": "Sfax",
        "latitude": 34.739,
        "longitude": 10.760,
        "power_kw": 60,
        "price_tnd_per_kwh": 0.9,
        "capacity": 3,
        "brand": "ChargeTunis"
    },
    {
        "name": "Sousse Corniche",
        "city": "Sousse",
        "latitude": 35.830,
        "longitude": 10.638,
        "power_kw": 80,
        "price_tnd_per_kwh": 1.1,
        "capacity": 5,
        "brand": "ChargeTunis"
    }
]

@app.on_event("startup")
def seed_data():
    try:
        existing = db["station"].count_documents({})
        if existing == 0:
            for s in SEED_STATIONS:
                create_document("station", s)
    except Exception as e:
        print("Seed error:", e)

# --- API ---

@app.get("/")
def root():
    return {"message": "ChargeTunis backend running"}

@app.get("/stations")
def list_stations():
    try:
        items = get_documents("station")
        # Simulate availability in real-time
        now = datetime.utcnow().second
        result = []
        for it in items:
            capacity = it.get("capacity", 4)
            occupied = (now % (capacity + 1))
            available = max(0, capacity - occupied)
            it["available"] = available
            it["id"] = str(it.get("_id"))
            result.append(it)
        return {"stations": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/payments/intent", response_model=PaymentIntentOut)
def create_payment_intent(payload: PaymentIntentIn):
    amount = round(payload.kwh * payload.price_tnd_per_kwh, 3)
    client_secret = f"pi_{uuid4().hex}"
    return PaymentIntentOut(client_secret=client_secret, amount_tnd=amount)

@app.post("/payments/confirm", response_model=PaymentResult)
def confirm_payment(payload: PaymentConfirmIn):
    if not luhn_check(payload.card_number):
        return PaymentResult(status="failed", message="Invalid card number")
    txn_id = f"txn_{uuid4().hex[:12]}"
    return PaymentResult(status="succeeded", transaction_id=txn_id, message="Payment confirmed")

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    import os
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
