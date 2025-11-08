import axios from 'axios';
import { env } from '../config/env';

type SendOptions = { linkPreview?: boolean };

export async function sendText(number: string, text: string, options?: SendOptions) {
  const url = `${env.evolutionBaseUrl}/message/sendText/${env.evolutionInstance}`;
  const body = { number, text, options: options ?? { linkPreview: true } };
  const headers = {
    'Content-Type': 'application/json',
    apikey: env.evolutionToken,
  } as Record<string, string>;
  const res = await axios.post(url, body, { headers });
  return res.data;
}