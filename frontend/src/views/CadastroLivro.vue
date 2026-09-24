<script setup>
import { ref, watch } from 'vue'
import BookForm from '@/components/BookForm.vue'
import { buscarPorIsbn, buscarPrecos, detectarIsbn, gerarDescricao } from '@/lib/api.js'

const photos = ref([])
const form = ref({
  titulo: '',
  autor: '',
  editora: '',
  ano: '',
  isbn: '',
  idioma: 'Português',
  condicao: 'usado',
  sku: '',
  descricao: '',
  localizacao: '',
  embutirLocalizacao: false,
  estante: '',
  largura: '',
  altura: '',
  grossura: '',
  peso: '',
  quantidade: 1,
  capa: 'mole',
  paginas: '',
  preco: '',
})
const generating = ref(false)
const generationError = ref('')
const metadataLoading = ref(false)
const metadataError = ref('')
const precos = ref(null)
const precosLoading = ref(false)
const precosError = ref('')

/** Preenche só os campos que ainda estão vazios — não sobrescreve o que o usuário já digitou. */
function aplicarMetadados(metadados) {
  if (!metadados) return
  if (!form.value.titulo && metadados.titulo) form.value.titulo = metadados.titulo
  if (!form.value.autor && metadados.autor) form.value.autor = metadados.autor
  if (!form.value.editora && metadados.editora) form.value.editora = metadados.editora
  if (!form.value.ano && metadados.ano) form.value.ano = metadados.ano
  if (!form.value.isbn && metadados.isbn) form.value.isbn = metadados.isbn
}

// Mantém o texto da localização (quando "Embutir localização na descrição"
// está marcado) sincronizado no final de `form.descricao` — guarda o que foi
// adicionado da última vez pra poder tirar antes de recolocar, sem duplicar.
let sufixoLocalizacaoAplicado = ''

function sincronizarLocalizacaoNaDescricao() {
  if (sufixoLocalizacaoAplicado && form.value.descricao.endsWith(sufixoLocalizacaoAplicado)) {
    form.value.descricao = form.value.descricao.slice(0, -sufixoLocalizacaoAplicado.length)
  }
  sufixoLocalizacaoAplicado =
    form.value.embutirLocalizacao && form.value.localizacao
      ? `\n\nLocalização: ${form.value.localizacao}`
      : ''
  if (sufixoLocalizacaoAplicado) form.value.descricao += sufixoLocalizacaoAplicado
}

watch(() => [form.value.embutirLocalizacao, form.value.localizacao], sincronizarLocalizacaoNaDescricao)

async function handlePhotosAdded() {
  generating.value = true
  generationError.value = ''
  const descricaoPromise = gerarDescricao(photos.value)
    .then((descricao) => {
      form.value.descricao = descricao
      sincronizarLocalizacaoNaDescricao()
    })
    .catch((err) => {
      generationError.value = err.message
    })
    .finally(() => {
      generating.value = false
    })

  // Tenta ler o ISBN do código de barras nas fotos, em paralelo com a descrição.
  // Se não achar (a maioria das fotos não mostra a contracapa), o campo ISBN
  // digitado manualmente (handleIsbnBlur) é quem preenche o resto.
  metadataLoading.value = true
  metadataError.value = ''
  const isbnPromise = detectarIsbn(photos.value)
    .then(aplicarMetadados)
    .catch((err) => {
      metadataError.value = err.message
    })
    .finally(() => {
      metadataLoading.value = false
    })

  await Promise.all([descricaoPromise, isbnPromise])
}

async function handleIsbnBlur() {
  // Já preenchido (seja pelo código de barras ou por já ter dados) — não faz sentido buscar de novo.
  if (form.value.titulo || !form.value.isbn) return

  metadataLoading.value = true
  metadataError.value = ''
  try {
    aplicarMetadados(await buscarPorIsbn(form.value.isbn))
  } catch (err) {
    metadataError.value = err.message
  } finally {
    metadataLoading.value = false
  }
}

// Evita rebuscar de novo se título/autor não mudaram desde a última busca
// (ex: usuário só passou o foco pelo campo sem editar nada).
let ultimaBuscaPrecos = ''

async function handleTituloBlur() {
  if (!form.value.titulo) return

  const chave = `${form.value.titulo}|${form.value.autor}`
  if (chave === ultimaBuscaPrecos) return
  ultimaBuscaPrecos = chave

  precosLoading.value = true
  precosError.value = ''
  try {
    precos.value = await buscarPrecos(form.value.titulo, form.value.autor)
  } catch (err) {
    precosError.value = err.message
    precos.value = null
  } finally {
    precosLoading.value = false
  }
}

function handleSubmit() {
  // TODO: enviar `form` + `photos` para o backend (POST /api/livros).
  console.log('Cadastrar livro', form.value, photos.value)
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-6 py-10">
    <BookForm
      v-model:form="form"
      v-model:photos="photos"
      :generating="generating"
      :generation-error="generationError"
      :metadata-loading="metadataLoading"
      :metadata-error="metadataError"
      :precos="precos"
      :precos-loading="precosLoading"
      :precos-error="precosError"
      @photos-added="handlePhotosAdded"
      @isbn-blur="handleIsbnBlur"
      @titulo-blur="handleTituloBlur"
      @submit="handleSubmit"
    />
  </div>
</template>
