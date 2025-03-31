from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import flight as models
from schemas import flight as schemas

router = APIRouter(
    prefix="/flights",
    tags=["flights"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.FlightResponse)
def create_flight(flight: schemas.FlightCreate, db: Session = Depends(get_db)):
    db_flight = models.Flight(
        airline=flight.airline,
        departure=flight.departure,
        arrival=flight.arrival,
        departure_time=flight.departure_time,
        arrival_time=flight.arrival_time,
        price=flight.price,
        available_seats=flight.available_seats
    )
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)
    return db_flight