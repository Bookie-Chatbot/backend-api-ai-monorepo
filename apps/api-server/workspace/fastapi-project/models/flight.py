from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime

class Flight(Base):
    __tablename__ = 'flights'
    __table_args__ = {'extend_existing': True}


    id = Column(Integer, primary_key=True, index=True)
    airline = Column(String(100), nullable=False)
    departure = Column(String(50), nullable=False)
    arrival = Column(String(50), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    available_seats = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)