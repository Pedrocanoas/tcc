const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000/api'

function normalizarSentenca(sentenca) {
  return sentenca
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .trim()
}

/** Fração de palavras da sentença menor que também aparecem na maior —
 * simples, mas dá pra comparar frases parecidas o bastante sem precisar de
 * embeddings/NLP de verdade. */
function similaridade(a, b) {
  const palavrasA = new Set(normalizarSentenca(a).split(/\s+/).filter(Boolean))
  const palavrasB = new Set(normalizarSentenca(b).split(/\s+/).filter(Boolean))
  if (!palavrasA.size || !palavrasB.size) return 0
  let comuns = 0
  for (const palavra of palavrasA) {
    if (palavrasB.has(palavra)) comuns++
  }
  return comuns / Math.min(palavrasA.size, palavrasB.size)
}

const LIMIAR_DUPLICATA = 0.6

/**
 * Combina as legendas geradas pra cada foto num só texto, sem repetir
 * frases parecidas. Cada foto gera uma legenda independente (o modelo só
 * vê uma imagem por vez) — como o prefixo de capa/condição é igual em
 * todas, a frase de abertura tende a se repetir; frases novas (um detalhe
 * que só aparece numa foto específica, tipo grifo ou mancha) são mantidas.
 */
export function combinarDescricoes(descricoes) {
  const sentencasIncluidas = []
  for (const { descricao } of descricoes) {
    const sentencas = descricao.split(/(?<=[.!?])\s+/).filter(Boolean)
    for (const sentenca of sentencas) {
      const jaTem = sentencasIncluidas.some((existente) => similaridade(existente, sentenca) >= LIMIAR_DUPLICATA)
      if (!jaTem) sentencasIncluidas.push(sentenca)
    }
  }
  return sentencasIncluidas.join(' ')
}

/**
 * Envia as fotos do livro pro backend e retorna a descrição de condição
 * combinada (uma legenda é gerada por foto — junta sem repetir frases
 * parecidas, ver `combinarDescricoes`). `capa`/`condicao`, quando
 * informados, condicionam a legenda gerada ao que o formulário já sabe, em
 * vez do modelo ter que adivinhar isso pela foto.
 */
export async function gerarDescricao(photos, capa, condicao) {
  const body = new FormData()
  for (const { file } of photos) {
    body.append('fotos', file)
  }
  if (capa) body.append('capa', capa)
  if (condicao) body.append('condicao', condicao)

  const response = await fetch(`${API_URL}/livros/gerar-descricao`, { method: 'POST', body })
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.error ?? 'Falha ao gerar descrição.')
  }

  return combinarDescricoes(data.descricoes)
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
