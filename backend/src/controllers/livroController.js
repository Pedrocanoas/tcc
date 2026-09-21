import { unlink } from 'node:fs/promises'

import { detectarIsbnNasFotos } from '../services/barcodeService.js'
import { gerarDescricoes } from '../services/descricaoService.js'
import { buscarMetadadosPorIsbn } from '../services/isbnLookupService.js'

export async function gerarDescricao(req, res, next) {
  const files = req.files ?? []
  if (files.length === 0) {
    return res.status(400).json({ error: 'Envie ao menos uma foto no campo "fotos".' })
  }

  try {
    const descricoes = await gerarDescricoes(files.map((file) => file.path))
    res.json({ descricoes })
  } catch (err) {
    next(err)
  } finally {
    await Promise.all(files.map((file) => unlink(file.path).catch(() => {})))
  }
}

export async function detectarIsbn(req, res, next) {
  const files = req.files ?? []
  if (files.length === 0) {
    return res.status(400).json({ error: 'Envie ao menos uma foto no campo "fotos".' })
  }

  try {
    const isbn = await detectarIsbnNasFotos(files.map((file) => file.path))
    const metadados = isbn ? await buscarMetadadosPorIsbn(isbn) : null
    res.json({ isbn, metadados })
  } catch (err) {
    next(err)
  } finally {
    await Promise.all(files.map((file) => unlink(file.path).catch(() => {})))
  }
}

export async function buscarPorIsbn(req, res, next) {
  try {
    const metadados = await buscarMetadadosPorIsbn(req.params.isbn)
    res.json({ metadados })
  } catch (err) {
    next(err)
  }
}
