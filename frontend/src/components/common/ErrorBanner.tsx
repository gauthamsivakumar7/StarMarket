import { ApiError } from '../../api/client'

function messageFor(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Something went wrong.'
}

export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {messageFor(error)}
    </div>
  )
}
