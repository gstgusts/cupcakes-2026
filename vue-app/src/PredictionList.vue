<script setup lang="ts">
import type { Prediction } from './types.ts'

defineProps<{ predictions: Prediction[] }>()
</script>

<template>
  <section class="card overflow-x-auto">
    <h2 class="px-6 pt-6 text-2xl font-extrabold">Predictions</h2>
    <table class="mt-4 w-full text-left">
      <thead class="border-b border-line text-sm text-muted">
        <tr>
          <th class="px-6 py-3 font-bold">Date</th>
          <th class="px-6 py-3 font-bold">Cupcake</th>
          <th class="px-6 py-3 font-bold">Store</th>
          <th class="px-6 py-3 font-bold">Prediction model</th>
          <th class="px-6 py-3 text-right font-bold">Bake</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-line">
        <tr v-for="prediction in predictions" :key="prediction.id" class="hover:bg-slate-50">
          <td class="px-6 py-4 tabular-nums">{{ prediction.date }}</td>
          <td class="px-6 py-4 font-bold">{{ prediction.cupcake.name }}</td>
          <td class="px-6 py-4">{{ prediction.store.name }}</td>
          <td class="px-6 py-4 text-muted">{{ prediction.prediction_model.name }}</td>
          <td class="px-6 py-4 text-right text-lg font-extrabold tabular-nums">
            {{ prediction.recommended_quantity }}
          </td>
        </tr>
        <tr v-if="predictions.length === 0">
          <td colspan="5" class="px-6 py-10 text-center text-muted">No predictions yet.</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
