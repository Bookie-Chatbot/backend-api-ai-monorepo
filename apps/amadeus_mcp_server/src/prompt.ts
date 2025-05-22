// apps/amadeus_mcp_server/src/prompt.ts
import { z } from 'zod';
import { server } from './index.js';

server.prompt(
	'analyze-flight-prices',
	'Analyze flight prices for a route',
	{
		originIataCode: z.string().length(3),
		destinationIataCode: z.string().length(3),
		departureDate: z.string(),
		returnDate: z.string().optional(),
	},
	async ({
		originIataCode,
		destinationIataCode,
		departureDate,
		returnDate,
	}) => {
		const schemaDesc = `
다음 스키마에 **정확히** 맞는 JSON 객체 하나만 반환해주세요:

{
  "message": string,
  "origin": string,
  "destination": string,
  "departureDate": string,
  "currencyCode": string,
  "oneWay": boolean,
  "priceMetrics": [
    { "quartileRanking": "MINIMUM"|"FIRST"|"MEDIUM"|"THIRD"|"MAXIMUM", "amount": number },
    …
  ]
}`;

		const userText = `
${originIataCode}→${destinationIataCode} (${departureDate}${
			returnDate ? `, 복귀 ${returnDate}` : ''
		}) 편도 항공권 가격을 분석해주세요.
–
"message": string을 작성할 땐 아래를 고려해서, 2-3줄의 간단한 설명을 포함해주세요.
가격 범위 개요
– 평균 대비 가격 위치
– 최적 예약 시기
– 가성비 항공편 예시
– 추가 인사이트

예시 응답:
{\n  "message": "...",\n  "origin": "...",\n  …\n}`;

		return {
			messages: [
				{
					role: 'user',
					content: { type: 'text', text: `${schemaDesc}\n\n${userText}` },
				},
			],
		};
	}
);

// If you need to search for airport information, you can use the search-airports tool.
// Prompt for finding the best flight deals
server.prompt(
	'find-best-deals',
	'Find the best flight deals',
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
		travelClass: z
			.enum(['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'])
			.optional()
			.describe('Travel class'),
	},
	async ({
		originLocationCode,
		destinationLocationCode,
		departureDate,
		returnDate,
		travelClass,
	}) => {
		return {
			messages: [
				{
					role: 'user',
					content: {
						type: 'text',
						text: `Please find the best flight deals for a trip from ${originLocationCode} to ${destinationLocationCode} departing on ${departureDate}${
							returnDate ? ` and returning on ${returnDate}` : ''
						}${travelClass ? ` in ${travelClass} class` : ''}.

Please use the search-flights tool to find options, and organize them by:

1. Best value options (considering price, duration, and convenience)
2. Cheapest options regardless of convenience
3. Most convenient options (fewest stops, best times)

For each option, provide a brief summary of why it might be a good choice for different types of travelers.`,
					},
				},
			],
		};
	}
);

// Please use the search-airports tool to confirm airport codes for each city, and then use the search-flights tool to find optimal flight routes between each city.
// utils/dateGuards.ts
import { DateTime } from 'luxon';

// ISO-date string that must be today or later
export const futureISO = z.string().refine(
	(d) => {
		const dt = DateTime.fromISO(d, { zone: 'utc' });
		return dt.isValid && dt.startOf('day') >= DateTime.utc().startOf('day');
	},
	{ message: 'Date must be today or in the future (YYYY-MM-DD).' }
);

// convenience: return a corrected (future) date string
export const shiftPastToToday = (iso: string) => {
	const dt = DateTime.fromISO(iso, { zone: 'utc' });
	return dt.isValid && dt < DateTime.utc().startOf('day')
		? DateTime.utc().toISODate()
		: iso;
};

