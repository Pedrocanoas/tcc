import { app } from './app.js'
import { env } from './config/env.js'
import { warmUpModel } from './services/descricaoService.js'

warmUpModel()

app.listen(env.port, () => {
  console.log(`API rodando em http://localhost:${env.port}`)
})
