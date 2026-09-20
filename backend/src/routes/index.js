import { Router } from 'express'
import health from './health.js'
import livros from './livros.js'

const router = Router()

router.use('/health', health)
router.use('/livros', livros)

export default router
