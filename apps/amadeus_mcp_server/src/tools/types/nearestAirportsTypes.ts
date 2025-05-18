


/**
 * Tool to find nearest relevant airports
 */
export interface NearestAirportParams {
    [key: string]: string | number | undefined;
    latitude: number;
    longitude: number;
    radius?: number;
    max?: number;
  }

  export interface NearestAirport {
    type: string;
    subtype: string;
    name: string;
    detailedName: string;
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

  export interface NearestAirportResponse {
    data: NearestAirport[];
  }
