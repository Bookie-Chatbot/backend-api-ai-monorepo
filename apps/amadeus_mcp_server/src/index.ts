import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import Amadeus from 'amadeus';
import dotenv from 'dotenv';
import NodeCache from 'node-cache';
import type { Request, Response } from 'express';
import { z } from 'zod';


// Define a type for our cache to make TypeScript happy
type TypedCache = {
  get: <T>(key: string) => T | undefined;
  set: <T>(key: string, value: T, ttl?: number) => boolean;
};

dotenv.config();

// Amadeus 인증
export let amadeus = null;
if (process.env.AMADEUS_CLIENT_ID && process.env.AMADEUS_CLIENT_SECRET) {
  amadeus = new Amadeus({
    clientId: process.env.AMADEUS_CLIENT_ID,
    clientSecret: process.env.AMADEUS_CLIENT_SECRET,
  });
} else {
  console.error('Warning: Amadeus credentials not found');
}

// MCP 서버 생성
export const server = new McpServer({
  name: 'amadeus-mcp-server',
  version: '1.0.0'
});

// 간단한 캐시
export const cache = new NodeCache({
  stdTTL: 600,
  checkperiod: 120,
  useClones: false
});

/**
 * Wrapper for Amadeus API calls with caching
 * @param cacheKey - Key for caching
 * @param ttl - Time to live in seconds
 * @param apiCall - Function that returns a promise with the API call
 * @returns Promise with API response
 */
export async function cachedApiCall<T>(
  cacheKey: string,
  ttl: number,
  apiCall: () => Promise<T>,
): Promise<T> {
  // Check if we have a cached response
  const cachedResponse = cache.get<T>(cacheKey);
  if (cachedResponse) {
    console.error(`Cache hit for ${cacheKey}`);
    return cachedResponse;
  }

  // If not cached, make the API call
  console.error(`Cache miss for ${cacheKey}, calling API...`);
  try {
    const response = await apiCall();

    // Cache the response with the specified TTL
    cache.set<T>(cacheKey, response, ttl);

    return response;
  } catch (error: unknown) {
    console.error(`API call failed for ${cacheKey}:`, error);
    throw error;
  }
}


// SSE 연결들을 저장
const activeTransports = new Map<string, SSEServerTransport>();

// 익명 함수로 서버 구동
export async function main() {
  // Tools, resources, prompt 등을 사전에 등록
  await Promise.all([
    import('./tools.js'),
    import('./resources.js'),
    import('./prompt.js')
  ]);

  // Express 준비
  const app = express();
  app.use(cors());
  app.use(bodyParser.json());

  const PORT = process.env.AMADEUS_PORT || 8020;

  app.get('/sse', async (req, res) => {
    console.error('New SSE connection');

    // 헤더·handshake를 SDK가 처리하도록 transport 먼저 만든다
    const transport = new SSEServerTransport('/messages', res);
    await server.connect(transport);

    // 연결이 끝난 뒤 세션 ID를 받아서 보관
    // 최신 SDK: connectionId, 구버전: sessionId
    const id: string = (transport as any).connectionId ?? (transport as any).sessionId;
    activeTransports.set(id, transport);
    console.error('[DEBUG] registered session', id);

    req.on('close', () => {
      console.error('SSE closed', id);
      activeTransports.delete(id);
    });
  });

app.post('/messages', async (req, res) => {
  const id = (req.query.sessionId as string) ?? (req.query.connectionId as string);
  const transport = activeTransports.get(id);
  if (!transport) return res.status(404).json({ error: 'Session not found' });

  // pass req.body explicitly ** 진짜 중요 이부분
  await transport.handlePostMessage(req, res, req.body);
});

  // 간단한 Health 체크
  app.get('/health', (req, res) => {
    res.json({
      status: 'ok',
      connections: activeTransports.size,
      version: process.env.npm_package_version || '1.0.0'
    });
  });

  // 서버 시작
  app.listen(PORT, () => {
    console.error(`Amadeus Flight MCP Server running on port ${PORT}`);
    console.error(`Environment: ${process.env.NODE_ENV || 'development'}`);
    console.error(`Amadeus API client initialized: ${!!amadeus}`);
  });
}

// ...existing code...
server.tool(
  'initialize',
  'JSON-RPC handshake',
  {
    protocolVersion: z.string().optional(),
    capabilities: z.any().optional(),
    clientInfo: z.any().optional(),
  },
  async ({ protocolVersion, capabilities, clientInfo }) => {
    console.error('[DEBUG] initialize RPC called', { protocolVersion, capabilities, clientInfo });
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            initialized: true,
            protocolVersion,
            capabilities,
            clientInfo,
          }),
        },
      ],
    };
  },
);


if (process.argv[1] === new URL(import.meta.url).pathname) {
  main().catch((error: unknown) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}