export function errorHandler(err, req, res, _next) {
  console.error(err)
  const status = err.status ?? (err.name === 'MulterError' ? 400 : 500)
  res.status(status).json({ error: err.message ?? 'Erro interno do servidor' })
}
