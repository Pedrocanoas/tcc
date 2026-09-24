<script setup>
import { ref } from "vue";

import YearPicker from "./YearPicker.vue";

const form = defineModel("form", {
  default: () => ({
    titulo: "",
    autor: "",
    editora: "",
    ano: "",
    isbn: "",
    idioma: "Português",
    condicao: "usado",
    sku: "",
    descricao: "",
    localizacao: "",
    embutirLocalizacao: false,
    estante: "",
    largura: "",
    altura: "",
    grossura: "",
    peso: "",
    quantidade: 1,
    capa: "mole",
    paginas: "",
    preco: "",
  }),
});

const ESTANTES = [
  "Literatura Brasileira",
  "Literatura Estrangeira",
  "Romance",
  "Infantil e Juvenil",
  "Didático e Acadêmico",
  "Direito",
  "Autoajuda",
  "Religião e Espiritualidade",
  "História",
  "Outros Assuntos",
];

const photos = defineModel("photos", { default: () => [] });

defineProps({
  generating: { type: Boolean, default: false },
  generationError: { type: String, default: "" },
  metadataLoading: { type: Boolean, default: false },
  metadataError: { type: String, default: "" },
  precos: { type: Object, default: null },
  precosLoading: { type: Boolean, default: false },
  precosError: { type: String, default: "" },
});

const emit = defineEmits(["submit", "photos-added", "isbn-blur", "titulo-blur"]);

const BRL_FORMATTER = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
function formatarPreco(valor) {
  return BRL_FORMATTER.format(valor);
}

const isDragging = ref(false);

function addFiles(fileList) {
  const files = Array.from(fileList).filter((file) =>
    file.type.startsWith("image/"),
  );
  if (!files.length) return;
  const items = files.map((file) => ({ file, url: URL.createObjectURL(file) }));
  photos.value = [...photos.value, ...items];
  emit("photos-added");
}

function onDrop(event) {
  isDragging.value = false;
  addFiles(event.dataTransfer.files);
}

function onSelect(event) {
  addFiles(event.target.files);
  event.target.value = "";
}

function removePhoto(index) {
  URL.revokeObjectURL(photos.value[index].url);
  photos.value = photos.value.filter((_, i) => i !== index);
}
</script>

