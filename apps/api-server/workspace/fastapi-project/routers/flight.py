from fastapi import APIRouter, Depends, HTTPException, Query
from amadeus import Client, ResponseError
import os
from fastapi_project.amadeus_client import amadeus
from sqlalchemy.orm import Session
from fastapi_project.database import SessionLocal, engine
from fastapi_project.models import flight as models
from fastapi_project.schemas import flight as schemas
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
    travel_class: str = Query(None, enum=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]),
    included_airline_codes: Optional[str] = Query(None),        # excluded 이랑 같이 사용 못함
    excluded_airline_codes: Optional[str] = Query(None),
    non_stop: Optional[bool] = Query(None),
    max: Optional[int] = Query(None),
    currency_code: Optional[str] = Query(None),
):
    try:
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            
        }
        
        if return_date:
            params["returnDate"] = return_date
        if children is not None:
            params["children"] = children
        if infants is not None:
            params["infants"] = infants
        if travel_class:
            params["travelClass"] = travel_class
        if included_airline_codes:
            params["includedAirlineCodes"] = included_airline_codes
        if excluded_airline_codes:
            params["excludedAirlineCodes"] = excluded_airline_codes
        if non_stop is not None:
            params["nonStop"] = "true" if non_stop else "false"
        if max is not None:
            params["max"] = max
        if currency_code:
            params["currencyCode"] = currency_code

        response = amadeus.shopping.flight_offers_search.get(**params)
        return response.data
    except ResponseError as error:
        raise HTTPException(status_code=500, detail=str(error))