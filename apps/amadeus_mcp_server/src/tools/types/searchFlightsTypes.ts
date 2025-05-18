import { z } from 'zod';

// Shared parameter and response schemas
export const FlightParamsSchema = z.object({
    originLocationCode: z.string().length(3),
    destinationLocationCode: z.string().length(3),
    departureDate: z.string(),
    returnDate: z.string().optional(),
    adults: z.number().min(1).max(9).default(1),
    children: z.number().min(0).default(0),
    infants: z.number().min(0).default(0),
    travelClass: z.enum(['ECONOMY','PREMIUM_ECONOMY','BUSINESS','FIRST']).optional(),
    nonStop: z.boolean().default(false),
    currencyCode: z.string().length(3).default('KRW'),
    maxResults: z.number().min(1).max(250).default(20),
    });


export type FlightParamsType = z.infer<typeof FlightParamsSchema>;

// Define interfaces for Amadeus API responses and parameters
export interface FlightParams {
    [key: string]: string | number | boolean | undefined;
    originLocationCode: string;
    destinationLocationCode: string;
    departureDate: string;
    returnDate?: string;
    adults: number;
    children: number;
    infants: number;
    travelClass?: 'ECONOMY' | 'PREMIUM_ECONOMY' | 'BUSINESS' | 'FIRST';
    nonStop: boolean;
    currencyCode: string;
    max: number;
  }

  export const FlightOfferSchema = z.object({
    originLocationCode: z
      .string()
      .length(3)
      .describe('Origin airport IATA code (e.g., JFK)'),
    destinationLocationCode: z
      .string()
      .length(3)
      .describe('Destination airport IATA code (e.g., LHR)'),
    departureDate: z.string().describe('Departure date in YYYY-MM-DD format'),
    returnDate: z
      .string()
      .optional()
      .describe('Return date in YYYY-MM-DD format (for round trips)'),
    adults: z.number().min(1).max(9).default(1).describe('Number of adults'),
    children: z.number().min(0).default(0).describe('Number of children'),
    infants: z.number().min(0).default(0).describe('Number of infants'),
    travelClass: z
      .enum(['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'])
      .optional()
      .describe('Travel class'),
    nonStop: z
      .boolean()
      .default(false)
      .describe('Filter for non-stop flights only'),
    currencyCode: z
      .string()
      .length(3)
      .default('KRW')
      .describe('Currency code for pricing'),
    maxResults: z
      .number()
      .min(1)
      .max(250)
      .default(20)
      .describe('Maximum number of results'),
    });

export type FlightOfferType = z.infer<typeof FlightOfferSchema>;




  // Define interfaces for Amadeus API response objects
  export interface FlightSegment {
    departure: {
      iataCode: string;
      at: string;
    };
    arrival: {
      iataCode: string;
      at: string;
    };
    carrierCode: string;
    number: string;
  }

  export interface FlightItinerary {
    duration: string;
    segments: FlightSegment[];
  }

  export interface FlightOffer {
    price: {
      total: string;
      currency: string;
    };
    itineraries: FlightItinerary[];
    validatingAirlineCodes: string[];
    numberOfBookableSeats?: number;
    id: string;

  }

  // Define response interfaces for API calls
  export interface FlightOfferResponse {
    data: FlightOffer[];
  }