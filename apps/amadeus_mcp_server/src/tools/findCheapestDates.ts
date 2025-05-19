import { z } from 'zod';
// Tool to search for flights
import { amadeus, cachedApiCall, server } from '../index.js';
import { cache } from '../index.js';
import * as Types from './types/index.js';



// apps/amadeus_mcp_server/src/tools.ts

server.tool(
  'find-cheapest-dates',
  'Find the cheapest dates to fly for a given route (using Flight Offers Search v2)',
  {
    originLocationCode: z.string().length(3).describe('Origin airport IATA code (e.g., ICN)'),
    destinationLocationCode: z.string().length(3).describe('Destination airport IATA code (e.g., FRA)'),
    departureDate: z
  .string()
  //.refine(d => new Date(d) >= new Date(), { message: '출발일은 오늘 이후여야 합니다.' }),
  ,
    returnDate: z.string().optional().describe('Return date in YYYY-MM-DD format'),
    maxPrice: z.number().optional().describe('Maximum price limit per ticket'),
    nonStop: z.boolean().optional().default(false).describe('Only non-stop flights'),
    adults: z.number().min(1).default(1).describe('Number of adult passengers'),
    currencyCode: z.string().length(3).default('KRW').describe('Currency code for pricing'),
    maxResults: z.number().min(1).default(5).describe('Max number of offers to return'),
  },
  async ({
    originLocationCode,
    destinationLocationCode,
    departureDate,
    returnDate,
    maxPrice,
    nonStop,
    adults,
    currencyCode,
    maxResults,
  }) => {
    try {

          // 0) 출발일이 과거면 오늘로 대체
          const today = new Date().toISOString().split('T')[0];
          const validDepartureDate = departureDate < today ? today : departureDate;
      // 1) v2FlightOffersSearch 파라미터 세팅
      const params: Record<string, any> = {
        originLocationCode,
        destinationLocationCode,
        departureDate,
        adults,
        nonStop,
        currencyCode,
        max: maxResults,
      };
      if (returnDate) params.returnDate = returnDate;
      if (maxPrice)  params.maxPrice  = maxPrice;

      // 2) 실제 Amadeus v2 쇼핑 Flight Offers Search 호출
      const rsp = await amadeus.shopping.flightOffersSearch.get(params);

      console.log(`res: ${params.originLocationCode}
        ${params.destinationLocationCode} ${params.departureDate}
        ${params.returnDate} ${params.nonStop} ${params.adults} ${params.currencyCode}
        ${params.max} - ${rsp.status} - ${rsp.statusText} - data: ${JSON.stringify(rsp.data)}`);

      console.log('Flight Offers Search response:', rsp.data);

      // 3) 데이터 유효성 검사
      if (!rsp.data || rsp.data.length === 0) {
        return {
          content: [
            { type: 'text', text: 'No flight offers found for the given criteria.' },
          ],
          isError: false,
        };
      }

      // 4) 가장 저렴한 offer 선택
      const cheapest = rsp.data.reduce((prev: any, curr: any) => {
        const prevPrice = parseFloat(prev.price.total);
        const currPrice = parseFloat(curr.price.total);
        return currPrice < prevPrice ? curr : prev;
      });

      // 5) 응답 포맷
      const seg = cheapest.itineraries[0].segments[0];
      const result = {
        route:     `${seg.departure.iataCode}-${seg.arrival.iataCode}`,
        carrier:   seg.carrierCode,
        departure: seg.departure.at,
        arrival:   seg.arrival.at,
        price:     `${cheapest.price.total} ${cheapest.price.currency}`,
        offer_id:  cheapest.id,
        // v2 응답의 self 링크
        link:      rsp.meta?.links?.self,
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error: unknown) {
      console.error('Error finding cheapest dates:', error);
      return {
        content: [
          {
            type: 'text',
            text: `Error finding cheapest dates: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  }
);

