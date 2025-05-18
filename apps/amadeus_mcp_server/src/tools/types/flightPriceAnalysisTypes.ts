export interface PriceAnalysisParams {
    [key: string]: string | undefined;
    originLocationCode: string;
    destinationLocationCode: string;
    departureDate: string;
    returnDate?: string;
    currencyCode: string;
  }

  export
  interface PriceAnalysisResponse {
    data: Array<{
      type: string;
      origin: string;
      destination: string;
      departureDate: string;
      returnDate?: string;
      priceMetrics: Array<{
        amount: string;
        quartileRanking: string;
        [key: string]: string | number | boolean | undefined | null;
      }>;
      [key: string]:
        | string
        | number
        | boolean
        | undefined
        | null
        | Array<Record<string, unknown>>;
    }>;
  }

  