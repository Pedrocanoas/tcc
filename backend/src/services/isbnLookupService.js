const FETCH_TIMEOUT_MS = 8000

async function fetchJson(url) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
  try {
    const response = await fetch(url, { signal: controller.signal })
    if (!response.ok) return null
    return await response.json()
  } catch {
    return null
  } finally {
    clearTimeout(timeout)
  }
}

async function buscarGoogleBooks(isbn) {
  const data = await fetchJson(`https://www.googleapis.com/books/v1/volumes?q=isbn:${isbn}`)
  const info = data?.items?.[0]?.volumeInfo
  if (!info) return null

  return {
    isbn,
    titulo: info.title ?? '',
    autor: info.authors?.join(', ') ?? '',
    editora: info.publisher ?? '',
    ano: info.publishedDate?.slice(0, 4) ?? '',
  }
}

async function buscarBrasilApi(isbn) {
  const info = await fetchJson(`https://brasilapi.com.br/api/isbn/v1/${isbn}`)
  if (!info) return null

  return {
    isbn,
    titulo: info.title ?? '',
    autor: info.authors?.join(', ') ?? '',
    editora: info.publisher ?? '',
    ano: info.year ? String(info.year) : '',
  }
}

async function buscarOpenLibrary(isbn) {
  const info = await fetchJson(`https://openlibrary.org/isbn/${isbn}.json`)
  if (!info) return null

  return {
    isbn,
    titulo: info.title ?? '',
    // a edição não traz o nome do autor direto (só a key /authors/OL...),
    // então esse fallback fica sem autor — melhor que nada, sem outra chamada
    autor: '',
    editora: info.publishers?.[0] ?? '',
    ano: info.publish_date ?? '',
  }
}

/** Consulta metadados oficiais do livro (título/autor/editora/ano) pelo ISBN,
 * tentando Google Books, Brasil API (melhor cobertura de livros nacionais,
 * agrega CBL/Mercado Editorial) e Open Library nessa ordem. Retorna null se
 * nenhuma das três souber desse ISBN. */
export async function buscarMetadadosPorIsbn(isbnBruto) {
  const isbn = isbnBruto.replace(/[^0-9Xx]/g, '')
  if (!isbn) return null

  return (
    (await buscarGoogleBooks(isbn)) ?? (await buscarBrasilApi(isbn)) ?? (await buscarOpenLibrary(isbn))
  )
}
