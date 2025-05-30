from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi_project.database import SessionLocal
from fastapi_project.models import hotel as models
from fastapi_project.schemas import hotel as schemas
from typing import List

router = APIRouter(
    prefix="/hotels",
    tags=["hotels"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create Hotel
@router.post("/", response_model=schemas.HotelResponse)
def create_hotel(hotel: schemas.HotelCreate, db: Session = Depends(get_db)):
    db_hotel = models.Hotel(**hotel.dict())
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

# Read All Hotels
@router.get("/", response_model=List[schemas.HotelResponse])
def read_hotels(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    hotels = db.query(models.Hotel).offset(skip).limit(limit).all()
    return hotels

# Read Single Hotel
@router.get("/{hotel_id}", response_model=schemas.HotelResponse)
def read_hotel(hotel_id: int, db: Session = Depends(get_db)):
    db_hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
    if db_hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return db_hotel

# Update Hotel
@router.put("/{hotel_id}", response_model=schemas.HotelResponse)
def update_hotel(hotel_id: int, hotel: schemas.HotelCreate, db: Session = Depends(get_db)):
    db_hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
    if db_hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    for key, value in hotel.dict().items():
        setattr(db_hotel, key, value)
    
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

# Delete Hotel
@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    db_hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_id).first()
    if db_hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    db.delete(db_hotel)
    db.commit()
    return {"message": "Hotel deleted successfully"}