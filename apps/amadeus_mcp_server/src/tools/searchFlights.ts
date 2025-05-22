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
				params
			)) as Types.FlightOfferResponse;

			// ── 항공편 카드 생성 ───────────────────────────────────────────────
			const flights = response.data
				.slice(0, maxResults)
				.map((offer: Types.FlightOffer) => {
					const firstSeg = offer.itineraries[0].segments[0];
					const lastSegArr = offer.itineraries.at(-1)!.segments;
					const lastSeg = lastSegArr[lastSegArr.length - 1];

					return {
						price: Number(offer.price.total), // ▶ number
						currency: offer.price.currency, // ▶ e.g. KRW
						origin: firstSeg.departure.iataCode,
						destination: lastSeg.arrival.iataCode,
						departureDate: firstSeg.departure.at, // ISO-8601
						returnDate: returnDate ?? null,
						bookingUrl: null, // 예약 링크 미구현
					};
				});

			// ── 자연어 메시지 생성 ────────────────────────────────────────────
			const cheapest = flights.reduce(
				(min, f) => (f.price < min.price ? f : min),
				flights[0]
			);
			const message =
				`부엉이 부키가 추천하는 항공편 ${flights.length}개를 찾았어요! ` +
				`가장 저렴한 편은 ${cheapest.origin}→${cheapest.destination} ` +
				`${cheapest.departureDate.split('T')[0]} 출발 · ` +
				`${cheapest.price.toLocaleString()} ${cheapest.currency}, 부키!`;

			// ── 툴 응답 반환 ──────────────────────────────────────────────────
			return {
				content: [
					{
						type: 'text',
						text: JSON.stringify(
							{
								flights,
								message,
							},
							null,
							2
						),
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
	}
);
