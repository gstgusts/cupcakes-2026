import { useCallback, useEffect, useState } from 'react'
import { api } from './api.ts'
import { keycloak } from './keycloak.ts'
import PredictionForm from './PredictionForm.tsx'
import PredictionList from './PredictionList.tsx'
import type { Prediction, PredictionModel } from './types.ts'

export default function App() {
  const [models, setModels] = useState<PredictionModel[]>([])
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [error, setError] = useState('')

  // Reloads the list after a prediction is created
  const loadPredictions = useCallback(() => {
    api.predictions().then(setPredictions).catch(() => setError('Loading the predictions failed.'))
  }, [])

  // Loads the data once when the app starts (the state is set when the answers arrive)
  useEffect(() => {
    api.predictionModels().then(setModels).catch(() => setError('Loading the prediction models failed.'))
    api.predictions().then(setPredictions).catch(() => setError('Loading the predictions failed.'))
  }, [])

  const name = keycloak.tokenParsed?.name ?? keycloak.tokenParsed?.preferred_username

  return (
    <div className="flex min-h-screen flex-col bg-sky-soft font-sans text-ink antialiased">
      <header className="border-b border-line bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="flex items-center gap-3">
            <span className="text-3xl leading-none" aria-hidden="true">🧁</span>
            <span className="text-xl font-extrabold text-brand">Cupcake Business</span>
            <span className="rounded-full bg-sky-soft px-3 py-1 text-sm font-bold">React</span>
          </span>
          <span className="flex items-center gap-6">
            <span className="font-semibold text-muted">{name}</span>
            <button
              className="font-semibold text-brand hover:text-brand-dark"
              onClick={() => keycloak.logout({ redirectUri: window.location.origin })}
            >
              Sign out
            </button>
          </span>
        </nav>
      </header>

      <main className="mx-auto w-full max-w-5xl space-y-8 px-6 py-12">
        {error && <p className="alert-error">{error}</p>}
        <PredictionForm models={models} onCreated={loadPredictions} />
        <PredictionList predictions={predictions} />
      </main>
    </div>
  )
}
