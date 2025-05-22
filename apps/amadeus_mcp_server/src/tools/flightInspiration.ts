import { z } from 'zod';
// Tool to search for flights
import { amadeus, cachedApiCall, server } from '../index.js';
import { cache } from '../index.js';
import * as Types from './types/index.js';




server.tool(
  'flight-inspiration',
  'Find the cheapest destinations where you can fly to',
  {
    origin: z
      .string()
      .length(3)
      .describe('Origin airport/city IATA code (e.g., MAD)'),
    departureDate: z
      .string()
      .optional()
      .describe('Departure date or range (YYYY-MM-DD or YYYY-MM-DD,YYYY-MM-DD)'),
    oneWay: z
      .boolean()
      .optional()
      .default(false)
      .describe('Whether to search for one-way flights only'),
    duration: z
      .string()
      .optional()
      .describe('Duration of stay in days (e.g., "7" or "2,8" for range)'),
    nonStop: z
      .boolean()
      .optional()
      .default(false)
      .describe('Whether to search for non-stop flights only'),
    maxPrice: z
      .number()
      .optional()
      .describe('Maximum price limit'),
    viewBy: z
      .enum(['COUNTRY', 'DATE', 'DESTINATION', 'DURATION', 'WEEK'])
      .optional()
      .describe('How to group the results'),
  },
  async ({
    origin,
    departureDate,
    oneWay,
    duration,
    nonStop,
    maxPrice,
    viewBy,
  }) => {
    try {
      const params: Types.FlightInspirationParams = {
        origin,
        departureDate,
        oneWay,
        duration,
        nonStop,
        maxPrice,
        viewBy,
      };

      // Remove undefined values
      for (const key of Object.keys(params)) {
        if (params[key] === undefined) {
          delete params[key];
        }
      }

      const response = (await amadeus.shopping.flightDestinations.get(
        params,
      )) as Types.FlightInspirationResponse;

      // Format the response for better readability
      const formattedResults = response.data.map((destination) => ({
        destination: destination.destination,
        departureDate: destination.departureDate,
        returnDate: destination.returnDate,
        price: destination.price.total,
        links: destination.links,
      }));

      return {
        /*
        content: [
          {
            type: 'text',
            text: JSON.stringify(formattedResults, null, 2),
          },
        ],*/
        /**
        content: [
            {
              type: 'resource',
              resource: {
                mimeType: 'application/json',
                text: JSON.stringify(formattedResults, null, 2),
              },
            },
          ],*/
      };
    } catch (error: unknown) {
      console.error('Error searching flight inspiration:', error);
      return {
        content: [
          {
            type: 'text',
            text: `Error searching flight inspiration: ${
              error instanceof Error ? error.message : 'Unknown error'
            }`,
          },
        ],
        isError: true,
      };
    }
  },
);
