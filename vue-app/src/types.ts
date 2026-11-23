// Types of the JSON API responses (see http://localhost:5000/api/docs)

export interface Ref {
  id: string
  name: string
}

export interface PredictionModel {
  id: string
  name: string
  cupcake: Ref
  store: Ref
  average_demand: number
  demand_std_dev: number
  production_cost: number
  selling_price: number
  salvage_value: number
  critical_ratio: number
}

export interface Prediction {
  id: string
  date: string
  recommended_quantity: number
  prediction_model: Ref
  cupcake: Ref
  store: Ref
  created_at: string
}

export interface NewPrediction {
  prediction_model_id: string
  date: string
}

/** Validation errors of the API: a message per field (400 and 409 responses). */
export type FieldErrors = Partial<Record<'prediction_model_id' | 'date' | 'request', string>>
