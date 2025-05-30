from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi_project.database import SessionLocal
from fastapi_project.models import reservation as models
from fastapi_project.schemas import reservation as schemas
from typing import List

router = APIRouter(
    prefix="/reservations",
    tags=["reservations"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create Reservation
@router.post("/", response_model=schemas.ReservationResponse)
def create_reservation(reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    db_reservation = models.Reservation(**reservation.dict())
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

# Read All Reservations
@router.get("/", response_model=List[schemas.ReservationResponse])
def read_reservations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    reservations = db.query(models.Reservation).offset(skip).limit(limit).all()
    return reservations

# Read Single Reservation
@router.get("/{reservation_id}", response_model=schemas.ReservationResponse)
def read_reservation(reservation_id: int, db: Session = Depends(get_db)):
    db_reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return db_reservation

# Update Reservation
@router.put("/{reservation_id}", response_model=schemas.ReservationResponse)
def update_reservation(reservation_id: int, reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    db_reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    for key, value in reservation.dict().items():
        setattr(db_reservation, key, value)
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

# Delete Reservation
@router.delete("/{reservation_id}")
def delete_reservation(reservation_id: int, db: Session = Depends(get_db)):
    db_reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    db.delete(db_reservation)
    db.commit()
    return {"message": "Reservation deleted successfully"}