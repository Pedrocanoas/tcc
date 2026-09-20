<script setup>
import { ref } from 'vue'
import BookForm from '@/components/BookForm.vue'
import { gerarDescricao } from '@/lib/api.js'

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
})
const generating = ref(false)
const generationError = ref('')

async function handlePhotosAdded() {
  generating.value = true
  generationError.value = ''
  try {
    form.value.descricao = await gerarDescricao(photos.value)
  } catch (err) {
    generationError.value = err.message
  } finally {
    generating.value = false
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
      @photos-added="handlePhotosAdded"
      @submit="handleSubmit"
    />
  </div>
</template>
