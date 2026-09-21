#!/usr/bin/env node
/**
 * Busca titulo/autor/editora/ano/isbn/idioma/descricao dos livros já raspados
 * (que têm fotos mas ainda não têm descricao.txt) usando o mapeamento
 * livro->SKU salvo em .sku-map.json (gerado a partir do scrape de fotos).
 *
 * Uso:
 *   node scrape_descriptions.mjs [--delay 2.5]
 */

import { readdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const RAW_DIR = path.join(__dirname, 'raw')
const SKU_MAP_FILE = path.join(__dirname, '.sku-map.json')

const BASE_URL = 'https://www.estantevirtual.com.br'
const HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
const STATE_MARKER = 'window.__INITIAL_STATE__='

function parseArgs() {
  const args = { delay: 2.5 }
  const argv = process.argv.slice(2)
  for (let i = 0; i < argv.length; i++) {
    const raw = argv[i].replace(/^--/, '')
    const [key, inlineVal] = raw.split('=')
    const val = inlineVal ?? argv[++i]
    if (key === 'delay') args.delay = Number(val)
  }
  return args
}

const sleep = (s) => new Promise((resolve) => setTimeout(resolve, s * 1000))

async function fileExists(p) {
  try {
    await readFile(p)
    return true
  } catch {
    return false
  }
}

function extractInitialState(html) {
  const idx = html.indexOf(STATE_MARKER)
  if (idx === -1) return null
  const jsonStart = idx + STATE_MARKER.length
  // acha o fim do objeto JSON contando chaves, ja que vem seguido de mais `window.X=...`
  let depth = 0
  let inString = false
  let escape = false
  for (let i = jsonStart; i < html.length; i++) {
    const ch = html[i]
    if (escape) {
      escape = false
      continue
    }
    if (ch === '\\') {
      escape = true
      continue
    }
    if (ch === '"') inString = !inString
    if (inString) continue
    if (ch === '{') depth++
    if (ch === '}') {
      depth--
      if (depth === 0) {
        return JSON.parse(html.slice(jsonStart, i + 1))
      }
    }
  }
  return null
}

function buildDescricaoTxt(product) {
  const attrs = product.formattedAttributes ?? {}
  const description = product.currentProduct?.description ?? product.currentProduct?.longDescription ?? ''

  const linhas = [
    `Titulo: ${product.name ?? ''}`,
    `Autor: ${product.author ?? ''}`,
    `Editora: ${attrs.publisher ?? ''}`,
    `Ano: ${attrs.year ?? ''}`,
    `ISBN: ${attrs.isbn ?? ''}`,
    `Idioma: ${attrs.language ?? ''}`,
    `Condicao (site): usado`,
    `SKU: ${product.sku?.replace(/-\d+$/, '') ?? ''}`,
    '',
    'Descricao do vendedor:',
    description,
  ]
  return linhas.join('\n') + '\n'
}

async function main() {
  const args = parseArgs()
  console.log(`config: delay=${args.delay}s`)

  const skuMap = JSON.parse(await readFile(SKU_MAP_FILE, 'utf-8'))
  const livros = Object.keys(skuMap).sort((a, b) => Number(a.slice(5)) - Number(b.slice(5)))
  console.log(`livros no mapeamento: ${livros.length}`)

  let ok = 0
  let skipped = 0
  let failed = 0

  for (const livro of livros) {
    const destPath = path.join(RAW_DIR, livro, 'descricao.txt')
    if (await fileExists(destPath)) {
      skipped++
      continue
    }

    const sku = skuMap[livro]
    const url = `${BASE_URL}/livro/${sku}`
    try {
      const res = await fetch(url, { headers: HEADERS })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const html = await res.text()
      const state = extractInitialState(html)
      const product = state?.Product
      if (!product) throw new Error('Product não encontrado no __INITIAL_STATE__')

      await writeFile(destPath, buildDescricaoTxt(product), 'utf-8')
      console.log(`${livro} <- ${sku}: descricao.txt escrito`)
      ok++
    } catch (err) {
      console.error(`[aviso] falha em ${livro} (${sku}): ${err.message}`)
      failed++
    }

    await sleep(args.delay)
  }

  console.log(`concluido: ${ok} escritos, ${skipped} ja existiam, ${failed} falharam`)
}

main()
