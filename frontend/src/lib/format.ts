// Formatting helpers for GhostGuard UI.

export function fmtNaira(n: number | string | null | undefined): string {
  const num = typeof n === 'string' ? parseFloat(n) : n ?? 0
  if (Number.isNaN(num)) return '₦0'
  return '₦' + num.toLocaleString('en-NG', { maximumFractionDigits: 0 })
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function shortHash(hash: string | null | undefined, chars = 8): string {
  if (!hash) return '—'
  return hash.length > chars ? hash.slice(0, chars) + '…' : hash
}

export const LAYER_LABELS: Record<string, string> = {
  identity: 'Layer 1 · Identity',
  shared_attributes: 'Layer 2 · Shared Attributes',
  existence: 'Layer 3 · Existence',
  process: 'Layer 4 · Process',
  cross_check: 'Layer 5 · Cross-Check',
}

export function layerLabel(layer: string): string {
  return LAYER_LABELS[layer] ?? layer
}
