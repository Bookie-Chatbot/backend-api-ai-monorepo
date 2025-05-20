from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base
from datetime import datetime

class Reservation(Base):
    __tablename__ = 'reservations'
    __table_args__ = {'extend_existing': True}


    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=True)
    flight_id = Column(Integer, ForeignKey('flights.id'), nullable=True)
    status = Column(String(50), nullable=False)
    reservation_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)