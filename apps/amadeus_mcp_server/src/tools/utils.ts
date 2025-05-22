export const asText = (payload: unknown) => ({
    type: 'text' as const,
    text: typeof payload === 'string' ? payload : JSON.stringify(payload),
  });