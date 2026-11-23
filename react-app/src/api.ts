import { keycloak } from './keycloak.ts'
import type { FieldErrors, NewPrediction, Prediction, PredictionModel } from './types.ts'

/** An API answer that is not 2xx. `errors` holds the field messages of 400 and 409 answers. */
export class ApiError extends Error {
  readonly status: number
  readonly errors: FieldErrors

  constructor(status: number, message: string, errors: FieldErrors = {}) {
    super(message)
    this.status = status
    this.errors = errors
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  // Refreshes the access token if it expires within 30 seconds
  try {
    await keycloak.updateToken(30)
  } catch {
    // The Keycloak session has ended: log in again
    await keycloak.login()
  }

  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      ...init.headers,
      Authorization: `Bearer ${keycloak.token}`,
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    },
  })
  if (response.status === 401) {
    await keycloak.login()
  }

  const body = await response.json()
  if (!response.ok) {
    throw new ApiError(response.status, body.error ?? 'The request failed.', body.errors)
  }
  return body as T
}

export const api = {
  predictionModels: () => request<PredictionModel[]>('/prediction-models'),
  predictions: () => request<Prediction[]>('/predictions'),
  createPrediction: (input: NewPrediction) =>
    request<Prediction>('/predictions', { method: 'POST', body: JSON.stringify(input) }),
}
