import 'dotenv/config'

export const env = {
  port: process.env.PORT ?? 3000,
  corsOrigin: process.env.CORS_ORIGIN ?? 'http://localhost:5173',
}
