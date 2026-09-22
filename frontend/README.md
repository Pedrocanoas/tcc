# frontend

Vue 3 (Composition API) + Vite + Tailwind CSS.

```sh
npm install
npm run dev      # http://localhost:5173
npm run build
```

## Variáveis de ambiente

`VITE_API_URL` (opcional, default `http://localhost:3000/api`) — endereço
do [`backend/`](../backend/README.md) que os formulários chamam pra gerar
descrição e buscar metadados por ISBN (ver `src/lib/api.js`).
