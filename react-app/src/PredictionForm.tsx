import { useState, type FormEvent } from 'react'
import { api, ApiError } from './api.ts'
import type { FieldErrors, PredictionModel } from './types.ts'

/** Tomorrow as YYYY-MM-DD in local time (cupcakes are baked the day before). */
function tomorrow() {
  const day = new Date()
  day.setDate(day.getDate() + 1)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${day.getFullYear()}-${pad(day.getMonth() + 1)}-${pad(day.getDate())}`
}

interface Props {
  models: PredictionModel[]
  onCreated: () => void
}

export default function PredictionForm({ models, onCreated }: Props) {
  const [modelId, setModelId] = useState('')
  const [date, setDate] = useState(tomorrow)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setErrors({})
    setMessage('')
    try {
      const prediction = await api.createPrediction({ prediction_model_id: modelId, date })
      setMessage(`Prediction created: bake ${prediction.recommended_quantity} cupcakes on ${prediction.date}.`)
      onCreated()
    } catch (error) {
      setErrors(error instanceof ApiError ? error.errors : { request: 'Saving the prediction failed.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="card p-8">
      <h1 className="text-3xl font-extrabold">New prediction</h1>
      <p className="mt-1 text-muted">Calculates how many cupcakes to bake on one date.</p>

      {message && <p className="alert-success mt-6">{message}</p>}
      {errors.request && <p className="alert-error mt-6">{errors.request}</p>}

      <form onSubmit={submit} className="mt-6 grid gap-5 sm:grid-cols-[1fr_12rem_auto] sm:items-start" noValidate>
        <div>
          <label className="label" htmlFor="model">Prediction model</label>
          <select
            id="model"
            className={`input ${errors.prediction_model_id ? 'input-invalid' : ''}`}
            value={modelId}
            onChange={(event) => setModelId(event.target.value)}
          >
            <option value="">Choose a prediction model</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.cupcake.name} · {model.store.name} · {model.name}
              </option>
            ))}
          </select>
          {errors.prediction_model_id && <p className="field-error">{errors.prediction_model_id}</p>}
        </div>

        <div>
          <label className="label" htmlFor="date">Date</label>
          <input
            id="date"
            type="date"
            className={`input ${errors.date ? 'input-invalid' : ''}`}
            value={date}
            onChange={(event) => setDate(event.target.value)}
          />
          {errors.date && <p className="field-error">{errors.date}</p>}
        </div>

        <button type="submit" className="btn-primary sm:mt-7" disabled={saving}>
          {saving ? 'Calculating…' : 'Calculate'}
        </button>
      </form>
    </section>
  )
}
