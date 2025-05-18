/**
 * Tool to find cheapest travel dates
 */
export interface CheapestDateResult {
    data: Array<{
      type: string;
      origin: string;
      destination: string;
      departureDate: string;
      returnDate?: string | null;
      price: {
        total: string;
        currency: string;
      };
    }>;
  }