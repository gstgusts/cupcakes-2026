import type { Prediction } from './types.ts'

export default function PredictionList({ predictions }: { predictions: Prediction[] }) {
  return (
    <section className="card overflow-x-auto">
      <h2 className="px-6 pt-6 text-2xl font-extrabold">Predictions</h2>
      <table className="mt-4 w-full text-left">
        <thead className="border-b border-line text-sm text-muted">
          <tr>
            <th className="px-6 py-3 font-bold">Date</th>
            <th className="px-6 py-3 font-bold">Cupcake</th>
            <th className="px-6 py-3 font-bold">Store</th>
            <th className="px-6 py-3 font-bold">Prediction model</th>
            <th className="px-6 py-3 text-right font-bold">Bake</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {predictions.map((prediction) => (
            <tr key={prediction.id} className="hover:bg-slate-50">
              <td className="px-6 py-4 tabular-nums">{prediction.date}</td>
              <td className="px-6 py-4 font-bold">{prediction.cupcake.name}</td>
              <td className="px-6 py-4">{prediction.store.name}</td>
              <td className="px-6 py-4 text-muted">{prediction.prediction_model.name}</td>
              <td className="px-6 py-4 text-right text-lg font-extrabold tabular-nums">
                {prediction.recommended_quantity}
              </td>
            </tr>
          ))}
          {predictions.length === 0 && (
            <tr>
              <td colSpan={5} className="px-6 py-10 text-center text-muted">No predictions yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  )
}
