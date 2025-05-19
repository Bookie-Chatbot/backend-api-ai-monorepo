// src/tools/flight-price-analysis.ts
import { server, amadeus } from '../index.js';
import { z } from 'zod';
import { cache } from '../index.js';

server.tool(
  'flight-price-analysis',
  'Get flight price analysis for a route',
  {
    originIataCode:      z.string().length(3).describe('Origin airport IATA code (e.g., ICN)'),
    destinationIataCode: z.string().length(3).describe('Destination airport IATA code (e.g., FRA)'),
    departureDate:       z.string().describe('Departure date in YYYY-MM-DD format'),
    currencyCode:        z.string().length(3).default('KRW').describe('Currency code'),
    oneWay:              z.boolean().optional().describe('If true, analyze one-way fares'),
  },
  async (slots) => {
    // 1) oneWay 값 디폴트 처리: returnDate 없으면 true, 있으면 false
    const isOneWay = slots.oneWay ?? true;

    // 2) Analytics API 파라미터 준비 (POSTMAN에서 테스트한 이름 그대로)
    const analyticsParams: Record<string, string | boolean> = {
      originIataCode: slots.originIataCode,
      destinationIataCode: slots.destinationIataCode,
      departureDate: slots.departureDate,
      currencyCode: slots.currencyCode,
      oneWay: isOneWay,
    };

    // 1) 유저가 파라미터를 안줬다면, 캐시에서 꺼내오기
    let { originIataCode, destinationIataCode, departureDate, currencyCode } = slots;
    if (!originIataCode || !destinationIataCode || !departureDate) {
      const last = await cache.get<string>('last_search_params');
      if (!last) {
        throw new Error('이전에 검색된 항공편이 없습니다. 먼저 search-flights를 실행해주세요.');
      }
      const params = JSON.parse(last);
      originIataCode      ??= params.originLocationCode;
      destinationIataCode ??= params.destinationLocationCode;
      departureDate       ??= params.departureDate;
       currencyCode        ??= params.currencyCode;
    }
    if (!originIataCode || !destinationIataCode || !departureDate) {
      return {
        content: [
          {
            type: 'text',
            text: '필수 파라미터가 누락되었습니다. originIataCode, destinationIataCode, departureDate를 확인해주세요.',
          },
        ],
        isError: true,
      };
    }
    try {
      // 3) 실제 Amadeus Analytics 호출
      const response = await amadeus.analytics.itineraryPriceMetrics.get(analyticsParams);
    console.log('Flight Price Analysis response:', response.data);

      // 4) 결과 리턴
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
            text: `Error getting price analysis: ${error instanceof Error ? error.message : 'Unknown error'}`,
          },
        ],
        isError: true,
      };
    }
  }
);

