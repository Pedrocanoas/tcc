import { randomUUID } from 'node:crypto'
import os from 'node:os'
import path from 'node:path'

import { Router } from 'express'
import multer from 'multer'

import { buscarPorIsbn, detectarIsbn, gerarDescricao } from '../controllers/livroController.js'

const ALLOWED_MIME_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp'])

const storage = multer.diskStorage({
  destination: os.tmpdir(),
  filename: (req, file, cb) => cb(null, `${randomUUID()}${path.extname(file.originalname)}`),
})

const upload = multer({
  storage,
  limits: { fileSize: 15 * 1024 * 1024, files: 5 },
  fileFilter: (req, file, cb) => cb(null, ALLOWED_MIME_TYPES.has(file.mimetype)),
})

const router = Router()

router.post('/gerar-descricao', upload.array('fotos', 5), gerarDescricao)
router.post('/detectar-isbn', upload.array('fotos', 5), detectarIsbn)
router.get('/isbn/:isbn', buscarPorIsbn)

export default router
