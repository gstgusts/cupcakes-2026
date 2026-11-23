<script setup lang="ts">
import { ref } from 'vue'
import { api, ApiError } from './api.ts'
import type { FieldErrors, PredictionModel } from './types.ts'

/** Tomorrow as YYYY-MM-DD in local time (cupcakes are baked the day before). */
function tomorrow() {
  const day = new Date()
  day.setDate(day.getDate() + 1)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${day.getFullYear()}-${pad(day.getMonth() + 1)}-${pad(day.getDate())}`
}

defineProps<{ models: PredictionModel[] }>()
const emit = defineEmits<{ created: [] }>()

const modelId = ref('')
const date = ref(tomorrow())
const errors = ref<FieldErrors>({})
const message = ref('')
const saving = ref(false)

async function submit() {
  saving.value = true
  errors.value = {}
  message.value = ''
  try {
    const prediction = await api.createPrediction({ prediction_model_id: modelId.value, date: date.value })
    message.value = `Prediction created: bake ${prediction.recommended_quantity} cupcakes on ${prediction.date}.`
    emit('created')
  } catch (error) {
    errors.value = error instanceof ApiError ? error.errors : { request: 'Saving the prediction failed.' }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="card p-8">
    <h1 class="text-3xl font-extrabold">New prediction</h1>
    <p class="mt-1 text-muted">Calculates how many cupcakes to bake on one date.</p>

    <p v-if="message" class="alert-success mt-6">{{ message }}</p>
    <p v-if="errors.request" class="alert-error mt-6">{{ errors.request }}</p>

    <form class="mt-6 grid gap-5 sm:grid-cols-[1fr_12rem_auto] sm:items-start" novalidate @submit.prevent="submit">
      <div>
        <label class="label" for="model">Prediction model</label>
        <select id="model" v-model="modelId" class="input" :class="{ 'input-invalid': errors.prediction_model_id }">
          <option value="">Choose a prediction model</option>
          <option v-for="model in models" :key="model.id" :value="model.id">
            {{ model.cupcake.name }} · {{ model.store.name }} · {{ model.name }}
          </option>
        </select>
        <p v-if="errors.prediction_model_id" class="field-error">{{ errors.prediction_model_id }}</p>
      </div>

      <div>
        <label class="label" for="date">Date</label>
        <input id="date" v-model="date" type="date" class="input" :class="{ 'input-invalid': errors.date }" />
        <p v-if="errors.date" class="field-error">{{ errors.date }}</p>
      </div>

      <button type="submit" class="btn-primary sm:mt-7" :disabled="saving">
        {{ saving ? 'Calculating…' : 'Calculate' }}
      </button>
    </form>
  </section>
</template>
