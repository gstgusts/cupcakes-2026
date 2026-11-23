<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from './api.ts'
import { keycloak } from './keycloak.ts'
import PredictionForm from './PredictionForm.vue'
import PredictionList from './PredictionList.vue'
import type { Prediction, PredictionModel } from './types.ts'

const models = ref<PredictionModel[]>([])
const predictions = ref<Prediction[]>([])
const error = ref('')

// Reloads the list after a prediction is created
function loadPredictions() {
  api.predictions()
    .then((rows) => (predictions.value = rows))
    .catch(() => (error.value = 'Loading the predictions failed.'))
}

// Loads the data once when the app starts
onMounted(() => {
  api.predictionModels()
    .then((rows) => (models.value = rows))
    .catch(() => (error.value = 'Loading the prediction models failed.'))
  loadPredictions()
})

const name = keycloak.tokenParsed?.name ?? keycloak.tokenParsed?.preferred_username

function signOut() {
  keycloak.logout({ redirectUri: window.location.origin })
}
</script>

<template>
  <div class="flex min-h-screen flex-col bg-sky-soft font-sans text-ink antialiased">
    <header class="border-b border-line bg-white">
      <nav class="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <span class="flex items-center gap-3">
          <span class="text-3xl leading-none" aria-hidden="true">🧁</span>
          <span class="text-xl font-extrabold text-brand">Cupcake Business</span>
          <span class="rounded-full bg-sky-soft px-3 py-1 text-sm font-bold">Vue</span>
        </span>
        <span class="flex items-center gap-6">
          <span class="font-semibold text-muted">{{ name }}</span>
          <button class="font-semibold text-brand hover:text-brand-dark" @click="signOut">Sign out</button>
        </span>
      </nav>
    </header>

    <main class="mx-auto w-full max-w-5xl space-y-8 px-6 py-12">
      <p v-if="error" class="alert-error">{{ error }}</p>
      <PredictionForm :models="models" @created="loadPredictions" />
      <PredictionList :predictions="predictions" />
    </main>
  </div>
</template>
