# backend

API em Node.js (Express, ESM).

```sh
npm install
cp .env.example .env
npm run dev      # http://localhost:3000
```

## Variáveis de ambiente (`.env`)

| Variável | Default | Descrição |
|---|---|---|
| `PORT` | `3000` | porta da API |
| `CORS_ORIGIN` | `http://localhost:5173` | origem liberada no CORS (o frontend) |
| `MODEL_DIR` | `../model` (relativo ao repo) | onde fica o `.venv` do `model/`, usado pros endpoints de descrição/ISBN |
| `PYTHON_BIN` | `<MODEL_DIR>/.venv/Scripts/python.exe` (Windows) ou `.../bin/python` | executável Python a chamar |

`MODEL_DIR`/`PYTHON_BIN` só precisam ser configuradas se o `.venv` do
`model/` estiver em outro lugar (ex: deploy em outra máquina) — ver
[`model/README.md`](../model/README.md) pro setup do venv.

## Rotas

- `GET /api/health` — sanity check.
- `POST /api/livros/gerar-descricao` — multipart, campo `fotos` (1-5
  imagens). Gera a descrição de condição do livro via o modelo fine-tuned
  em `model/` (processo persistente, ver `src/services/descricaoService.js`
  + `model/src/serve.py`). Resposta: `{ descricoes: [{ arquivo, descricao }] }`.
- `POST /api/livros/detectar-isbn` — multipart, campo `fotos`. Tenta ler
  um código de barras EAN-13/ISBN nas fotos (`model/src/detect_barcode.py`)
  e, se achar, busca os metadados do livro. Resposta:
  `{ isbn, metadados }` (`metadados` é `null` se não achou nada).
- `GET /api/livros/isbn/:isbn` — busca os metadados de um ISBN digitado
  manualmente. Resposta: `{ metadados }`.

Em ambos os casos de busca por ISBN, `metadados` (quando encontrado) tem o
formato `{ isbn, titulo, autor, editora, ano }`, consultando em cadeia
Google Books → Brasil API → Open Library (`src/services/isbnLookupService.js`).
