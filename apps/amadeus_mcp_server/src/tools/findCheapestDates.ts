import { z } from 'zod';
// Tool to search for flights
import { amadeus, cachedApiCall, server } from '../index.js';
import { cache } from '../index.js';
import * as Types from './types/index.js';
import { asText } from './utils.js';
import { DateTime } from 'luxon';

// helpers/date.ts
export const shiftPastToTomorrow = (iso: string): string => {
	const today = DateTime.utc().startOf('day');
	let d = DateTime.fromISO(iso, { zone: 'utc' });
	if (d <= today) {
		d = today.plus({ days: 1 }); // 최소 내일
	}
	return d.toISODate(); // 'YYYY-MM-DD'
};

// apps/amadeus_mcp_server/src/tools.ts

server.tool(
	'find-cheapest-dates',
	'Find the cheapest dates to fly for a given route (using Flight Offers Search v2)',
	{
		originLocationCode: z
			.string()
			.length(3)
			.default('ICN')
			.describe('Origin airport IATA code (e.g., ICN)'),
		destinationLocationCode: z
			.string()
			.length(3)
			.describe('Destination airport IATA code (e.g., FRA)'),
		departureDate: z.string(),
		//.refine(d => new Date(d) >= new Date(), { message: '출발일은 오늘 이후여야 합니다.' }),
		returnDate: z
			.string()
			.optional()
			.describe('Return date in 2025-MM-DD format'),
		maxPrice: z
			.number()
			//	.nullable()
			.optional()
			.default(3000000)
			.describe('Maximum price limit per ticket'),
		nonStop: z
			.boolean()
			.optional()
			.default(true)
			.describe('Only non-stop flights'),
		adults: z.number().min(1).default(1).describe('Number of adult passengers'),
		currencyCode: z
			.string()
			.length(3)
			.default('KRW')
			.describe('Currency code for pricing'),
		maxResults: z
			.number()
			.min(1)
			.default(5)
			.describe('Max number of offers to return'),
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
			const today = new Date().toISOString().slice(0, 10); // 'YYYY-MM-DD'

			// ▸ 1) 요청 파라미터 만들기 전에 '과거 → 오늘' 보정
			const validDepartureDate = departureDate < today ? today : departureDate;
			let validReturnDate = returnDate;
			if (returnDate && returnDate < validDepartureDate) {
				// 왕복인데 복귀일이 출발일 이전이면 출발일 + 7일 정도로 보정
				const tmp = new Date(validDepartureDate);
				tmp.setDate(tmp.getDate() + 7);
				validReturnDate = tmp.toISOString().slice(0, 10);
			}

			// ▸ 2) 파라미터에 **보정된 날짜** 넣기
			const params: Record<string, any> = {
				originLocationCode,
				destinationLocationCode,
				departureDate: validDepartureDate, // ★ 수정
				adults,
				nonStop,
				currencyCode,
				max: maxResults,
			};
			if (validReturnDate) params.returnDate = validReturnDate;
			if (maxPrice) params.maxPrice = maxPrice;

			// ▸ 3) 충분한 디버그 로그
			console.log('[find-cheapest-dates] params →', params);

			// ▸ 4) API 호출
			const rsp = await amadeus.shopping.flightOffersSearch.get(params);

			console.log(`res: ${params.originLocationCode}
        ${params.destinationLocationCode} ${params.departureDate}
        ${params.returnDate} ${params.nonStop} ${params.adults} ${
				params.currencyCode
			}
        ${params.max} - ${rsp.status} - ${
				rsp.statusText
			} - data: ${JSON.stringify(rsp.data)}`);

			console.log('Flight Offers Search response:', rsp.data);

			// 3) 데이터 유효성 검사
			if (!rsp.data || rsp.data.length === 0) {
				return {
					content: [
						{
							type: 'text',
							text: 'No flight offers found for the given criteria.',
						},
					],
					isError: false,
				};
			}

			const cheapest = rsp.data.reduce((prev: any, curr: any) => {
				const prevPrice = parseFloat(prev.price.total);
				const currPrice = parseFloat(curr.price.total);
				return currPrice < prevPrice ? curr : prev;
			});

			// departure/arrival year를 2025로 고정
			cheapest.itineraries.forEach((itinerary: any) => {
				itinerary.segments.forEach((seg: any) => {
					const depDate = new Date(seg.departure.at);
					depDate.setFullYear(2025);
					seg.departure.at = depDate.toISOString();

					const arrDate = new Date(seg.arrival.at);
					arrDate.setFullYear(2025);
					seg.arrival.at = arrDate.toISOString();
				});
			});

			// 5) 응답 포맷
			const seg = cheapest.itineraries[0].segments[0];
			const result = {
				route: `${seg.departure.iataCode}-${seg.arrival.iataCode}`,
				carrier: seg.carrierCode,
				departure: seg.departure.at,
				arrival: seg.arrival.at,
				price: `${cheapest.price.total} ${cheapest.price.currency}`,
				offer_id: cheapest.id,
				// v2 응답의 self 링크
				//  link:      rsp.meta?.links?.self,
			};

			return { content: [asText(result)] };
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
