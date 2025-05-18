import { z } from 'zod';
// Tool to search for flights
import { amadeus, cachedApiCall, server } from '../index.js';
import { cache } from '../index.js';
import * as Types from './types/index.js';



server.tool(
  'airport-routes',
  'Find direct routes from a specific airport',
  {
    departureAirportCode: z
      .string()
      .length(3)
      .describe('Departure airport IATA code (e.g., JFK)'),
    maxResults: z
      .number()
      .min(1)
      .max(100)
      .optional()
      .default(10)
      .describe('Maximum number of results'),
  },
  async ({ departureAirportCode, maxResults }) => {
    try {
      const params: Types.AirportRoutesParams = {
        departureAirportCode,
        max: maxResults,
      };

      // Remove undefined values
      for (const key of Object.keys(params)) {
        if (params[key] === undefined) {
          delete params[key];
        }
      }

      const response = (await amadeus.airport.directDestinations.get(
        params,
      )) as Types.AirportRoutesResponse;

      // Format the response for better readability
      const formattedResults = response.data.map((route) => ({
        destination: route.iataCode,
        name: route.name,
        type: route.subtype,
        distance: `${route.distance.value} ${route.distance.unit}`,
        flightScore: route.analytics?.flights?.score || 'N/A',
        travelerScore: route.analytics?.travelers?.score || 'N/A',
      }));

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(formattedResults, null, 2),
          },
        ],
      };
    } catch (error: unknown) {
      console.error('Error searching airport routes:', error);
      return {
        content: [
          {
            type: 'text',
            text: `Error searching airport routes: ${
              error instanceof Error ? error.message : 'Unknown error'
            }`,
          },
        ],
        isError: true,
      };
    }
  },
);
