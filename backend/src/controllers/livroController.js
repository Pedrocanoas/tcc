import { unlink } from 'node:fs/promises'

import { gerarDescricoes } from '../services/descricaoService.js'

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
