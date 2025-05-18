/**
 * Tool to search for airport routes
 */
export interface AirportRoutesParams {
    [key: string]: string | number | undefined;
    departureAirportCode: string;
    max?: number;
  }

export interface AirportRoute {
    type: string;
    subtype: string;
    name: string;
    iataCode: string;
    distance: {
      value: number;
      unit: string;
    };
    analytics?: {
      flights?: {
        score?: number;
      };
      travelers?: {
        score?: number;
      };
    };
  }

  export interface AirportRoutesResponse {
    data: AirportRoute[];
  }