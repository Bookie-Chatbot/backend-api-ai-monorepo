from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import flight as models
from schemas import flight as schemas
from typing import List

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

# Create Flight
@router.post("/", response_model=schemas.FlightResponse)
def create_flight(flight: schemas.FlightCreate, db: Session = Depends(get_db)):
    db_flight = models.Flight(**flight.dict())
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)
    return db_flight

# Read All Flights
@router.get("/", response_model=List[schemas.FlightResponse])
def read_flights(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    flights = db.query(models.Flight).offset(skip).limit(limit).all()
    return flights

# Read Single Flight
@router.get("/{flight_id}", response_model=schemas.FlightResponse)
def read_flight(flight_id: int, db: Session = Depends(get_db)):
    db_flight = db.query(models.Flight).filter(models.Flight.id == flight_id).first()
    if db_flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return db_flight

# Update Flight
@router.put("/{flight_id}", response_model=schemas.FlightResponse)
def update_flight(flight_id: int, flight: schemas.FlightCreate, db: Session = Depends(get_db)):
    db_flight = db.query(models.Flight).filter(models.Flight.id == flight_id).first()
    if db_flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    for key, value in flight.dict().items():
        setattr(db_flight, key, value)
    
    db.commit()
    db.refresh(db_flight)
    return db_flight

# Delete Flight
@router.delete("/{flight_id}")
def delete_flight(flight_id: int, db: Session = Depends(get_db)):
    db_flight = db.query(models.Flight).filter(models.Flight.id == flight_id).first()
    if db_flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    db.delete(db_flight)
    db.commit()
    return {"message": "Flight deleted successfully"}