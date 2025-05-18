import { server } from '../index.js';
import { amadeus } from '../index.js';
import { cache } from '../index.js';
import * as Types from './types/index.js';
import { z } from 'zod';


server.tool(
  'search-flights',
  'Search for flight offers',
  {
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
  },
  async ({
    originLocationCode,
    destinationLocationCode,
    departureDate,
    returnDate,
    adults,
    children,
    infants,
    travelClass,
    nonStop,
    currencyCode,
    maxResults,
  }) => {
    try {
      const params: Types.FlightParams = {
        originLocationCode,
        destinationLocationCode,
        departureDate,
        returnDate,
        adults,
        children,
        infants,
        travelClass,
        nonStop,
        currencyCode,
        max: maxResults,
      };

      // Remove undefined values
      for (const key of Object.keys(params)) {
        if (params[key] === undefined) {
          delete params[key];
        }
      }

      const response = (await amadeus.shopping.flightOffersSearch.get(
        params,
      )) as  Types.FlightOfferResponse;

      await cache.set('last_search_offers', response.data, 600);


      const formattedResults = response.data.map((offer:  Types.FlightOffer) => {
        const {
          price,
          itineraries,
          validatingAirlineCodes,
          numberOfBookableSeats,
        } = offer;

        // Format itineraries with more details
        const formattedItineraries = itineraries.map(
          (itinerary:  Types.FlightItinerary, idx: number) => {
            // Calculate total duration in minutes
            const totalDurationMinutes = Number.parseInt(
              itinerary.duration.slice(2, -1),
            );
            // Format as hours and minutes
            const hours = Math.floor(totalDurationMinutes / 60);
            const minutes = totalDurationMinutes % 60;
            const formattedDuration = `${hours}h ${minutes}m`;

            // Count stops
            const numStops = itinerary.segments.length - 1;
            const stopsText =
              numStops === 0
                ? 'Non-stop'
                : `${numStops} stop${numStops > 1 ? 's' : ''}`;

            // Format segments with times
            const segments = itinerary.segments
              .map((segment: Types.FlightSegment) => {
                const departureTime = new Date(
                  segment.departure.at,
                ).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: true,
                });
                const arrivalTime = new Date(
                  segment.arrival.at,
                ).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: true,
                });

                return `${segment.departure.iataCode} (${departureTime}) → ${segment.arrival.iataCode} (${arrivalTime}) - ${segment.carrierCode}${segment.number}`;
              })
              .join(' | ');

            return {
              type: idx === 0 ? 'Outbound' : 'Return',
              duration: formattedDuration,
              stops: stopsText,
              segments,
            };
          },
        );

        return {
          price: `${price.total} ${price.currency}`,
          bookableSeats: numberOfBookableSeats || 'Unknown',
          airlines: validatingAirlineCodes.join(', '),
          itineraries: formattedItineraries,
        };
      });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(formattedResults, null, 2),
          },
        ],
      };
    } catch (error: unknown) {
      console.error('Error searching flights:', error);
      return {
        content: [
          {
            type: 'text',
            text: `Error searching flights: ${
              error instanceof Error ? error.message : 'Unknown error'
            }`,
          },
        ],
        isError: true,
      };
    }
  },
);

