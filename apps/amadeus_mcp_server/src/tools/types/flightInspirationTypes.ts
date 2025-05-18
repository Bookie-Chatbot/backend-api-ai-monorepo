/**
 * Tool to search for flight inspiration destinations
 */
export interface FlightInspirationParams {
    [key: string]: string | number | boolean | undefined;
    origin: string;
    departureDate?: string;
    oneWay?: boolean;
    duration?: string;
    nonStop?: boolean;
    maxPrice?: number;
    viewBy?: 'COUNTRY' | 'DATE' | 'DESTINATION' | 'DURATION' | 'WEEK';
  }

  export interface FlightDestination {
    type: string;
    origin: string;
    destination: string;
    departureDate: string;
    returnDate?: string;
    price: {
      total: string;
    };
    links: {
      flightDates: string;
      flightOffers: string;
    };
  }

  export interface FlightInspirationResponse {
    data: FlightDestination[];
  }