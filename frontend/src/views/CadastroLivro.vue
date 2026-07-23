<script setup>
import { ref } from 'vue'
import BookForm from '@/components/BookForm.vue'

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

async function handlePhotosAdded() {
  generating.value = true
  try {
    // TODO: enviar `photos` para a API de geração de descrição quando o
    // modelo/agente estiver disponível. Por enquanto é apenas um placeholder.
    await new Promise((resolve) => setTimeout(resolve, 600))
    form.value.descricao = 'Geração automática de descrição ainda não implementada.'
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
      @photos-added="handlePhotosAdded"
      @submit="handleSubmit"
    />
  </div>
</template>
