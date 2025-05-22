import { type AnalyzedQuery, TravelQueryType } from './queryAnalyzer.js';
import { server } from './index.js';
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

// Interface for tool selection and parameter mapping
interface ToolMapping {
	primaryTool: string;
	secondaryTools?: string[];
	parameterMap: (query: AnalyzedQuery) => Promise<Record<string, any>>;
}

// Map query types to appropriate tools and parameter mappings
const toolMappings: Record<TravelQueryType, ToolMapping> = {
	[TravelQueryType.INSPIRATION]: {
		primaryTool: 'discover-destinations',
		secondaryTools: ['search-flights'],
		async parameterMap(query) {
			return {
				originLocationCode: query.origin?.code || '',
				maxPrice: query.budget?.amount,
				departureDate: query.timeFrame.value,
				tripDuration: query.duration?.value.toString(),
			};
		},
	},

	[TravelQueryType.SPECIFIC_ROUTE]: {
		primaryTool: 'find-best-deals',
		secondaryTools: ['analyze-flight-prices', 'find-cheapest-dates'],
		async parameterMap(q) {
			const rawDepart = Array.isArray(q.timeFrame.value)
				? q.timeFrame.value[0]
				: q.timeFrame.value;

			const rawReturn = Array.isArray(q.timeFrame.value)
				? q.timeFrame.value[1]
				: undefined;

			return {
				originLocationCode: q.origin?.code ?? '',
				destinationLocationCode: q.destinations[0]?.code ?? '',
				departureDate: shiftPastToTomorrow(rawDepart),
				returnDate: rawReturn ? shiftPastToTomorrow(rawReturn) : undefined,
				travelClass: q.preferences?.class?.toUpperCase(),
			};
		},
	},

	[TravelQueryType.MULTI_CITY]: {
		primaryTool: 'plan-multi-city-trip',
		secondaryTools: ['search-flights', 'airport-routes'],
		async parameterMap(query) {
			const cities = query.destinations.map((dest) => dest.code).join(',');
			return {
				cities,
				startDate: Array.isArray(query.timeFrame.value)
					? query.timeFrame.value[0]
					: query.timeFrame.value,
				endDate: Array.isArray(query.timeFrame.value)
					? query.timeFrame.value[1]
					: '',
				homeAirport: query.origin?.code || '',
			};
		},
	},

	[TravelQueryType.FLEXIBLE_VALUE]: {
		primaryTool: 'find-cheapest-dates',
		secondaryTools: ['analyze-flight-prices'],
		async parameterMap(query) {
			return {
				originLocationCode: query.origin?.code || '',
				destinationLocationCode: query.destinations[0]?.code || '',
				earliestDepartureDate: Array.isArray(query.timeFrame.value)
					? query.timeFrame.value[0]
					: query.timeFrame.value,
				latestDepartureDate: Array.isArray(query.timeFrame.value)
					? query.timeFrame.value[1]
					: '',
				tripDuration: query.duration?.value.toString(),
			};
		},
	},
	// **추가**: Price Analysis 쿼리 → flight-price-analysis 호출
	[TravelQueryType.PRICE_ANALYSIS]: {
		primaryTool: 'flight-price-analysis',
		// flight-price-analysis 툴만 쓰면 충분
		async parameterMap(query) {
			// origin, destination, departureDate를 분석 결과에서 꺼내오거나
			// 캐시된 last_search_params를 fallback으로 사용
			let origin = query.origin?.code;
			let dest = query.destinations[0]?.code;
			let depart = Array.isArray(query.timeFrame.value)
				? query.timeFrame.value[0]
				: query.timeFrame.value;
			const params: Record<string, any> = {
				originIataCode: origin,
				destinationIataCode: dest,
				departureDate: depart,
				currencyCode: query.budget?.currency || 'KRW',
				// 편도/왕복 여부는 isFlexibleValue에 따라 결정
				oneWay: query.timeFrame.isFlexible,
			};
			return params;
		},
	},
};

// Process the analyzed query and call appropriate tools
export async function processQuery(analyzedQuery: AnalyzedQuery): Promise<{
	mainResult: any;
	supplementaryResults?: Record<string, any>;
	confidence: number;
	suggestedFollowUp?: string[];
}> {
	const mapping = toolMappings[analyzedQuery.type];

	if (!mapping) {
		throw new Error(
			`No tool mapping found for query type: ${analyzedQuery.type}`
		);
	}

	try {
		// Map the analyzed query to tool parameters
		const params = await mapping.parameterMap(analyzedQuery);

		// Call the primary tool
		const mainResult = await server.prompt(mapping.primaryTool, () => params);

		// Call secondary tools if needed and if confidence is high enough
		const supplementaryResults: Record<string, any> = {};
		if (mapping.secondaryTools && analyzedQuery.confidence > 0.7) {
			for (const tool of mapping.secondaryTools) {
				try {
					supplementaryResults[tool] = await server.prompt(tool, () => params);
				} catch (error) {
					console.error(`Error running secondary tool ${tool}:`, error);
				}
			}
		}

		// Generate follow-up suggestions based on ambiguities or missing information
		const suggestedFollowUp = generateFollowUpQuestions(analyzedQuery);

		return {
			mainResult,
			supplementaryResults:
				Object.keys(supplementaryResults).length > 0
					? supplementaryResults
					: undefined,
			confidence: analyzedQuery.confidence,
			suggestedFollowUp,
		};
	} catch (error) {
		console.error('Error processing query:', error);
		throw error;
	}
}

// Generate follow-up questions based on analysis
function generateFollowUpQuestions(query: AnalyzedQuery): string[] {
	const questions: string[] = [];

	// Check for missing or ambiguous information
	if (!query.origin?.code) {
		questions.push('Which city would you like to depart from?');
	}

	if (query.timeFrame.isFlexible) {
		questions.push('Do you have specific dates in mind for your travel?');
	}

	if (!query.budget && query.type !== TravelQueryType.SPECIFIC_ROUTE) {
		questions.push('Do you have a budget in mind for this trip?');
	}

	if (!query.duration && query.type !== TravelQueryType.SPECIFIC_ROUTE) {
		questions.push('How long would you like to travel for?');
	}

	if (query.ambiguities) {
		questions.push(...query.ambiguities);
	}

	return questions;
}

// Example usage:
// const query = "I want to go somewhere warm in December for about a week";
// const analyzed = await analyzeQuery(query);
// const result = await processQuery(analyzed);
