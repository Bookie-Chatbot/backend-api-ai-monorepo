import { z } from 'zod';
// Tool to search for flights
import { amadeus, cachedApiCall, server } from '../index.js';
import { cache } from '../index.js';
import * as Types from './types/index.js';

/**
 * Tool to get detailed flight offer information
 */
server.tool(
  'get-flight-details',
  'Get detailed information about a specific flight offer',
  {
    offerId: z.string().describe('The flight offer ID returned by search-flights'),
  },
  async ({ offerId }) => {
    try {
      // 1) 먼저 캐시나 DB에서 flightOffersSearch 결과 배열을 가져옵니다.
      //    예: 이전 search-flights 호출에서 response.data 전체를 Redis 등에 저장했다가 꺼내는 로직
      const cachedOffers = await cache.get<Types.FlightOffer[]>('last_search_offers');
      if (!cachedOffers) {
        throw new Error('No cached flight offers found; please run search-flights first');
      }

      // 2) offerId와 일치하는 항공편 찾기
      const offer = cachedOffers.find((o) => o.id === offerId);
      if (!offer) {
        return {
          content: [
            {
              type: 'text',
              text: `Flight offer ID ${offerId} not found in cache.`,
            },
          ],
          isError: true,
        };
      }

      // 3) 상세 정보 포맷
      const segments = offer.itineraries.flatMap((it) => it.segments);
      const details = {
        price: `${offer.price.total} ${offer.price.currency}`,
        bookableSeats: offer.numberOfBookableSeats ?? 'Unknown',
        airlines: offer.validatingAirlineCodes.join(', '),
        segments: segments.map((seg) => ({
          from: `${seg.departure.iataCode} @ ${seg.departure.at}`,
          to:   `${seg.arrival.iataCode} @ ${seg.arrival.at}`,
          carrier: `${seg.carrierCode}${seg.number}`,
        })),
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(details, null, 2),
          },
        ],
      };
    } catch (error: unknown) {
      console.error('Error getting flight details:', error);
      return {
        content: [
          {
            type: 'text',
            text: `Error getting flight details: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  }
);