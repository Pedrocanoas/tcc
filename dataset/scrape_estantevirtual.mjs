#!/usr/bin/env node
/**
 * Baixa as fotos dos livros do sebo "Só o Pó" no Estante Virtual (loja
 * própria) pra expandir dataset/raw/. Coleta só as imagens, não a descrição
 * — numera a partir do maior livroNNN já existente e continua de onde parou
 * se rodar de novo (guarda os SKUs já processados em .scrape-state.json).
 *
 * Uso:
 *   node scrape_estantevirtual.mjs [--delay 2.5] [--max-books 1620] [--start-page 1] [--end-page 54]
 */

import { mkdir, readdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const RAW_DIR = path.join(__dirname, 'raw')
const STATE_FILE = path.join(__dirname, '.scrape-state.json')

const BASE_URL = 'https://www.estantevirtual.com.br'
const SELLER_PATH = '/sebos-e-livreiros/sebo-so-o-po'
const HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }

function parseArgs() {
  const args = { delay: 2.5, maxBooks: Infinity, startPage: 1, endPage: 54 }
  const argv = process.argv.slice(2)
  for (let i = 0; i < argv.length; i++) {
    const raw = argv[i].replace(/^--/, '')
    const [key, inlineVal] = raw.split('=')
    const val = inlineVal ?? argv[++i]
    if (key === 'delay') args.delay = Number(val)
    if (key === 'max-books') args.maxBooks = Number(val)
    if (key === 'start-page') args.startPage = Number(val)
    if (key === 'end-page') args.endPage = Number(val)
  }
  return args
}

const sleep = (s) => new Promise((resolve) => setTimeout(resolve, s * 1000))

async function fetchText(url) {
  const res = await fetch(url, { headers: HEADERS })
  if (!res.ok) throw new Error(`HTTP ${res.status} em ${url}`)
  return res.text()
}

async function collectSkus(startPage, endPage, delay) {
  const seen = new Set()
  const skus = []
  for (let page = startPage; page <= endPage; page++) {
    const url = `${BASE_URL}${SELLER_PATH}?page=${page}`
    try {
      const html = await fetchText(url)
      const matches = [...html.matchAll(/\/livro\/([A-Z0-9-]+)/g)].map((m) => m[1])
      let added = 0
      for (const sku of matches) {
        if (!seen.has(sku)) {
          seen.add(sku)
          skus.push(sku)
          added++
        }
      }
      console.log(`pagina ${page}/${endPage}: +${added} livros (total ${skus.length})`)
    } catch (err) {
      console.error(`[aviso] falha na pagina ${page}: ${err.message}`)
    }
    await sleep(delay)
  }
  return skus
}

async function downloadBookPhotos(sku, destDir) {
  const url = `${BASE_URL}/livro/${sku}`
  const html = await fetchText(url)

  const re = new RegExp(
    `https://static\\.estantevirtual\\.com\\.br/book/00/${sku}/${sku}_detail(\\d)\\.jpg\\?[^"'\\s]*`,
    'g',
  )
  const found = new Map()
  for (const m of html.matchAll(re)) {
    found.set(Number(m[1]), m[0])
  }
  if (found.size === 0) return 0

  await mkdir(destDir, { recursive: true })
  let count = 0
  for (const n of [...found.keys()].sort((a, b) => a - b)) {
    const imgUrl = found.get(n)
    try {
      const res = await fetch(imgUrl, { headers: HEADERS })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const buf = Buffer.from(await res.arrayBuffer())
      await writeFile(path.join(destDir, `foto${count + 1}.jpg`), buf)
      count++
    } catch (err) {
      console.error(`[aviso] falha ao baixar foto ${n} de ${sku}: ${err.message}`)
    }
  }
  return count
}

async function nextLivroNumber() {
  const entries = await readdir(RAW_DIR)
  const nums = entries
    .map((name) => /^livro(\d+)$/.exec(name))
    .filter(Boolean)
    .map((m) => Number(m[1]))
  return (nums.length ? Math.max(...nums) : 0) + 1
}

async function loadDoneSkus() {
  try {
    return new Set(JSON.parse(await readFile(STATE_FILE, 'utf-8')))
  } catch {
    return new Set()
  }
}

async function main() {
  const args = parseArgs()
  console.log(`config: delay=${args.delay}s maxBooks=${args.maxBooks} paginas=${args.startPage}-${args.endPage}`)

  const skus = await collectSkus(args.startPage, args.endPage, args.delay)
  console.log(`total de SKUs coletados: ${skus.length}`)

  const doneSkus = await loadDoneSkus()
  let nextNum = await nextLivroNumber()
  let processed = 0
  let totalPhotos = 0

  for (const sku of skus) {
    if (processed >= args.maxBooks) break
    if (doneSkus.has(sku)) continue

    const nome = `livro${String(nextNum).padStart(3, '0')}`
    try {
      const n = await downloadBookPhotos(sku, path.join(RAW_DIR, nome))
      if (n > 0) {
        console.log(`${nome} <- ${sku}: ${n} fotos`)
        nextNum++
        totalPhotos += n
      } else {
        console.log(`[aviso] ${sku}: nenhuma foto encontrada, pulando`)
      }
    } catch (err) {
      console.error(`[aviso] falha em ${sku}: ${err.message}`)
    }

    doneSkus.add(sku)
    await writeFile(STATE_FILE, JSON.stringify([...doneSkus]))
    processed++
    await sleep(args.delay)
  }

  console.log(`concluido: ${processed} livros processados, ${totalPhotos} fotos baixadas`)
}

main()
