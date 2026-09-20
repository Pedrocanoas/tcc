import 'dotenv/config'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = path.resolve(__dirname, '../../..')
const MODEL_DIR = path.resolve(REPO_ROOT, 'model')
const DEFAULT_PYTHON_BIN =
  process.platform === 'win32'
    ? path.join(MODEL_DIR, '.venv', 'Scripts', 'python.exe')
    : path.join(MODEL_DIR, '.venv', 'bin', 'python')

export const env = {
  port: process.env.PORT ?? 3000,
  corsOrigin: process.env.CORS_ORIGIN ?? 'http://localhost:5173',
  modelDir: process.env.MODEL_DIR ?? MODEL_DIR,
  pythonBin: process.env.PYTHON_BIN ?? DEFAULT_PYTHON_BIN,
}
