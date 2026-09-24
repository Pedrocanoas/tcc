const BASE_URL = 'https://www.estantevirtual.com.br'
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
}
const FETCH_TIMEOUT_MS = 8000
const JSON_LD_RE = /<script type="application\/ld\+json"[^>]*>(.*?)<\/script>/gs

async function fetchHtml(url) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
  try {
    const response = await fetch(url, { headers: HEADERS, signal: controller.signal })
    if (!response.ok) return null
    return await response.text()
  } catch {
    return null
  } finally {
    clearTimeout(timeout)
  }
}

/** A Estante Virtual embute os resultados da busca num <script type="application/ld+json">
 * (schema.org ItemList) — mais confiável que raspar o HTML visual da página. */
function extractListings(html) {
  for (const match of html.matchAll(JSON_LD_RE)) {
    let json
    try {
      json = JSON.parse(match[1])
    } catch {
      continue
    }

    const graph = Array.isArray(json['@graph']) ? json['@graph'] : [json]
    for (const node of graph) {
      if (node['@type'] !== 'ItemList' || !Array.isArray(node.itemListElement)) continue

      const listings = node.itemListElement
        .map((el) => el.item)
        .filter((item) => item?.offers?.price != null && item?.url)
        .map((item) => ({ titulo: item.name, preco: Number(item.offers.price), url: item.url }))

      if (listings.length) return listings
    }
  }
  return []
}

function normalizar(texto) {
  return texto
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
}

function escapeRegex(texto) {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Quando um filtro (ex.: `tipo-de-livro=novo`) não acha nenhum anúncio pra
 * busca exata, a Estante Virtual às vezes cai pra uma busca "parecida" por
 * palavra solta e devolve livros sem relação nenhuma com o título buscado
 * (ex.: "como modelar com uml2" virou "como reduzir os quadris e modelar as
 * coxas" — bateu em "como"/"modelar" mas é outro livro). Exige que TODAS as
 * palavras (>2 letras) do título buscado apareçam como palavra inteira no
 * título do anúncio — descarta esse lixo em vez de mostrar preço errado. */
function filtrarRelevantes(listings, titulo) {
  const palavrasBuscadas = normalizar(titulo)
    .split(/\s+/)
    .filter((palavra) => palavra.length > 2)
  if (!palavrasBuscadas.length) return listings

  return listings.filter((listing) => {
    const tituloNormalizado = normalizar(listing.titulo)
    return palavrasBuscadas.every((palavra) => new RegExp(`\\b${escapeRegex(palavra)}\\b`).test(tituloNormalizado))
  })
}

// A Estante Virtual só distingue novo/usado no filtro (não tem "seminovo"),
// então agrupamos seminovo com usado — mais perto do preço de referência real.
const TIPO_DE_LIVRO = { novo: 'novo', seminovo: 'usado', usado: 'usado' }

function buildSearchUrl(query, condicao) {
  const params = new URLSearchParams({ nsCat: 'Natural', q: query, searchField: 'titulo-autor' })
  const tipoDeLivro = TIPO_DE_LIVRO[condicao]
  if (tipoDeLivro) params.set('tipo-de-livro', tipoDeLivro)
  return `${BASE_URL}/busca?${params}`
}

async function buscarListagens(query, condicao) {
  const buscaUrl = buildSearchUrl(query, condicao)
  const html = await fetchHtml(buscaUrl)
  return { listings: html ? extractListings(html) : null, buscaUrl }
}

function resumirPrecos(listings, buscaUrl, condicaoAplicada) {
  const menor = listings.reduce((a, b) => (a.preco <= b.preco ? a : b))
  const maior = listings.reduce((a, b) => (a.preco >= b.preco ? a : b))
  const media = listings.reduce((soma, l) => soma + l.preco, 0) / listings.length

  return {
    quantidade: listings.length,
    menor: { preco: menor.preco, url: menor.url },
    maior: { preco: maior.preco, url: maior.url },
    media,
    buscaUrl,
    condicaoAplicada,
  }
}

/** Busca anúncios do mesmo livro na Estante Virtual e resume os preços
 * encontrados (menor, maior, média) pra ajudar a precificar. Tenta
 * título + autor primeiro; a busca da Estante Virtual costuma achar bem
 * menos anúncios com a string composta, então cai pra só título se não
 * achar nada. `condicao` ('novo' | 'seminovo' | 'usado', opcional) filtra
 * por condição do anúncio, mantida igual nas duas tentativas. Retorna null
 * se a busca falhar; `quantidade: 0` se não achar nenhum anúncio nem no
 * fallback. */
export async function buscarPrecosDeMercado(titulo, autor, condicao) {
  if (!titulo) return null

  const condicaoAplicada = TIPO_DE_LIVRO[condicao] ?? null
  const queryCompleta = [titulo, autor].filter(Boolean).join(' ').trim()

  const primeira = await buscarListagens(queryCompleta, condicao)
  if (primeira.listings === null) return null
  const primeiraRelevante = filtrarRelevantes(primeira.listings, titulo)
  if (primeiraRelevante.length) return resumirPrecos(primeiraRelevante, primeira.buscaUrl, condicaoAplicada)

  if (queryCompleta !== titulo) {
    const fallback = await buscarListagens(titulo, condicao)
    if (fallback.listings !== null) {
      const fallbackRelevante = filtrarRelevantes(fallback.listings, titulo)
      if (fallbackRelevante.length) return resumirPrecos(fallbackRelevante, fallback.buscaUrl, condicaoAplicada)
      return { quantidade: 0, buscaUrl: fallback.buscaUrl, condicaoAplicada }
    }
  }

  return { quantidade: 0, buscaUrl: primeira.buscaUrl, condicaoAplicada }
}
