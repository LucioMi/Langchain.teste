import express from 'express';
import { env, assertEnv } from './config/env';
import { createMessageTrace } from './observability/langfuse';

const app = express();
app.use(express.json());

assertEnv();

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.post('/webhook/teste.agente.codigo', async (req, res) => {
  try {
    const body = req.body;
    const message: string = body?.data?.message?.conversation || '';
    const userId: string = body?.sender || body?.data?.key?.remoteJid || 'unknown';
    const messageId: string = body?.data?.key?.id || 'unknown';

    const trace = createMessageTrace(userId, message, messageId);
    const span = trace.span({ name: 'llm_call' });

    const reply = `Recebido: ${message}`;
    span.end({ output: reply });

    res.json({ status: 'ok', reply });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'internal_error' });
  }
});

app.listen(env.port, () => {
  console.log(`Server running on http://localhost:${env.port}`);
});