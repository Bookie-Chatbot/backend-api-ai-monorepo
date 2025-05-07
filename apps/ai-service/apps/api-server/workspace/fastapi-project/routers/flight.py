from fastapi import APIRouter, Depends, HTTPException, Query
from amadeus import Client, ResponseError
import os
from amadeus_client import amadeus
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import flight as models
from schemas import flight as schemas
from typing import List, Optional

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

# Search Flight (amadeus API)
# Amadeus API: Flight Offers Search
@router.get("/search")
def search_flights(
    origin: str = Query(...),
    destination: str = Query(...),
    departure_date: str = Query(...),
    return_date: Optional[str] = Query(None),
    adults: int = Query(1),
    children: Optional[int] = Query(None),
    infants: Optional[int] = Query(None),
    travel_class: Optional[str] = Query(None),
    included_airline_codes: Optional[str] = Query(None),
    excluded_airline_codes: Optional[str] = Query(None),
    non_stop: Optional[bool] = Query(None),
    currency_code: Optional[str] = Query(None),
    max_price: Optional[int] = Query(None),
    max: Optional[int] = Query(None)
):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date,
            adults=adults,
            children=children,
            infants=infants,
            travelClass=travel_class,
            includedAirlineCodes=included_airline_codes,
            excludedAirlineCodes=excluded_airline_codes,
            nonStop=non_stop,
            currencyCode=currency_code,
            maxPrice=max_price,
            max=max
        )
        return response.data
    except ResponseError as error:
        raise HTTPException(status_code=500, detail=str(error))