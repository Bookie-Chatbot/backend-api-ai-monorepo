import { server } from '../index.js';
import { amadeus } from '../index.js';
import { cache } from '../index.js';
import * as Types from './types/index.js';
import { z } from 'zod';


/*
 * Tool to get flight price analysis
 */
server.tool(
  'flight-price-analysis',
  'Get flight price analysis for a route',
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
    currencyCode: z
      .string()
      .length(3)
      .default('USD')
      .describe('Currency code for pricing'),
  },
  async ({
    originLocationCode,
    destinationLocationCode,
    departureDate,
    returnDate,
    currencyCode,
  }) => {
    try {
      const params: Types.PriceAnalysisParams = {
        originLocationCode,
        destinationLocationCode,
        departureDate,
        returnDate,
        currencyCode,
      };

      // Remove undefined values
      for (const key of Object.keys(params)) {
        if (params[key] === undefined) {
          delete params[key];
        }
      }

      const response = (await amadeus.analytics.itineraryPriceMetrics.get(
        params,
      )) as Types.PriceAnalysisResponse;

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    } catch (error: unknown) {
      console.error('Error getting price analysis:', error);
      return {
        content: [
          {
            type: 'text',
            text: `Error getting price analysis: ${
              error instanceof Error ? error.message : 'Unknown error'
            }`,
          },
        ],
        isError: true,
      };
    }
  },
);