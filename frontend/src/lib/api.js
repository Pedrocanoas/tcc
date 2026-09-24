const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000/api'

/**
 * Envia as fotos do livro pro backend e retorna a descrição de condição gerada
 * (usa a primeira, já que todas as fotos de um mesmo livro devem descrever o mesmo estado).
 */
export async function gerarDescricao(photos) {
  const body = new FormData()
  for (const { file } of photos) {
    body.append('fotos', file)
  }

  const response = await fetch(`${API_URL}/livros/gerar-descricao`, { method: 'POST', body })
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.error ?? 'Falha ao gerar descrição.')
  }

  return data.descricoes[0]?.descricao ?? ''
}

/**
 * Tenta ler um código de barras de ISBN nas fotos e, se achar, busca os
 * metadados oficiais do livro (título/autor/editora/ano). Retorna null se
 * nenhuma foto tiver um código legível ou o ISBN não for encontrado.
 */
export async function detectarIsbn(photos) {
  const body = new FormData()
  for (const { file } of photos) {
    body.append('fotos', file)
  }

  const response = await fetch(`${API_URL}/livros/detectar-isbn`, { method: 'POST', body })
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.error ?? 'Falha ao ler código de barras.')
  }

  return data.metadados
}

/**
 * Busca os metadados oficiais do livro a partir de um ISBN digitado
 * manualmente. Retorna null se o ISBN não for encontrado.
 */
export async function buscarPorIsbn(isbn) {
  const response = await fetch(`${API_URL}/livros/isbn/${encodeURIComponent(isbn)}`)
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.error ?? 'Falha ao buscar metadados do ISBN.')
  }

  return data.metadados
}

/**
 * Busca anúncios do mesmo livro na Estante Virtual e resume os preços
 * encontrados (menor, maior, média) pra ajudar a precificar. Retorna null se
 * a busca falhar; `quantidade: 0` se não achar nenhum anúncio parecido.
 */
export async function buscarPrecos(titulo, autor, condicao) {
  const params = new URLSearchParams({ titulo })
  if (autor) params.set('autor', autor)
  if (condicao) params.set('condicao', condicao)

  const response = await fetch(`${API_URL}/livros/precos?${params}`)
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.error ?? 'Falha ao buscar preços.')
  }

  return data.resultado
}
