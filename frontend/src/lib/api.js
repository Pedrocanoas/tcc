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
