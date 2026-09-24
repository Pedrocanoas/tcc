<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps({
  min: { type: Number, default: 1000 },
  max: { type: Number, default: 2100 },
});

const model = defineModel({ type: [String, Number], default: "" });

const currentYear = new Date().getFullYear();

function decadeStart(year) {
  return Math.floor(year / 10) * 10;
}

const open = ref(false);
const root = ref(null);
const pageStart = ref(decadeStart(Number(model.value) || currentYear));

const years = computed(() =>
  Array.from({ length: 10 }, (_, i) => pageStart.value + i),
);

function toggle() {
  if (!open.value) pageStart.value = decadeStart(Number(model.value) || currentYear);
  open.value = !open.value;
}

function prevDecade() {
  pageStart.value -= 10;
}

function nextDecade() {
  pageStart.value += 10;
}

function pick(year) {
  if (year < props.min || year > props.max) return;
  model.value = year;
  open.value = false;
}

function onInput(event) {
  model.value = event.target.value.replace(/\D/g, "").slice(0, 4);
}

function onClickOutside(event) {
  if (root.value && !root.value.contains(event.target)) open.value = false;
}

onMounted(() => document.addEventListener("click", onClickOutside));
onBeforeUnmount(() => document.removeEventListener("click", onClickOutside));
</script>

<template>
  <div ref="root" class="relative" @keydown.esc="open = false">
    <div class="relative">
      <input
        :value="model"
        type="text"
        inputmode="numeric"
        maxlength="4"
        placeholder="aaaa"
        class="w-full rounded-lg border border-slate-300 px-3 py-2 pr-9 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        @input="onInput"
        @focus="open = true"
      />
      <button
        type="button"
        class="absolute inset-y-0 right-0 flex w-9 items-center justify-center text-slate-400 hover:text-slate-600"
        aria-label="Abrir seletor de ano"
        @click="toggle"
      >
        <svg
          class="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5"
          />
        </svg>
      </button>
    </div>

    <div
      v-if="open"
      class="absolute z-10 mt-1 w-56 rounded-lg border border-slate-200 bg-white p-3 shadow-lg"
    >
      <div class="mb-2 flex items-center justify-between">
        <button
          type="button"
          class="rounded p-1 text-slate-500 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-30"
          :disabled="pageStart <= min"
          aria-label="Década anterior"
          @click="prevDecade"
        >
          ‹
        </button>
        <span class="text-sm font-medium text-slate-700">
          {{ pageStart }} - {{ pageStart + 9 }}
        </span>
        <button
          type="button"
          class="rounded p-1 text-slate-500 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-30"
          :disabled="pageStart + 9 >= max"
          aria-label="Próxima década"
          @click="nextDecade"
        >
          ›
        </button>
      </div>

      <div class="grid grid-cols-2 gap-1">
        <button
          v-for="year in years"
          :key="year"
          type="button"
          :disabled="year < min || year > max"
          class="rounded-md px-2 py-1.5 text-sm transition-colors disabled:cursor-not-allowed disabled:text-slate-300 disabled:hover:bg-transparent"
          :class="
            Number(model) === year
              ? 'bg-blue-800 text-white hover:bg-blue-900'
              : year === currentYear
                ? 'font-semibold text-blue-700 hover:bg-blue-50'
                : 'text-slate-700 hover:bg-blue-50'
          "
          @click="pick(year)"
        >
          {{ year }}
        </button>
      </div>
    </div>
  </div>
</template>
