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
      .default('KRW')
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
        // 1) 파라미터 준비: 이름을 API 스펙에 맞춰 변경
        const params: Record<string, string> = {
          originIataCode: originLocationCode,
          destinationIataCode: destinationLocationCode,
          departureDate,
          currencyCode,
        };
        if (returnDate) {
          params.returnDate = returnDate;
        }

        // 2) 호출
        const response = await amadeus.analytics.itineraryPriceMetrics.get(params);

        // 3) 결과 반환
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
    }
  );