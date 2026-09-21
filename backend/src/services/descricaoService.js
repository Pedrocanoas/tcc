import { spawn } from 'node:child_process'
import readline from 'node:readline'

import { env } from '../config/env.js'

const PYTHON_NOT_FOUND_MESSAGE = `Python do model/ não encontrado em ${env.pythonBin}. Rode o setup do model/ (ver model/README.md).`

let worker = null
let queue = []

function rejectQueue(err) {
  for (const pending of queue) pending.reject(err)
  queue = []
}

function ensureWorker() {
  if (worker) return worker

  const child = spawn(env.pythonBin, ['-m', 'src.serve'], { cwd: env.modelDir })
  const rl = readline.createInterface({ input: child.stdout })

  rl.on('line', (line) => {
    const pending = queue.shift()
    if (!pending) return

    let parsed
    try {
      parsed = JSON.parse(line)
    } catch {
      pending.reject(new Error('Saída inesperada do processo de inferência (não é JSON válido).'))
      return
    }

    if (parsed.error) pending.reject(Object.assign(new Error(`Falha ao gerar descrição: ${parsed.error}`), { status: 500 }))
    else pending.resolve(parsed.ok)
  })

  child.stderr.on('data', (chunk) => console.error(`[model] ${chunk.toString().trim()}`))

  child.on('error', (err) => {
    const wrapped =
      err.code === 'ENOENT' ? Object.assign(new Error(PYTHON_NOT_FOUND_MESSAGE), { status: 500 }) : err
    rejectQueue(wrapped)
    worker = null
  })

  child.on('exit', (code) => {
    console.error(`[model] processo de inferência encerrou (code ${code})`)
    rejectQueue(Object.assign(new Error('Processo de inferência encerrou inesperadamente.'), { status: 500 }))
    worker = null
  })

  worker = child
  return worker
}

/** Sobe o processo de inferência antecipadamente, pra não pagar o custo de
 * carregar o modelo (~15-20s) só na primeira request de verdade. */
export function warmUpModel() {
  ensureWorker()
}

/** Envia as fotos pro processo persistente de inferência e retorna a
 * descrição de condição gerada por foto. As chamadas são atendidas em fila
 * (uma por vez), já que só existe um processo/modelo carregado na GPU/CPU. */
export function gerarDescricoes(imagePaths) {
  const child = ensureWorker()
  return new Promise((resolve, reject) => {
    queue.push({
      resolve: (results) => resolve(results.map(({ image, caption }) => ({ arquivo: image, descricao: caption }))),
      reject,
    })
    child.stdin.write(JSON.stringify(imagePaths) + '\n')
  })
}
