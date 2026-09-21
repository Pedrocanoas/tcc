<script setup>
import ifspLogo from '@/assets/ifsp-logo.png'
</script>

<template>
  <header class="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
    <div class="mx-auto flex max-w-5xl items-center gap-4 px-6 py-3">
      <img
        :src="ifspLogo"
        alt="Instituto Federal de São Paulo — Campus São José dos Campos"
        class="h-11 w-auto shrink-0"
      />
      <div class="h-8 w-px bg-slate-200" aria-hidden="true" />
      <h1 class="text-lg font-bold text-blue-900">Acervo de Livros</h1>
    </div>
  </header>
</template>
