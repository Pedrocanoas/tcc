import express from 'express'
import cors from 'cors'
import morgan from 'morgan'

import { env } from './config/env.js'
import routes from './routes/index.js'
import { notFound } from './middlewares/notFound.js'
import { errorHandler } from './middlewares/errorHandler.js'

export const app = express()

app.use(cors({ origin: env.corsOrigin }))
app.use(morgan('dev'))
app.use(express.json())

app.use('/api', routes)

app.use(notFound)
app.use(errorHandler)
