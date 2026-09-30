import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listAssets } from '../api/assets'
import { Money } from '../components/common/Money'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { ErrorBanner } from '../components/common/ErrorBanner'

export function AssetsListPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ['assets'], queryFn: listAssets })
  const [category, setCategory] = useState('all')

  const categories = useMemo(() => {
    if (!data) return []
    return Array.from(new Set(data.map((a) => a.category)))
  }, [data])

  const filtered = data?.filter((a) => category === 'all' || a.category === category)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Assets</h1>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="all">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <LoadingSpinner />}
      <ErrorBanner error={error} />

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-100 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-2 font-medium">Name</th>
              <th className="px-4 py-2 font-medium">Category</th>
              <th className="px-4 py-2 font-medium text-right">Price</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered?.map((asset) => (
              <tr key={asset.id} className="hover:bg-slate-50">
                <td className="px-4 py-2.5">
                  <Link to={`/assets/${asset.id}`} className="font-medium text-slate-800 hover:underline">
                    {asset.name}
                  </Link>
                </td>
                <td className="px-4 py-2.5 text-slate-500">{asset.category}</td>
                <td className="px-4 py-2.5 text-right font-medium text-slate-800">
                  <Money value={asset.current_price} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered?.length === 0 && <p className="p-4 text-sm text-slate-500">No assets found.</p>}
      </div>
    </div>
  )
}
