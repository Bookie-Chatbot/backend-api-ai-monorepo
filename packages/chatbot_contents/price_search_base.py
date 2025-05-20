
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class LocationInfo(BaseModel):
    iataCode: str
    terminal: Optional[str]
    at: str

class Aircraft(BaseModel):
    code: str

class OperatingInfo(BaseModel):
    carrierCode: str

class Segment(BaseModel):
    id: str
    number: str
    carrierCode: str
    numberOfStops: int
    duration: str
    blacklistedInEU: bool
    departure: LocationInfo
    arrival: LocationInfo
    aircraft: Aircraft
    operating: Optional[OperatingInfo]

class Itinerary(BaseModel):
    duration: str
    segments: List[Segment]

class AdditionalService(BaseModel):
    amount: str
    type: str

class Fee(BaseModel):
    amount: str
    type: str

class PriceDetail(BaseModel):
    base: str
    total: str
    currency: str
    fees: List[Fee]
    additionalServices: Optional[List[AdditionalService]]
    grandTotal: Optional[str]

class PricingOptions(BaseModel):
    fareType: List[str]
    includedCheckedBagsOnly: bool

class AmenityProvider(BaseModel):
    name: str

class Amenity(BaseModel):
    amenityProvider: AmenityProvider
    amenityType: str
    description: str
    isChargeable: bool

class FareDetailsBySegment(BaseModel):
    segmentId: str
    cabin: str
    # 'class' 는 파이썬 예약어라서 따옴표로 처리하거나 alias 사용
    fare_class: str = Field(..., alias="class")
    fareBasis: str
    brandedFare: str
    brandedFareLabel: str
    includedCabinBags: Dict[str,int]
    includedCheckedBags: Dict[str,int]
    amenities: List[Amenity]  # 복수형으로 변경

class TravelerPricing(BaseModel):
    travelerId: str
    travelerType: str
    fareOption: str
    price: PriceDetail
    fareDetailsBySegment: List[FareDetailsBySegment]

class FlightOffer(BaseModel):
    id: str
    instantTicketingRequired: bool
    isUpsellOffer: bool
    itineraries: List[Itinerary]
    lastTicketingDate: str
    lastTicketingDateTime: str
    nonHomogeneous: bool
    numberOfBookableSeats: int
    oneWay: bool
    price: PriceDetail
    pricingOptions: PricingOptions
    source: str
    travelerPricings: List[TravelerPricing]
    type: str
    validatingAirlineCodes: List[str]