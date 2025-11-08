import dotenv from 'dotenv';
dotenv.config();

export const env = {
  port: parseInt(process.env.PORT || '5678', 10),
  openaiApiKey: process.env.OPENAI_API_KEY || '',
  evolutionBaseUrl: process.env.EVOLUTION_API_BASE_URL || '',
  evolutionToken: process.env.EVOLUTION_API_TOKEN || '',
  evolutionInstance: process.env.EVOLUTION_INSTANCE || '',
  langfusePublicKey: process.env.LANGFUSE_PUBLIC_KEY || '',
  langfuseSecretKey: process.env.LANGFUSE_SECRET_KEY || '',
  langfuseHost: process.env.LANGFUSE_HOST || '',
};

export function assertEnv() {
  const missing = Object.entries(env)
    .filter(([_, v]) => v === '' || v === undefined)
    .map(([k]) => k);
  if (missing.length) {
    console.warn(`Warn: missing envs: ${missing.join(', ')}`);
  }
}