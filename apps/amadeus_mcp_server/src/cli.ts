#!/usr/bin/env node
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { server, amadeus } from './index.js';
import {main} from './index.js';

async function run() {
  try {
    await main();
  } catch (err) {
    console.error('Fatal error in CLI:', err);
    process.exit(1);
  }
}

run();