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

function buildSearchUrl(query) {
  return `${BASE_URL}/busca?nsCat=Natural&q=${encodeURIComponent(query)}&searchField=titulo-autor`
}

async function buscarListagens(query) {
  const buscaUrl = buildSearchUrl(query)
  const html = await fetchHtml(buscaUrl)
  return { listings: html ? extractListings(html) : null, buscaUrl }
}

function resumirPrecos(listings, buscaUrl) {
  const menor = listings.reduce((a, b) => (a.preco <= b.preco ? a : b))
  const maior = listings.reduce((a, b) => (a.preco >= b.preco ? a : b))
  const media = listings.reduce((soma, l) => soma + l.preco, 0) / listings.length

  return {
    quantidade: listings.length,
    menor: { preco: menor.preco, url: menor.url },
    maior: { preco: maior.preco, url: maior.url },
    media,
    buscaUrl,
  }
}

/** Busca anúncios do mesmo livro na Estante Virtual e resume os preços
 * encontrados (menor, maior, média) pra ajudar a precificar. Tenta
 * título + autor primeiro; a busca da Estante Virtual costuma achar bem
 * menos anúncios com a string composta, então cai pra só título se não
 * achar nada. Retorna null se a busca falhar; `quantidade: 0` se não achar
 * nenhum anúncio nem no fallback. */
export async function buscarPrecosDeMercado(titulo, autor) {
  if (!titulo) return null

  const queryCompleta = [titulo, autor].filter(Boolean).join(' ').trim()
  const primeira = await buscarListagens(queryCompleta)
  if (primeira.listings === null) return null
  if (primeira.listings.length) return resumirPrecos(primeira.listings, primeira.buscaUrl)

  if (queryCompleta !== titulo) {
    const fallback = await buscarListagens(titulo)
    if (fallback.listings?.length) return resumirPrecos(fallback.listings, fallback.buscaUrl)
    if (fallback.listings !== null) return { quantidade: 0, buscaUrl: fallback.buscaUrl }
  }

  return { quantidade: 0, buscaUrl: primeira.buscaUrl }
}
