import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

import { env } from '../config/env.js'

const execFileAsync = promisify(execFile)

/**
 * Roda `python -m src.infer --json <fotos>` no ambiente do model/ e retorna
 * uma descrição de condição gerada por foto.
 */
export async function gerarDescricoes(imagePaths) {
  let stdout
  try {
    ;({ stdout } = await execFileAsync(env.pythonBin, ['-m', 'src.infer', '--json', ...imagePaths], {
      cwd: env.modelDir,
      maxBuffer: 10 * 1024 * 1024,
    }))
  } catch (err) {
    if (err.code === 'ENOENT') {
      throw Object.assign(
        new Error(`Python do model/ não encontrado em ${env.pythonBin}. Rode o setup do model/ (ver model/README.md).`),
        { status: 500 },
      )
    }
    throw Object.assign(new Error(`Falha ao gerar descrição: ${err.stderr ?? err.message}`), { status: 500 })
  }

  let results
  try {
    results = JSON.parse(stdout)
  } catch {
    throw Object.assign(new Error('Saída inesperada do script de inferência (não é JSON válido).'), { status: 500 })
  }

  return results.map(({ image, caption }) => ({ arquivo: image, descricao: caption }))
}