// Prompt for finding cheapest dates to travel
server.prompt(
	'find-cheapest-dates',
	'Find the cheapest future-dated flight deals',
	{
		originLocationCode: z.string().length(3),
		destinationLocationCode: z.string().length(3),
		earliestDepartureDate: futureISO,
		latestDepartureDate: futureISO,
		tripDuration: z
			.string()
			.regex(/^\d+$/, 'Duration must be an integer (days)')
			.optional(),
	},
	({
		originLocationCode,
		destinationLocationCode,
		earliestDepartureDate,
		latestDepartureDate,
		tripDuration,
	}) => {
		// 1️⃣ Auto-correct dates -------------------------------------------
		let earliest = shiftPastToToday(earliestDepartureDate);
		let latest = shiftPastToToday(latestDepartureDate);

		// If the user reversed them, swap & log
		if (DateTime.fromISO(latest) < DateTime.fromISO(earliest)) {
			[earliest, latest] = [latest, earliest];
		}

		// 2️⃣ Optional round-trip duration logic ----------------------------
		let durationLine = '';
		if (tripDuration) {
			durationLine = ` for roughly ${tripDuration}-day stays`;
		}

		// 3️⃣ Compose the *corrected* user prompt ---------------------------
		const promptText = `
  I'm looking for the **cheapest dates** to fly from **${originLocationCode} → ${destinationLocationCode}**
  between **${earliest}** and **${latest}**${durationLine}.

  • Please call **find-cheapest-dates** with these corrected parameters.
  • After you retrieve results, provide
	1. the top cheapest date pairs
	2. a brief price-trend analysis across the window
	3. which days of the week are consistently cheapest
	4. any holidays/events pushing prices up (use public-holiday/major-event data)
	5. sample nonstop flight options for the very cheapest dates.
  `;

		return {
			messages: [
				{
					role: 'user',
					content: { type: 'text', text: promptText.trim() },
				},
			],
		};
	}
);

// Prompt for planning a multi-city trip
server.prompt(
	'plan-multi-city-trip',
	'Plan a multi-city trip',
	{
		cities: z
			.string()
			.describe('Comma-separated list of city or airport codes to visit'),
		startDate: z.string().describe('Start date of trip in YYYY-MM-DD format'),
		endDate: z.string().describe('End date of trip in YYYY-MM-DD format'),
		homeAirport: z.string().length(3).describe('Home airport IATA code'),
	},
	async ({ cities, startDate, endDate, homeAirport }) => {
		return {
			messages: [
				{
					role: 'user',
					content: {
						type: 'text',
						text: `Please help me plan a multi-city trip visiting the following cities: ${cities}. I'll be starting from ${homeAirport} on ${startDate} and returning on ${endDate}.


For my trip plan, I would like:

1. The most logical order to visit these cities to minimize backtracking
2. Flight options between each city
3. Recommended number of days in each location based on the total trip duration
4. Any insights about potential challenges or considerations for this itinerary

Please outline a complete trip plan with flight details and suggested stays in each location.`,
					},
				},
			],
		};
	}
);

// Prompt for discovering flight destinations
server.prompt(
	'discover-destinations',
	'Find inspiring flight destinations within your budget',
	{
		originLocationCode: z
			.string()
			.length(3)
			.describe('Origin airport IATA code (e.g., MAD)'),
		maxPrice: z.string().optional().describe('Maximum budget for flights'),
		departureDate: z
			.string()
			.optional()
			.describe('Preferred departure date or date range (YYYY-MM-DD)'),
		tripDuration: z
			.string()
			.optional()
			.describe('Desired trip duration in days (e.g., "7" or "2,8" for range)'),
	},
	async ({ originLocationCode, maxPrice, departureDate, tripDuration }) => {
		return {
			messages: [
				{
					role: 'user',
					content: {
						type: 'text',
						text: `Please help me discover interesting destinations I can fly to from ${originLocationCode}${
							maxPrice ? ` within a budget of ${maxPrice}` : ''
						}${departureDate ? ` around ${departureDate}` : ''}${
							tripDuration ? ` for about ${tripDuration} days` : ''
						}.

Please use the flight-inspiration tool to find destinations and then:

1. Group destinations by region or country
2. Highlight the best deals found
3. Provide insights about seasonal trends
4. Suggest specific destinations that offer good value
5. Include any interesting destinations that might be unexpected

For the most interesting options, please use the search-flights tool to find specific flight details.

Please organize the results to help me discover new travel possibilities within my constraints.`,
					},
				},
			],
		};
	}
);
// If needed, use the search-airports tool to get more information about the destinations.

