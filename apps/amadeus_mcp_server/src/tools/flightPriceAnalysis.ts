// src/tools/flight-price-analysis.ts
import { server, amadeus } from '../index.js';
import { z } from 'zod';
import { cache } from '../index.js';
import { asText } from './utils.js';

server.tool(
	'analyze-flight-prices',
	'Analyze flight prices for a route',
	{
		originIataCode: z.string().length(3).describe('출발지 IATA 코드'),
		destinationIataCode: z.string().length(3).describe('도착지 IATA 코드'),
		departureDate: z.string().describe('출발일 (2025-MM-DD)'),
		currencyCode: z.string().length(3).default('KRW').describe('통화 코드'),
		oneWay: z.boolean().optional().describe('편도 여부 (기본 true)'),
	},
	async (slots, _extra) => {
		// 기본값 처리
		const isOneWay = slots.oneWay ?? true;

		// Amadeus Analytics API 호출 파라미터
		const analyticsParams: Record<string, string | boolean> = {
			originIataCode: slots.originIataCode,
			destinationIataCode: slots.destinationIataCode,
			departureDate: slots.departureDate,
			currencyCode: slots.currencyCode,
			oneWay: isOneWay,
		};
		console.log('[DEBUG] analyticsParams =', analyticsParams);

		try {
			const response = await amadeus.analytics.itineraryPriceMetrics.get(
				analyticsParams
			);
			console.log('[DEBUG] Amadeus response.data =', response.data);

			const metric = response.data[0];
			const priceMetrics = metric.priceMetrics.map((m: any) => ({
				quartileRanking: m.quartileRanking,
				amount: parseFloat(m.amount),
			}));
			console.log('[DEBUG] formatted priceMetrics =', priceMetrics);

			// 최종 JSON 포맷
			const result = {
				message:
					`${slots.departureDate} ${slots.originIataCode}→${slots.destinationIataCode} ` +
					`편도 최저 ${priceMetrics[0].amount.toLocaleString()} ${
						slots.currencyCode
					}, ` +
					`최고 ${priceMetrics[4].amount.toLocaleString()} ${
						slots.currencyCode
					} 사이에요.`,
				origin: slots.originIataCode,
				destination: slots.destinationIataCode,
				departureDate: slots.departureDate,
				currencyCode: slots.currencyCode,
				oneWay: isOneWay,
				priceMetrics,
			};
			console.log('[DEBUG] formatted result =', result);

			return { content: [asText(result)], isError: false };

			/* content: [
              {
                type: 'text',
                text: JSON.stringify(result)
              }
            ],*/
		} catch (error) {
			console.error('[ERROR] price-analysis failed:', error);
			return {
				content: [
					{
						type: 'text',
						text: `가격 분석 중 오류가 발생했어요: ${
							error instanceof Error ? error.message : 'Unknown error'
						}`,
					},
				],
				isError: true,
			};
		}
	}
);
