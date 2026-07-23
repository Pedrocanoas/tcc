<script setup>
import ifspLogo from '@/assets/ifsp-logo.svg'
</script>

<template>
  <header class="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
    <div class="mx-auto flex max-w-5xl items-center gap-3 px-6 py-3">
      <img :src="ifspLogo" alt="IFSP" class="h-9 w-9 shrink-0" />
      <div class="leading-tight">
        <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">
          Instituto Federal de São Paulo
        </p>
        <h1 class="text-lg font-bold text-blue-900">Acervo de Livros</h1>
      </div>
    </div>
  </header>
</template>