<template>
  <section class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
    <h2 class="text-lg font-semibold text-slate-900">Cadastrar livro</h2>
    <p class="mt-1 text-sm text-slate-500">
      Preencha os dados do livro. Assim que as fotos forem enviadas, a descrição
      é gerada automaticamente.
    </p>

    <form
      class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2"
      @submit.prevent="$emit('submit')"
    >
      <div class="flex flex-col gap-1 sm:col-span-2">
        <span class="text-sm font-medium text-slate-700">Fotos do livro</span>
        <label
          class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors"
          :class="
            isDragging
              ? 'border-blue-400 bg-blue-50'
              : 'border-slate-300 hover:border-slate-400'
          "
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <svg
            class="h-7 w-7 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z"
            />
          </svg>
          <span class="text-sm text-slate-600">
            Arraste as fotos aqui ou
            <span class="font-medium text-blue-700"
              >clique para selecionar</span
            >
          </span>
          <span class="text-xs text-slate-400"
            >A descrição é gerada automaticamente após o envio</span
          >
          <input
            type="file"
            accept="image/*"
            multiple
            class="hidden"
            @change="onSelect"
          />
        </label>

        <ul
          v-if="photos.length"
          class="mt-2 grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6"
        >
          <li
            v-for="(photo, index) in photos"
            :key="photo.url"
            class="group relative aspect-square"
          >
            <img
              :src="photo.url"
              :alt="`Foto ${index + 1}`"
              class="h-full w-full rounded-lg object-cover"
            />
            <button
              type="button"
              class="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-xs text-white opacity-0 shadow transition-opacity group-hover:opacity-100"
              aria-label="Remover foto"
              @click="removePhoto(index)"
            >
              ✕
            </button>
          </li>
        </ul>
        <p v-if="generating" class="mt-1 text-xs font-medium text-amber-600">
          Gerando descrição a partir das fotos…
        </p>
        <p
          v-else-if="generationError"
          class="mt-1 text-xs font-medium text-red-600"
        >
          {{ generationError }}
        </p>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:col-span-2 sm:grid-cols-2">
        <div class="flex flex-col gap-4">
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-slate-700">ISBN</span>
            <input
              v-model="form.isbn"
              type="text"
              placeholder="Digite o ISBN pra preencher título/autor/editora automaticamente"
              class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              @blur="$emit('isbn-blur')"
            />
            <p v-if="metadataLoading" class="text-xs font-medium text-amber-600">
              Buscando dados do livro…
            </p>
            <p v-else-if="metadataError" class="text-xs font-medium text-red-600">
              {{ metadataError }}
            </p>
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-slate-700">Autor</span>
            <input
              v-model="form.autor"
              type="text"
              class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-slate-700">Editora</span>
            <input
              v-model="form.editora"
              type="text"
              class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-slate-700">SKU</span>
            <input
              v-model="form.sku"
              type="text"
              placeholder="Gerado automaticamente"
              class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </label>
        </div>

        <div class="flex flex-col gap-4">
          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-slate-700">Título</span>
            <input
              v-model="form.titulo"
              type="text"
              required
              placeholder="Ex: English Grammar in Use"
              class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              @blur="$emit('titulo-blur')"
            />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-slate-700">Ano</span>
            <YearPicker v-model="form.ano" :min="1000" :max="2100" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-slate-700">Idioma</span>
            <select
              v-model="form.idioma"
              class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option>Português</option>
              <option>Inglês</option>
              <option>Espanhol</option>
              <option>Outro</option>
            </select>
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-sm font-medium text-slate-700">Condição</span>
            <select
              v-model="form.condicao"
              class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              <option value="novo">Novo</option>
              <option value="seminovo">Seminovo</option>
              <option value="usado">Usado</option>
            </select>
          </label>
        </div>
      </div>

      <div class="flex flex-col gap-1 sm:col-span-2">
        <span class="text-sm font-medium text-slate-700">Localização do Produto</span>
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
          <input
            v-model="form.localizacao"
            type="text"
            placeholder="(Na sua loja) [Opcional]"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input
              v-model="form.embutirLocalizacao"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300 text-blue-800 focus:ring-2 focus:ring-blue-200"
            />
            Embutir localização na descrição
          </label>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:col-span-2 sm:grid-cols-2">
        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Estante</span>
          <select
            v-model="form.estante"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          >
            <option value="">Selecione...</option>
            <option v-for="opcao in ESTANTES" :key="opcao" :value="opcao">
              {{ opcao }}
            </option>
          </select>
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Capa</span>
          <select
            v-model="form.capa"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          >
            <option value="mole">Mole</option>
            <option value="dura">Dura</option>
          </select>
        </label>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:col-span-2 sm:grid-cols-3">
        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Largura (cm)</span>
          <input
            v-model="form.largura"
            type="number"
            min="0"
            step="1"
            required
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Altura (cm)</span>
          <input
            v-model="form.altura"
            type="number"
            min="0"
            step="1"
            required
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Grossura (cm)</span>
          <input
            v-model="form.grossura"
            type="number"
            min="0"
            step="1"
            required
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </label>
      </div>

      <div class="grid grid-cols-2 gap-4 sm:col-span-2 sm:grid-cols-4">
        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Peso (g)</span>
          <input
            v-model="form.peso"
            type="number"
            min="0"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Nº de Páginas</span>
          <input
            v-model="form.paginas"
            type="number"
            min="0"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Quantidade</span>
          <input
            v-model="form.quantidade"
            type="number"
            min="1"
            required
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-sm font-medium text-slate-700">Preço (R$)</span>
          <input
            v-model="form.preco"
            type="number"
            min="0"
            step="0.01"
            required
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </label>
      </div>

      <div
        v-if="precosLoading || precosError || precos"
        class="sm:col-span-2 rounded-xl border border-slate-200 bg-slate-50 p-4"
      >
        <p v-if="precosLoading" class="flex items-center gap-2 text-sm text-amber-600">
          <svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="9" stroke="currentColor" stroke-width="3" />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M21 12a9 9 0 0 0-9-9V0a12 12 0 0 1 12 12h-3Z"
            />
          </svg>
          Buscando preços de anúncios parecidos…
        </p>

        <p v-else-if="precosError" class="flex items-center gap-2 text-sm text-red-600">
          <svg class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 9v3.75m-9.303 3.376C1.83 17.933 2.914 20 4.767 20h14.466c1.853 0 2.937-2.067 1.837-3.874L13.837 4.126c-.923-1.51-3.023-1.51-3.946 0L2.13 16.126ZM12 15.75h.007v.008H12v-.008Z"
            />
          </svg>
          {{ precosError }}
        </p>

        <p v-else-if="precos && precos.quantidade === 0" class="flex items-center gap-2 text-sm text-slate-500">
          <svg class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
            />
          </svg>
          Nenhum anúncio parecido encontrado na Estante Virtual pra comparar preço.
        </p>

        <div v-else-if="precos">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-1.5 text-xs font-medium text-slate-500">
              <svg class="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" d="M4 20V10M10 20V4M16 20v-7M4 20h16" />
              </svg>
              {{ precos.quantidade }} anúncio{{ precos.quantidade > 1 ? "s" : "" }} parecido{{
                precos.quantidade > 1 ? "s" : ""
              }}
              na Estante Virtual
            </div>
            <a
              :href="precos.buscaUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="shrink-0 text-xs font-medium text-blue-700 underline hover:text-blue-900"
              >ver todos</a
            >
          </div>

          <div class="mt-3 grid grid-cols-3 divide-x divide-slate-200">
            <div class="flex flex-col gap-1 pr-3">
              <div class="flex items-center gap-1.5 text-xs font-medium text-emerald-700">
                <svg class="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v14m0 0-5-5m5 5 5-5" />
                </svg>
                Menor preço
              </div>
              <div class="text-lg font-semibold text-slate-900">{{ formatarPreco(precos.menor.preco) }}</div>
              <a
                :href="precos.menor.url"
                target="_blank"
                rel="noopener noreferrer"
                class="w-fit text-xs text-blue-700 underline hover:text-blue-900"
                >ver anúncio</a
              >
            </div>

            <div class="flex flex-col gap-1 px-3">
              <div class="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                <svg class="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" d="M6 12h12" />
                </svg>
                Preço médio
              </div>
              <div class="text-lg font-semibold text-slate-900">{{ formatarPreco(precos.media) }}</div>
            </div>

            <div class="flex flex-col gap-1 pl-3">
              <div class="flex items-center gap-1.5 text-xs font-medium text-amber-700">
                <svg class="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 20V6m0 0-5 5m5-5 5 5" />
                </svg>
                Maior preço
              </div>
              <div class="text-lg font-semibold text-slate-900">{{ formatarPreco(precos.maior.preco) }}</div>
              <a
                :href="precos.maior.url"
                target="_blank"
                rel="noopener noreferrer"
                class="w-fit text-xs text-blue-700 underline hover:text-blue-900"
                >ver anúncio</a
              >
            </div>
          </div>
        </div>
      </div>

      <label class="flex flex-col gap-1 sm:col-span-2">
        <span class="text-sm font-medium text-slate-700">Descrição</span>
        <textarea
          v-model="form.descricao"
          rows="5"
          placeholder="Gerada automaticamente a partir das fotos, ou escreva manualmente…"
          class="resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </label>

      <div
        class="sm:col-span-2 flex justify-end border-t border-slate-100 pt-4"
      >
        <button
          type="submit"
          class="rounded-lg bg-blue-800 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-900"
        >
          Cadastrar livro
        </button>
      </div>
    </form>
  </section>
</template>
