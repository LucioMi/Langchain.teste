import { Langfuse } from 'langfuse';
import { env } from '../config/env';

export const langfuse = new Langfuse({
  publicKey: env.langfusePublicKey,
  secretKey: env.langfuseSecretKey,
  baseUrl: env.langfuseHost,
});

export function createMessageTrace(userId: string, message: string, messageId: string) {
  const trace = langfuse.trace({
    name: 'whatsapp_agent',
    userId,
    input: message,
    metadata: { messageId },
  });
  return trace;
}