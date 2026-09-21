import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

import { env } from '../config/env.js'

const execFileAsync = promisify(execFile)

/**
 * Roda `python -m src.detect_barcode` nas fotos e retorna o ISBN do código de
 * barras encontrado (ou null se nenhuma foto tiver um código legível). Não
 * carrega nenhum modelo — leve o suficiente pra rodar como processo avulso.
 */
export async function detectarIsbnNasFotos(imagePaths) {
  const { stdout } = await execFileAsync(env.pythonBin, ['-m', 'src.detect_barcode', ...imagePaths], {
    cwd: env.modelDir,
    maxBuffer: 10 * 1024 * 1024,
  })

  const { isbn } = JSON.parse(stdout)
  return isbn
}