// Prompt for exploring airport routes
server.prompt(
	'explore-airport-routes',
	'Discover direct routes and connections from an airport',
	{
		airportCode: z.string().length(3).describe('Airport IATA code (e.g., JFK)'),
		maxResults: z
			.string()
			.optional()
			.default('20')
			.describe('Maximum number of routes to show'),
	},
	async ({ airportCode, maxResults }) => {
		return {
			messages: [
				{
					role: 'user',
					content: {
						type: 'text',
						text: `Please analyze the routes available from ${airportCode} airport.

Please use the airport-routes tool to find direct destinations, and then:

1. Group destinations by region/continent
2. Highlight major routes with high flight frequency
3. Identify popular leisure and business destinations
4. List any seasonal or unique routes
5. Provide insights about the airport's connectivity

For key routes, please use the search-flights tool to check typical prices and schedules.

Please organize this information to help understand:
- The airport's route network
- Best connection possibilities
- Popular destinations served
- Unique route opportunities`,
					},
				},
			],
		};
	}
);

// Use the search-airports tool to get more details about the connected airports.

// Prompt for finding nearby airports
server.prompt(
	'find-nearby-airports',
	'Find convenient airports near a specific location',
	{
		latitude: z.string().describe('Location latitude'),
		longitude: z.string().describe('Location longitude'),
		radius: z
			.string()
			.optional()
			.default('500')
			.describe('Search radius in kilometers'),
		maxResults: z
			.string()
			.optional()
			.default('10')
			.describe('Maximum number of airports to show'),
	},
	async ({ latitude, longitude, radius, maxResults }) => {
		return {
			messages: [
				{
					role: 'user',
					content: {
						type: 'text',
						text: `Please help me find convenient airports near latitude ${latitude}, longitude ${longitude}${
							radius ? ` within ${radius} kilometers` : ''
						}.

Please use the nearest-airports tool to find airports, and then:

1. Rank airports by convenience (considering distance and flight options)
2. Provide key information about each airport (size, typical destinations)
3. Compare transportation options to/from each airport
4. Highlight any airports with unique advantages
5. Suggest which airports might be best for different types of trips

For the most relevant airports:
- Use the airport-routes tool to check available destinations
- Use the search-flights tool to compare typical prices
- Consider factors like flight frequency and seasonal variations

Please organize this information to help choose the most suitable airport based on:
- Distance and accessibility
- Flight options and frequencies
- Typical prices
- Overall convenience for different types of travel`,
					},
				},
			],
		};
	}
);

// Prompt for comprehensive trip planning
server.prompt(
	'plan-complete-trip',
	'Get comprehensive trip planning assistance',
	{
		originLocationCode: z
			.string()
			.length(3)
			.describe('Origin airport IATA code'),
		budget: z.string().optional().describe('Total budget for flights'),
		departureDate: z
			.string()
			.optional()
			.describe('Preferred departure date or date range'),
		tripDuration: z
			.string()
			.optional()
			.describe('Desired trip duration in days'),
		preferences: z
			.string()
			.optional()
			.describe('Travel preferences (e.g., "beach, culture, food")'),
	},
	async ({
		originLocationCode,
		budget,
		departureDate,
		tripDuration,
		preferences,
	}) => {
		return {
			messages: [
				{
					role: 'user',
					content: {
						type: 'text',
						text: `Please help me plan a trip from ${originLocationCode}${
							budget ? ` with a budget of ${budget}` : ''
						}${departureDate ? ` around ${departureDate}` : ''}${
							tripDuration ? ` for ${tripDuration} days` : ''
						}${preferences ? ` focusing on ${preferences}` : ''}.

Please use multiple tools to create a comprehensive trip plan:

1. Use the flight-inspiration tool to discover potential destinations that match my criteria
2. Use the nearest-airports tool to find alternative departure/arrival airports
3. Use the airport-routes tool to understand connection possibilities
4. Use the find-cheapest-dates tool to optimize travel dates
5. Use the search-flights tool to find specific flight options

Please provide:
1. Top destination recommendations based on my criteria
2. Best flight options and routing suggestions
3. Price analysis and booking timing recommendations
4. Alternative airports to consider
5. A complete trip outline with:
   - Recommended destinations
   - Flight options and prices
   - Suggested itinerary
   - Travel tips and considerations

Please organize all this information into a clear, actionable trip plan.`,
					},
				},
			],
		};
	}
);
